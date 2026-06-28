import unittest
import numpy as np
from src.optimization.hybrid_optimizer import optimize_energy

class TestHybridOptimizer(unittest.TestCase):
    def test_solar_recommended(self):
        # Solar has higher output
        result = optimize_energy(100.0, 50.0)
        self.assertEqual(result["recommended_source"], "Solar")
        self.assertEqual(result["solar_power"], 100.0)
        self.assertEqual(result["wind_power"], 50.0)
        self.assertEqual(result["total_energy"], 150.0)

    def test_wind_recommended(self):
        # Wind has higher output
        result = optimize_energy(30.0, 80.0)
        self.assertEqual(result["recommended_source"], "Wind")
        self.assertEqual(result["total_energy"], 110.0)

    def test_invalid_negative_values(self):
        # Negative values should raise ValueError
        with self.assertRaises(ValueError):
            optimize_energy(-10.0, 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(10.0, -50.0)

    def test_invalid_types(self):
        # Non-numeric values should raise ValueError
        with self.assertRaises(ValueError):
            optimize_energy("100", 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(100.0, None)

    def test_nan_or_inf_values(self):
        # NaN or Inf values should raise ValueError
        with self.assertRaises(ValueError):
            optimize_energy(np.nan, 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(100.0, np.inf)

if __name__ == "__main__":
    unittest.main()
