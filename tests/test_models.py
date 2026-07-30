import math
import unittest

import numpy as np

from src.optimization.hybrid_optimizer import (
    BatteryParams,
    HybridEnergyOptimizer,
    optimize_energy,
)


class TestHybridOptimizer(unittest.TestCase):
    def test_solar_primary_when_dominant(self):
        result = optimize_energy(100.0, 50.0)
        self.assertEqual(result["recommended_source"], "Solar")
        self.assertEqual(result["solar_power"], 100.0)
        self.assertEqual(result["wind_power"], 50.0)
        self.assertEqual(result["total_energy"], 150.0)
        self.assertGreater(result["solar_share"], 0.6)

    def test_wind_primary_when_dominant(self):
        result = optimize_energy(30.0, 80.0)
        self.assertEqual(result["recommended_source"], "Wind")
        self.assertEqual(result["total_energy"], 110.0)

    def test_hybrid_when_balanced(self):
        result = optimize_energy(100.0, 100.0)
        self.assertEqual(result["recommended_source"], "Hybrid")
        self.assertAlmostEqual(result["hybrid_share"], 1.0, places=3)

    def test_load_following_and_battery(self):
        result = optimize_energy(
            200.0, 100.0, load_kw=350.0, battery_kw=40.0, strategy="hybrid"
        )
        self.assertAlmostEqual(result["solar_used"] + result["wind_used"], 300.0)
        self.assertAlmostEqual(result["battery_used"], 40.0)
        self.assertAlmostEqual(result["shortfall_kw"], 10.0)
        self.assertLess(result["reliability_index"], 1.0)
        self.assertGreater(result["reliability_index"], 0.9)

    def test_min_cost_prefers_cheaper_source(self):
        result = optimize_energy(
            400.0,
            400.0,
            load_kw=300.0,
            solar_cost_per_kwh=3.0,
            wind_cost_per_kwh=1.0,
            strategy="min_cost",
        )
        self.assertAlmostEqual(result["wind_used"], 300.0)
        self.assertAlmostEqual(result["solar_used"], 0.0)
        self.assertEqual(result["recommended_source"], "Wind")
        self.assertAlmostEqual(result["curtailment_kw"], 500.0)

    def test_curtailment_when_oversupply(self):
        result = optimize_energy(500.0, 500.0, load_kw=200.0, strategy="balanced")
        self.assertAlmostEqual(result["solar_used"] + result["wind_used"], 200.0)
        self.assertAlmostEqual(result["curtailment_kw"], 800.0)
        self.assertAlmostEqual(result["reliability_index"], 1.0)

    def test_invalid_negative_values(self):
        with self.assertRaises(ValueError):
            optimize_energy(-10.0, 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(10.0, -50.0)

    def test_invalid_types(self):
        with self.assertRaises(ValueError):
            optimize_energy("100", 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(100.0, None)

    def test_nan_or_inf_values(self):
        with self.assertRaises(ValueError):
            optimize_energy(float("nan"), 50.0)
        with self.assertRaises(ValueError):
            optimize_energy(100.0, float("inf"))

    def test_unknown_strategy(self):
        with self.assertRaises(ValueError):
            optimize_energy(10.0, 10.0, strategy="magic")


class TestHybridEnergyOptimizerLP(unittest.TestCase):
    def test_24h_balanced_solves(self):
        hours = np.arange(24)
        solar = np.clip(np.sin((hours - 6) * np.pi / 14) * 100, 0, None)
        solar = np.where((hours >= 6) & (hours <= 18), solar, 0.0)
        wind = np.full(24, 30.0)
        load = np.full(24, 50.0)
        opt = HybridEnergyOptimizer(
            battery=BatteryParams(capacity_kwh=100, max_charge_kw=40, max_discharge_kw=40),
            co2_grid_kg_per_kwh=0.4,
        )
        res = opt.optimize(solar, wind, load=load, mode="balanced")
        self.assertIn(res["status"], ("Optimal", "Not Solved", "Undefined"))
        # CBC should find optimal on this small LP
        self.assertEqual(res["status"], "Optimal")
        self.assertEqual(len(res["schedule"]), 24)
        self.assertIn("soc", res["schedule"].columns)
        self.assertGreaterEqual(res["self_consumption_rate"], 0.0)
        self.assertLessEqual(res["self_consumption_rate"], 100.0)

    def test_negative_forecast_clipped(self):
        opt = HybridEnergyOptimizer()
        res = opt.optimize([-10, 20], [5, -3], load=10, mode="max_profit")
        self.assertEqual(len(res["schedule"]), 2)
        self.assertTrue((res["schedule"]["solar_avail"] >= 0).all())


if __name__ == "__main__":
    unittest.main()
