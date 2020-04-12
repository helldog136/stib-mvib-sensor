"""
Support for STIB/MVIB information.
For more info on the API see :
https://opendata.stib-mivb.be/
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.XXX --> to do
"""
import asyncio
import logging
import datetime
import time

import voluptuous as vol
from homeassistant.exceptions import PlatformNotReady
from pystibmvib import STIBAPIClient
from pystibmvib import STIBService

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession

REQUIREMENTS = ['pystibmvib==1.0.5']

_LOGGER = logging.getLogger(__name__)

CONF_STOPS = 'stops'
CONF_STOP_NAME = 'stop_name'
CONF_LANG = 'lang'
CONF_LINE_FILTER = 'line_filter'
CONF_LINE_NR = 'line_nr'
CONF_DESTINATION = 'destination'
CONF_CLIENT_ID_KEY = 'client_id'
CONF_CLIENT_SECRET_KEY = 'client_secret'
CONF_MAX_PASSAGES = 'max_passages'
CONF_MAX_DELTA_ACTU = 'actualization_delta'

DEFAULT_NAME = 'STIB/MVIB'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID_KEY): cv.string,
    vol.Required(CONF_CLIENT_SECRET_KEY): cv.string,
    vol.Optional(CONF_LANG, default='fr'): cv.string,
    vol.Optional(CONF_MAX_DELTA_ACTU, default=90): cv.positive_int,
    vol.Required(CONF_STOPS): [{
        vol.Required(CONF_STOP_NAME): cv.string,
        vol.Optional(CONF_LINE_FILTER, default=[]): [
            {
                vol.Required(CONF_LINE_NR): cv.positive_int,
                vol.Required(CONF_DESTINATION): cv.string
            }
        ],
        vol.Optional(CONF_MAX_PASSAGES, default=3): cv.positive_int}]
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Create the sensor."""

    client_id = config.get(CONF_CLIENT_ID_KEY)
    client_secret = config.get(CONF_CLIENT_SECRET_KEY)
    lang = config.get(CONF_LANG)

    session = async_get_clientsession(hass)
    stib_service = STIBService(STIBAPIClient(loop=hass.loop,
                                             session=session,
                                             client_id=client_id,
                                             client_secret=client_secret))

    sensors = []
    for stop in config.get(CONF_STOPS):
        # TODO unchecked values and unhandled exceptions... Should add that somwhere (check in python lib and try except here)
        stop_name = stop[CONF_STOP_NAME]
        lines_filter = []
        for item in stop[CONF_LINE_FILTER]:
            lines_filter.append((item[CONF_LINE_NR], item[CONF_DESTINATION]))
        max_passages = stop[CONF_MAX_PASSAGES]
        sensors.append(STIBMVIBPublicTransportSensor(
            stib_service=stib_service,
            stop_name=stop_name,
            lines_filter=lines_filter, max_passages=max_passages, lang=lang,
            max_time_delta=config.get(CONF_MAX_DELTA_ACTU)))

    tasks = [sensor.async_update() for sensor in sensors]
    if tasks:
        await asyncio.wait(tasks)
    if not all(sensor._attributes for sensor in sensors):
        raise PlatformNotReady

    async_add_entities(sensors, True)


class STIBMVIBPublicTransportSensor(Entity):
    def __init__(self, stib_service, stop_name, lines_filter, max_passages, lang, max_time_delta):
        """Initialize the sensor."""
        self.stib_service = stib_service
        self.stop_name = stop_name
        self.lines_filter = lines_filter
        self.max_passages = max_passages
        self.lang = lang
        self.passages = {}
        self._tech_name = stop_name
        self._max_time_delta = max_time_delta
        self._name = stop_name
        self._attributes = {"stop_name": self._name}
        self._last_update = 0
        self._last_intermediate_update = 0
        self._state = None

    async def async_update(self):
        """Get the latest data from the STIB/MVIB API."""
        now = time.time()
        max_delta = self._max_time_delta
        if 'arriving_in_min' in self._attributes.keys() and 'arriving_in_sec' in self._attributes.keys():
            max_delta = min(max_delta,
                            (int(self._attributes['arriving_in_min']) * 60 + int(
                                self._attributes['arriving_in_sec'])) // 2)
        max_delta = max(max_delta, 10)
        delta = now - self._last_update
        if self._state is None \
            or delta > max_delta \
            or (self._state == 0 and delta > 10):  # Here we are making a reconciliation by calling STIB API
            self._last_update = now
            self._last_intermediate_update = now
            self.passages = await self.stib_service.get_passages(stop_name=self.stop_name,
                                                                 line_filters=self.lines_filter,
                                                                 max_passages=self.max_passages,
                                                                 lang=self.lang,
                                                                 now=datetime.datetime.now())
            if self.passages is None:
                _LOGGER.error("No data recieved from STIB.")
                return
            _LOGGER.error("Data recievd from STIB: " + str(self.passages))
            try:
                first = self.passages[0].to_dict()
                self._state = first['arriving_in']['min']
                self._attributes['destination'] = first['destination']
                self._attributes['arrival_time'] = first['expectedArrivalTime']
                self._attributes['stop_id'] = first['stop_id']
                self._attributes['message'] = first['message']
                self._attributes['arriving_in_min'] = first['arriving_in']['min']
                self._attributes['arriving_in_sec'] = first['arriving_in']['sec']
                self._attributes['line_number'] = first['lineId']
                self._attributes['line_type'] = first['line_type']
                self._attributes['line_color'] = first['line_color']
                self._attributes['next_passages'] = self.passages[1:]
                self._attributes['all_passages'] = self.passages

            except (KeyError, IndexError) as error:
                _LOGGER.debug("Error getting data from STIB/MVIB, %s", error)
        else:  # here we update logically the state and arrival in min.
            intermediate_delta = now - self._last_intermediate_update
            if intermediate_delta > 60:
                self._last_intermediate_update = now
                self._state = max(self._state - intermediate_delta // 60, 0)
                self._attributes['arriving_in_min'] = max(
                    self._attributes['arriving_in_min'] - intermediate_delta // 60, 0)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._tech_name

    @property
    def friendly_name(self):
        """Return the friendly_name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if 'line_type' in self._attributes.keys():
            if self._attributes['line_type'] == 'B':
                return 'mdi:bus'
            if self._attributes['line_type'] == 'M':
                return 'mdi:subway'
            if self._attributes['line_type'] == 'T':
                return 'mdi:tram'
        return 'mdi:bus'

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes
