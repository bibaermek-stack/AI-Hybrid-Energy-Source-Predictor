import unittest
from fastapi.testclient import TestClient
from api.main import app

class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("models_loaded", data)

    def test_predict_endpoint_valid(self):
        health = self.client.get("/health").json()
        if health["status"] == "healthy":
            payload = {
                "irradiation": 800.0,
                "temperature": 25.0,
                "module": 30.0,
                "hour": 12,
                "day": 15,
                "month": 6,
                "wind_speed": 12.0,
                "direction": 180.0,
                "theoretical": 1000.0
            }
            response = self.client.post("/predict", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("solar_power", data)
            self.assertIn("wind_power", data)
            self.assertIn("total_energy", data)
            self.assertIn("recommended_source", data)

    def test_predict_endpoint_invalid_input(self):
        payload = {
            "irradiation": -500.0,  # Invalid negative (min is 0 in schema)
            "temperature": 25.0,
            "module": 30.0,
            "hour": 12,
            "day": 15,
            "month": 6,
            "wind_speed": 12.0,
            "direction": 180.0,
            "theoretical": 1000.0
        }
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 422)  # Pydantic validation error

    def test_explain_endpoint_solar(self):
        response = self.client.post("/explain", json={"source": "Solar"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("explanation", data)
        self.assertTrue("Solar" in data["explanation"] or "solar" in data["explanation"].lower())

    def test_explain_endpoint_wind(self):
        response = self.client.post("/explain", json={"source": "Wind"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("explanation", data)
        self.assertTrue("Wind" in data["explanation"] or "wind" in data["explanation"].lower())

    def test_chat_endpoint_valid(self):
        response = self.client.post("/chat", json={"query": "how does temperature affect solar panels?", "lang": "en"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertTrue("solar" in data["response"].lower() or "temperature" in data["response"].lower())

    def test_forecast_endpoint_check(self):
        sequence = [[0.5, 25.0, 30.0, 12, 15, 6] for _ in range(24)]
        response = self.client.post("/forecast", json={"sequence": sequence})
        self.assertIn(response.status_code, [200, 503])

if __name__ == "__main__":
    unittest.main()

