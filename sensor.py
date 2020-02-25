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
from pystibmvib import Passages

import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession

REQUIREMENTS = ['pystibmvib==0.0.5']

_LOGGER = logging.getLogger(__name__)

CONF_STOPS = 'stops'
CONF_STOP_NAME = 'stop_name'
CONF_LANG = 'lang'
CONF_FILTERED_OUT_STOP_IDS = 'filtered_out_stop_ids'
CONF_CLIENT_ID_KEY = 'client_id'
CONF_CLIENT_SECRET_KEY = 'client_secret'
CONF_MAX_PASSAGES = 'max_passages'
CONF_MAX_DELTA_ACTU = 'actualization_delta'

DEFAULT_NAME = 'STIB/MVIB'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CLIENT_ID_KEY): cv.string,
    vol.Required(CONF_CLIENT_SECRET_KEY): cv.string,
    vol.Optional(CONF_LANG, default='fr'): cv.string,
    vol.Optional(CONF_MAX_DELTA_ACTU, default=60): cv.positive_int,
    vol.Required(CONF_STOPS): [{
        vol.Required(CONF_STOP_NAME): cv.string,
        vol.Optional(CONF_FILTERED_OUT_STOP_IDS, default=[]): [cv.positive_int],
        vol.Optional(CONF_MAX_PASSAGES, default=3): cv.positive_int}]
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    """Create the sensor."""

    client_id = config.get(CONF_CLIENT_ID_KEY)
    client_secret = config.get(CONF_CLIENT_SECRET_KEY)
    lang = config.get(CONF_LANG)
    name = DEFAULT_NAME

    session = async_get_clientsession(hass)

    sensors = []
    for stop in config.get(CONF_STOPS):
        # TODO unchecked values and unhandled exceptions... Should add that somwhere (check in python lib and try except here)
        stop_name = stop[CONF_STOP_NAME]
        filtered_out = stop[CONF_FILTERED_OUT_STOP_IDS]
        max_passages = stop[CONF_MAX_PASSAGES]
        passages = Passages(loop=hass.loop,
                            stop_name=stop_name,
                            client_id=client_id,
                            client_secret=client_secret,
                            filtered_out_stop_ids=filtered_out,
                            session=session,
                            utcoutput=None,
                            max_passages_per_stop=max_passages,
                            time_ordered_result=True,
                            lang=lang)
        sensors.append(STIBMVIBPublicTransportSensor(passages, stop_name, config.get(CONF_MAX_DELTA_ACTU)))

    tasks = [sensor.async_update() for sensor in sensors]
    if tasks:
        await asyncio.wait(tasks)
    if not all(sensor._attributes for sensor in sensors):
        raise PlatformNotReady

    async_add_entities(sensors, True)


class STIBMVIBPublicTransportSensor(Entity):
    def __init__(self, passages, name, max_time_delta):
        """Initialize the sensor."""
        self.passages = passages
        self._tech_name = name
        self._max_time_delta = max_time_delta
        self._name = self._tech_name
        self._attributes = {"stop_name": self._tech_name}
        self._last_update = 0
        self._state = None

    async def async_update(self):
        """Get the latest data from the STIB/MVIB API."""
        now = time.time()
        max_delta = self._max_time_delta
        if 'arriving_in_min' in self._attributes.keys() and 'arriving_in_sec' in self._attributes.keys():
            max_delta = min(max_delta,
                            (int(self._attributes['arriving_in_min'])*60 + int(self._attributes['arriving_in_sec']))//2)
        max_delta = max(max_delta, 10)
        if now - self._last_update > max_delta:
            self._last_update = now
            await self.passages.update_passages(datetime.datetime.now())
            if self.passages.passages is None:
                _LOGGER.error("No data recieved from STIB.")
                return
            try:
                first = self.passages.passages[0]
                self._name = f"{self._tech_name} - {first['destination']}"
                self._state = first['arriving_in']['min']
                self._attributes['destination'] = first['destination']
                self._attributes['arrival_time'] = first['arrival_time']
                self._attributes['stop_id'] = first['stop_id']
                self._attributes['message'] = first['message']
                self._attributes['arriving_in_min'] = first['arriving_in']['min']
                self._attributes['arriving_in_sec'] = first['arriving_in']['sec']
                self._attributes['line_number'] = first['line_number']
                self._attributes['line_type'] = first['line_type']
                self._attributes['line_color'] = first['line_color']
                self._attributes['next_passages'] = self.passages.passages[1:]
            except (KeyError, IndexError) as error:
                _LOGGER.debug("Error getting data from STIB/MVIB, %s", error)

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
        if self._attributes['line_type'] is not None:
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
