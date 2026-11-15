# dronecan-dsdl

The DroneCAN message definitions shared by every AERKI device: radar, payload sensors and the flight controller.
One source of truth, validated against the full DroneCAN ecosystem on every commit.

[![DSDL checks](https://github.com/aerki-space/dronecan-dsdl/actions/workflows/ci.yml/badge.svg)](https://github.com/aerki-space/dronecan-dsdl/actions/workflows/ci.yml)

## Types

| Type | ID | Purpose |
|---|---|---|
| `aerki.radar.Detections` | 20400 | Up to 16 radar targets per frame: range, azimuth, elevation, radial velocity, SNR |
| `aerki.radar.Status` | 20401 | Radar mode, transmitter state, temperature, supply, frame rate |
| `aerki.radar.SetBeam` | 230 (service) | Standby, hold a beam direction, or resume scanning |
| `aerki.sensor.AirQuality` | 20410 | Particulates, CO, CO₂, VOC index, temperature and humidity from an air-quality payload |
| `aerki.sensor.Hotspot` | 20411 | A thermal hotspot already projected to the ground, with uncertainty and confidence |

Full field-by-field definitions: [docs/types.md](docs/types.md) (generated from the sources).

## What's checked on every commit

- **No ID collisions:** the definitions are parsed together with every namespace that ships with the DroneCAN
  tools: the standard set, the ArduPilot set and the known vendor sets.
- **ID ranges:** every ID stays inside the ranges allocated in [docs/id-allocation.md](docs/id-allocation.md).
- **Round trips:** every type is encoded into real DroneCAN frames, on both classic CAN and CAN FD, then decoded
  and compared.
- **Generated docs:** the generated documentation matches the sources.

## Use it

```sh
pip install -r requirements.txt
python3 tools/validate.py                 # IDs, sizes, signatures
python3 -m unittest discover -s tests     # round trips
```

Integration with ArduPilot, PX4, the DroneCAN GUI tool, Python and C firmware: [docs/usage.md](docs/usage.md).

## Layout

```
aerki/
  radar/     radar messages and services
  sensor/    payload sensor messages
docs/        ID allocation, usage, generated type reference
tools/       validate.py, gen_docs.py
tests/       round-trip and rule checks
```

## License

MIT, see [LICENSE](LICENSE).
