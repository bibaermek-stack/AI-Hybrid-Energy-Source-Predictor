"""Unit tests for microgrid simulation (education labs P1)."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.simulation.adapters.weather_profile import synthetic_day_profile
from src.simulation.microgrid.battery_ess import BatteryESS
from src.simulation.microgrid.engine import run_day_simulation, run_mppt_trace, summarize_day
from src.simulation.microgrid.mppt import MPPTController
from src.simulation.microgrid.solar_panel import SolarArray, SolarPanelConfig


class TestSolarArray(unittest.TestCase):
    def test_zero_irradiance(self):
        arr = SolarArray(SolarPanelConfig(), num_panels=10)
        self.assertEqual(arr.calculate_power(0, 25), 0.0)

    def test_power_scales_with_panels(self):
        cfg = SolarPanelConfig(area=1.6, efficiency=0.2, temp_coefficient=0.0)
        p1 = SolarArray(cfg, 10).calculate_power(1000, 25)
        p2 = SolarArray(cfg, 20).calculate_power(1000, 25)
        self.assertAlmostEqual(p2, 2 * p1, places=5)


class TestBatteryESS(unittest.TestCase):
    def test_charge_increases_soc(self):
        b = BatteryESS(10, 5, efficiency=1.0, initial_soc_frac=0.2)
        b.charge(2000, 1.0)
        self.assertGreater(b.get_soc(), 0.2)

    def test_discharge_empty(self):
        b = BatteryESS(1, 10, efficiency=1.0, initial_soc_frac=0.0)
        deficit = b.discharge(1000, 1.0)
        self.assertGreater(deficit, 0)


class TestMPPT(unittest.TestCase):
    def test_optimize_updates_ref(self):
        m = MPPTController(step_size=0.5)
        v0 = m.v_ref
        m.optimize(24.0, 5.0)
        m.optimize(24.5, 5.1)
        self.assertNotEqual(m.v_ref, v0)


class TestEngine(unittest.TestCase):
    def test_run_day_columns(self):
        weather = synthetic_day_profile()
        df = run_day_simulation(weather, num_panels=50, battery_kwh=20, load_kw=10)
        for col in ("pv_kw", "load_kw", "soc", "grid_import_kw", "grid_export_kw"):
            self.assertIn(col, df.columns)
        self.assertEqual(len(df), 24)
        self.assertTrue((df["soc"] >= 0).all() and (df["soc"] <= 1).all())

    def test_summarize(self):
        weather = synthetic_day_profile()
        df = run_day_simulation(weather, num_panels=80, battery_kwh=40, load_kw=12)
        s = summarize_day(df)
        self.assertGreaterEqual(s["pv_kwh"], 0)
        self.assertGreaterEqual(s["load_kwh"], 0)

    def test_mppt_trace(self):
        df = run_mppt_trace(800, step_size=0.5, steps=40)
        self.assertEqual(len(df), 40)
        self.assertIn("p", df.columns)


if __name__ == "__main__":
    unittest.main()
