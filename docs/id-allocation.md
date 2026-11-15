# ID allocation

DroneCAN reserves message IDs 20000 – 21999 and service IDs 200 – 255 for vendor-specific types. Other vendors use
parts of those ranges too, so AERKI's blocks were picked to avoid every vendor set that ships with the DroneCAN tools.
`tools/validate.py` re-checks that on every commit.

## Messages

| Range | Namespace | Allocated |
|---|---|---|
| 20400 – 20409 | `aerki.radar` | 20400 Detections, 20401 Status |
| 20410 – 20429 | `aerki.sensor` | 20410 AirQuality, 20411 Hotspot |
| 20430 – 20499 | reserved for future AERKI namespaces | – |

## Services

| Range | Namespace | Allocated |
|---|---|---|
| 230 – 239 | all AERKI services | 230 radar.SetBeam |

Service 210 was the first choice for `SetBeam`, but it collides with Hobbywing's ESC `SetID`. That's why the
collision check exists.

## Rules

1. A new namespace gets a block in this file before its first type is added. `validate.py` rejects types without one.
2. Never change a type's fields once it's released. The data-type signature would change and break deployed nodes.
   Add a new type with a new ID instead.
3. Use SI units (m, m/s, rad, °C) and say so in a comment on every field.
