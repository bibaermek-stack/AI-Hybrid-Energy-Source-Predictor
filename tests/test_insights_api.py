"""
Endpoints behind the mobile Training, Sustainability and Labs screens, plus the
/predict fields the mobile screens read.
"""

import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.schemas import PredictionResponse

ROOT = Path(__file__).resolve().parents[1]


class TestMetricsEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_serves_the_committed_metrics_file(self):
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        committed = json.loads((ROOT / "artifacts" / "model_metrics.json").read_text(encoding="utf-8"))
        self.assertEqual(data["solar_forecast"], committed["solar_forecast"])
        self.assertEqual(
            data["yolo11n"]["test"], committed["yolo11n_fault_detection"]["test_set_all"]
        )

    def test_feature_importances_come_from_the_loaded_models(self):
        data = self.client.get("/metrics").json()
        solar = data["feature_importance"]["solar"]
        wind = data["feature_importance"]["wind"]
        # solar_model.pkl is trained on six columns, wind_model.pkl on three.
        self.assertEqual(len(solar), 6)
        self.assertEqual(len(wind), 3)
        for items in (solar, wind):
            self.assertAlmostEqual(sum(i["importance"] for i in items), 1.0, places=2)
            values = [i["importance"] for i in items]
            self.assertEqual(values, sorted(values, reverse=True))
        self.assertEqual(solar[0]["feature"], "IRRADIATION")


class TestSustainabilityImpact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_co2_and_equivalents(self):
        response = self.client.post(
            "/sustainability/impact",
            json={"renewable_kwh": 1000, "grid_import_kwh": 0, "grid_factor_kg_per_kwh": 0.45},
        )
        self.assertEqual(response.status_code, 200)
        carbon = response.json()["carbon"]
        self.assertAlmostEqual(carbon["co2_avoided_kg"], 450.0)
        self.assertAlmostEqual(carbon["co2_net_benefit_kg"], 450.0)
        self.assertAlmostEqual(carbon["trees_year_equiv"], 450.0 / 21.0)
        self.assertAlmostEqual(response.json()["energy"]["self_sufficiency_pct"], 100.0)

    def test_grid_import_reduces_self_sufficiency(self):
        energy = self.client.post(
            "/sustainability/impact", json={"renewable_kwh": 750, "grid_import_kwh": 250}
        ).json()["energy"]
        self.assertAlmostEqual(energy["self_sufficiency_pct"], 75.0)

    def test_rejects_negative_energy(self):
        response = self.client.post("/sustainability/impact", json={"renewable_kwh": -1})
        self.assertEqual(response.status_code, 422)


class TestMicrogridDayLab(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_synthetic_day_runs_24_hours(self):
        response = self.client.post(
            "/labs/microgrid-day",
            json={"num_panels": 100, "battery_kwh": 50, "load_kw": 15, "inverter_kw": 40, "weather": "synthetic"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["weather_source"], "synthetic")
        self.assertEqual(len(data["hours"]), 24)
        summary = data["summary"]
        self.assertAlmostEqual(summary["load_kwh"], 15 * 24, places=1)
        self.assertGreater(summary["pv_kwh"], 0)
        for hour in data["hours"]:
            self.assertGreaterEqual(hour["soc"], 0.0)
            self.assertLessEqual(hour["soc"], 1.0)

    def test_more_panels_produce_more_pv(self):
        def pv(panels):
            return self.client.post(
                "/labs/microgrid-day", json={"num_panels": panels, "weather": "synthetic"}
            ).json()["summary"]["pv_kwh"]

        self.assertGreater(pv(200), pv(50))

    def test_reports_the_profile_actually_used(self):
        data = self.client.post("/labs/microgrid-day", json={"weather": "sample"}).json()
        self.assertEqual(data["weather_source"], "sample")

    def test_rejects_unknown_weather_source(self):
        response = self.client.post("/labs/microgrid-day", json={"weather": "moon"})
        self.assertEqual(response.status_code, 422)


class TestMobilePredictContract(unittest.TestCase):
    """
    Fields the mobile screens read from POST /predict. The optimization screen
    once read an `optimal_dispatch` block the API never returned and silently
    showed fallbacks; a missing field here fails loudly instead.
    """

    READ_BY_MOBILE = {
        "solar_power",
        "wind_power",
        "total_energy",
        "recommended_source",
        "solar_used",
        "wind_used",
        "battery_used",
        "shortfall_kw",
        "curtailment_kw",
        "reliability_index",
        "estimated_cost",
        "wind_share",
    }

    def test_prediction_response_has_every_field_mobile_reads(self):
        missing = self.READ_BY_MOBILE - set(PredictionResponse.model_fields)
        self.assertEqual(missing, set())


if __name__ == "__main__":
    unittest.main()
