# Usage

## Python (pydronecan)

```python
import dronecan

dronecan.load_dsdl('path/to/dronecan-dsdl/aerki')
node = dronecan.make_node('/dev/ttyACM0', node_id=100, bitrate=1000000)

def on_detections(e):
    for t in e.message.targets:
        print(f'{t.range:6.1f} m  az {t.azimuth:+.2f} rad  {t.radial_velocity:+.1f} m/s  {t.snr:.0f} dB')

node.add_handler(dronecan.thirdparty.aerki.radar.Detections, on_detections)
node.spin()
```

Custom namespaces appear under `dronecan.thirdparty`. The tests in `tests/test_dsdl.py` show how to encode and decode
each type.

## DroneCAN GUI tool

Copy or symlink the `aerki` directory into `~/dronecan_vendor_specific_types/`. The GUI tool loads it at start-up,
and you can then subscribe to the messages, plot their fields and call `aerki.radar.SetBeam`.

## C firmware (libcanard)

Generate C pack and unpack code with DroneCAN's code generator, next to libcanard and the standard DSDL:

```sh
git clone https://github.com/DroneCAN/dronecan_dsdlc
git clone https://github.com/DroneCAN/DSDL
pip install -r dronecan_dsdlc/requirements.txt
python dronecan_dsdlc/dronecan_dsdlc.py -O generated DSDL/uavcan dronecan-dsdl/aerki
```

## ArduPilot

ArduPilot only decodes the DroneCAN types it knows about, so the AERKI devices also publish standard messages that
ArduPilot uses with no code changes:

| Device | Standard message | ArduPilot use |
|---|---|---|
| Radar | `uavcan.equipment.range_sensor.Measurement` | Rangefinder (DroneCAN type) |
| Radar | `ardupilot.equipment.proximity_sensor.Proximity` | Proximity / obstacle avoidance |

The AERKI types carry the full detail for ground-station and companion-computer software.

## PX4

The same standard messages work with PX4's DroneCAN rangefinder support. Reading the AERKI types inside PX4 needs a
driver; until then, read them on the companion computer.
