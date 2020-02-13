# stib-mvib-sensor

This code can be used to add a custom sensor for STIB/MVIB public transport of Brussels (Belgium) to Home Assistant.

This Project is an adaptation of github.com/bollewolle/delijn-sensor, kudos to him/her for the work done.

**_Note:_** the idea is to eventually add this to the code of Home Assistant itself

## Options

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| platform | string | **Required** | `stib-mvib`
| client_id | string | **Required** | The client_id generated in a developer account at opendata.stib-mivb.be.
| client_secret | string | **Required** | The client_secret generated in a developer account at opendata.stib-mivb.be.
| lang | string | **Optional** (default:'fr') | The display language of destinations and service messages ('fr' OR 'nl')
| stops | object | **Required** | List of stops to display next passages of.

## stops object

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| stop_name | string | **Required** | Name of the Stop to retrieve the next passages of. Ie. De Brouckere
| filtered_out_stop_ids | list | **Optional** | List of specific stop_ids that must NOT be contained inside of the passages. These can be found by searching a stop here (https://opendata.bruxelles.be/explore/dataset/stib-stops/table/).   
| max_passages | number | **Optional** | Set a maximum number of passages to return in the sensor (maximum is 20 by default).


## Installation

### Step 1

Install `stib-mvib-sensor` by copying `stib-mvib.py` from this repo to `<config directory>/custom_components/sensor/stib-mvib.py` of your Home Assistant instance.

**Example:**

```bash
wget https://github.com/helldog136/stib-mvib-sensor/raw/master/stib-mvib.py
mv stib-mvib.py ~/.homeassistant//custom_components/sensor/
```

### Step 2

Set up the STIB/MVIB custom sensor.

**Example:**

```yaml
sensor:
  - platform: stib-mvib
    client_id: '<put your opendata.stib-mivb.be client_id here>'
    client_secret: '<put your opendata.stib-mivb.be client_secret here>'
    lang: 'fr'
    stops:
    - stop_name: 'Scherdemael'
      filtered_out_stop_ids:
      - 3733
      max_passages: 3
    - stop_name: 'De Brouckere'
      filtered_out_stop_ids:
      - 1465
      - 1820
      max_passages: 3
```
**_Note_**: replace with the client_id/secret you generated with you opendata.stib-mivb.be developer account.

## Credits

This Project is an adaptation of github.com/bollewolle/delijn-sensor, kudos to him/her for the work done.
Thanks to the codes of [RMV](https://www.home-assistant.io/components/sensor.rmvtransport/) and [Ruter Public Transport](https://www.home-assistant.io/components/sensor.ruter/) for all the initial work and inspiration.