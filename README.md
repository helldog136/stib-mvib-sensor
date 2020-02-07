# stib-mvib-sensor

This code can be used to add a custom sensor for STIB/MVIB public transport of Brussels (Belgium) to Home Assistant.

This Project is an adaptation of github.com/bollewolle/delijn-sensor, kudos to him/her for the work done.

**_Note:_** the idea is to eventually add this to the code of Home Assistant itself

## Options

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| platform | string | **Required** | `stib-mvib`
| sub_key | string | **Required** | The subscription key generated in a developer account at opendata.stib-mivb.be.
| nextpassages | object | **Required** | List of stops to display next passages of.

## nextpassages object

| Name | Type | Requirement | Description
| ---- | ---- | ------- | -----------
| stop_id | string | **Required** | Stop Id to retrieve the next passages of. These can be found by searching a stop here (https://opendata.bruxelles.be/explore/dataset/stib-stops/table/). Ie. 2838 
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
    sub_key: '<put your opendata.stib-mivb.be subscriptionkey here>'
    nextpassage:
    - stop_id: '2838'
      max_passages: 10
    - stop_id: '6444'
      max_passages: 5
```
**_Note_**: replace with the subscription key you generated with you opendata.stib-mivb.be developer account.

## Credits

This Project is an adaptation of github.com/bollewolle/delijn-sensor, kudos to him/her for the work done.
Thanks to the codes of [RMV](https://www.home-assistant.io/components/sensor.rmvtransport/) and [Ruter Public Transport](https://www.home-assistant.io/components/sensor.ruter/) for all the initial work and inspiration.