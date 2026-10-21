import sys
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/python/brain"))
from telemetry_analysis import parse_telemetry_csv, compare_laps
import api

SAMPLE = """lap,distance_m,speed_kmh,throttle_pct,brake_pct\n1,0,40,80,0\n1,50,60,90,0\n1,100,80,100,0\n2,0,42,80,0\n2,50,65,95,0\n2,100,85,100,0\n"""

class TelemetryTests(unittest.TestCase):
    def test_import_normalizes_channels_and_laps(self):
        result = parse_telemetry_csv(SAMPLE)
        self.assertEqual(result["row_count"], 6)
        self.assertEqual(result["lap_count"], 2)
        self.assertIn("speed_kmh", result["normalized_channels"])
        self.assertEqual(result["lap_detection"], "provided lap column")

    def test_compare_distance_aligns_and_reports_delta(self):
        result = compare_laps(parse_telemetry_csv(SAMPLE), "1.0", "2.0")
        self.assertEqual(result["sample_count"], 101)
        self.assertAlmostEqual(result["summary"]["mean_speed_delta_kmh"], 4.243, places=2)
        self.assertEqual(result["evidence_label"], "CALCULATED from user-imported telemetry")

    def test_infer_laps_on_distance_reset(self):
        text = "distance_m,speed_kmh\n0,40\n50,60\n100,80\n0,41\n50,61\n100,81\n"
        result = parse_telemetry_csv(text)
        self.assertEqual(result["lap_count"], 2)
        self.assertIn("inferred", result["lap_detection"])

    def test_missing_speed_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "speed column"):
            parse_telemetry_csv("distance_m,throttle_pct\n0,50\n1,60\n")

    def test_api_import_and_compare(self):
        client = TestClient(api.app)
        imported = client.post("/telemetry/import", json={"csv_text": SAMPLE})
        self.assertEqual(imported.status_code, 200, imported.text)
        self.assertNotIn("rows", imported.json())
        compared = client.post("/telemetry/compare", json={"csv_text": SAMPLE, "reference_lap": "1.0", "comparison_lap": "2.0"})
        self.assertEqual(compared.status_code, 200, compared.text)
        self.assertEqual(len(compared.json()["trace"]), 101)

if __name__ == "__main__":
    unittest.main()
