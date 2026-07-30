import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestSolarmanAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        
    def test_process_endpoint_valid(self):
        payload = {
            "payload": {
                "status": 1,
                "deviceId": 12345,
                "deviceSn": "SN12345",
                "dataList": [
                    {"key": "APo", "value": "25.0", "unit": "kW"},
                    {"key": "eToday", "value": "120.0", "unit": "kWh"},
                    {"key": "T_val", "value": "35.0", "unit": "°C"}
                ]
            },
            "dc_capacity_kwp": 50.0,
            "irradiance_w_m2": 800.0,
            "ambient_temp_c": 25.0
        }
        response = self.client.post("/solarman/process", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("parsed_data", data)
        self.assertIn("active_power_kw", data)
        self.assertIn("raw_pr", data)
        self.assertIn("corrected_pr", data)
        
        # Expected raw PR: Active Power (25.0 kW) / (Nominal (50.0 kWp) * (Irradiance (800) / 1000))
        # Expected expected_power_kw: 50.0 * 0.8 = 40.0 kW
        # Expected raw_pr: 25.0 / 40.0 = 0.625
        self.assertEqual(data["expected_power_kw"], 40.0)
        self.assertEqual(data["raw_pr"], 0.625)

    def test_process_endpoint_invalid_irradiance(self):
        payload = {
            "payload": {
                "status": 1,
                "dataList": []
            },
            "dc_capacity_kwp": 50.0,
            "irradiance_w_m2": -50.0  # Invalid negative (min gt 0 in schema)
        }
        response = self.client.post("/solarman/process", json=payload)
        self.assertEqual(response.status_code, 422)  # Pydantic validation error

    def test_roi_endpoint_valid(self):
        payload = {
            "total_generation_kwh": 45000.0,
            "initial_investment_kzt": 15000000.0,
            "tariff_kzt_per_kwh": 28.0,
            "opex_annual_kzt": 50000.0,
            "annual_degradation": 0.005,
            "inflation_rate": 0.05,
            "lifetime_years": 25
        }
        response = self.client.post("/solarman/roi", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("initial_investment_kzt", data)
        self.assertIn("cumulative_savings_kzt", data)
        self.assertIn("roi_pct", data)
        self.assertIn("payback_period_years", data)
        
        # Ensure values are strictly positive
        self.assertGreater(data["cumulative_savings_kzt"], 0)
        self.assertGreater(data["roi_pct"], 0)

    def test_weather_endpoint(self):
        response = self.client.get("/solarman/weather")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("location", data)
        self.assertIn("temperature_2m_c", data)
        self.assertIn("cloud_cover_pct", data)
        self.assertIn("uv_index", data)

    def test_alert_endpoint_healthy(self):
        payload = {
            "parsed_data": {
                "deviceId": 12345,
                "deviceSn": "SN12345",
                "faultCode": 0,
                "deviceStatus": 1
            }
        }
        response = self.client.post("/solarman/alert", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertFalse(data["is_offline"])
        self.assertFalse(data["is_faulty"])
        self.assertFalse(data["alert_sent"])

    def test_alert_endpoint_offline(self):
        payload = {
            "parsed_data": {
                "deviceId": 12345,
                "deviceSn": "SN12345",
                "faultCode": 0,
                "deviceStatus": 0  # Offline
            }
        }
        response = self.client.post("/solarman/alert", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data["is_offline"])
        self.assertFalse(data["is_faulty"])
        self.assertIn("OFFLINE", data["alert_message"])

    def test_forecast_endpoint(self):
        response = self.client.get("/solarman/forecast?dc_capacity_kwp=50.0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("forecasts", data)
        self.assertEqual(len(data["forecasts"]), 24)
        first_hour = data["forecasts"][0]
        self.assertIn("time", first_hour)
        self.assertIn("predicted_power_kw", first_hour)
        self.assertIn("cloud_cover", first_hour)
        self.assertIn("temperature", first_hour)

if __name__ == "__main__":
    unittest.main()
