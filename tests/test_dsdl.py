"""Round-trip and rule checks for the aerki DSDL:  python3 -m unittest discover -s tests"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tools'))

import dronecan  # noqa: E402
from dronecan import transport  # noqa: E402

import validate  # noqa: E402

dronecan.load_dsdl(validate.ROOT)
A = dronecan.thirdparty.aerki   # custom namespaces are attached under `thirdparty`


def roundtrip(msg, canfd):
    """Encode msg into real DroneCAN frames, decode it back; return (decoded payload, frame count)."""
    frames = transport.Transfer(payload=msg, source_node_id=42, transfer_id=7, transfer_priority=16,
                                service_not_message=False, canfd=canfd).to_frames()
    t = transport.Transfer()
    t.from_frames(frames)
    return t.payload, len(frames)


class Validation(unittest.TestCase):
    def test_no_problems(self):
        self.assertEqual(validate.check(validate.load()), [])

    def test_docs_up_to_date(self):
        import gen_docs
        with open(gen_docs.OUT) as f:
            self.assertEqual(f.read(), gen_docs.render(validate.load()),
                             'docs/types.md is stale: run python3 tools/gen_docs.py')


class RoundTrip(unittest.TestCase):
    def test_radar_detections_full(self):
        targets = [A.radar.Target(range=10.0 + i, azimuth=0.1 * i, elevation=-0.05, radial_velocity=-3.5, snr=20.0)
                   for i in range(16)]
        msg = A.radar.Detections(sensor_id=3, frame_index=65535, scan_complete=True,
                                 beam_azimuth=0.5, beam_elevation=0.0, targets=targets)
        for fd in (False, True):
            out, n = roundtrip(msg, fd)
            self.assertEqual(len(out.targets), 16)
            self.assertEqual(out.frame_index, 65535)
            self.assertTrue(out.scan_complete)
            self.assertAlmostEqual(out.targets[15].range, 25.0, delta=0.02)   # float16 precision
            self.assertAlmostEqual(out.targets[3].radial_velocity, -3.5, places=3)
        self.assertEqual(roundtrip(msg, True)[1], 3)       # 175 B fits in three 64-byte CAN FD frames

    def test_radar_detections_empty(self):
        msg = A.radar.Detections(sensor_id=0, targets=[])
        out, n = roundtrip(msg, False)
        self.assertEqual(len(out.targets), 0)
        # 15 B of fixed fields + 2 B transfer CRC, 7 payload bytes per classic frame
        self.assertEqual(n, math.ceil((15 + 2) / 7))

    def test_radar_status_constants(self):
        msg = A.radar.Status(sensor_id=1, mode=A.radar.Status().MODE_SCAN, tx_enabled=True,
                             temperature=41.5, supply_voltage=5.02, frame_rate=121.0, beams_per_scan=7,
                             error_flags=0x80000001)
        out, _ = roundtrip(msg, False)
        self.assertEqual(out.mode, 2)
        self.assertEqual(out.error_flags, 0x80000001)
        self.assertAlmostEqual(out.supply_voltage, 5.02, delta=0.01)

    def test_air_quality_with_missing_channel(self):
        msg = A.sensor.AirQuality(sensor_id=2, pm1_0=4.0, pm2_5=12.5, pm10=20.0, co=float('nan'), co2=415.0,
                                  voc_index=100.0, temperature=24.5, humidity=55.0, status=0)
        out, n = roundtrip(msg, False)
        self.assertTrue(math.isnan(out.co))
        self.assertAlmostEqual(out.co2, 415.0, delta=0.5)
        self.assertEqual(n, 4)

    def test_hotspot_position_precision(self):
        lat, lon = 1.2834567, 103.8512345                  # Singapore
        msg = A.sensor.Hotspot(track_id=513, latitude_deg_1e7=round(lat * 1e7), longitude_deg_1e7=round(lon * 1e7),
                               position_error=4.0, peak_temperature=312.0, area=2.5, confidence=0.9)
        out, _ = roundtrip(msg, True)
        self.assertEqual(out.latitude_deg_1e7 / 1e7, round(lat * 1e7) / 1e7)   # exact: 1e-7 deg ~ 1.1 cm
        self.assertEqual(out.track_id, 513)
        self.assertAlmostEqual(out.peak_temperature, 312.0, delta=0.25)


if __name__ == '__main__':
    unittest.main()
