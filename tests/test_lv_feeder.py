"""Radial LV feeder load flow behind lab 11 (src/simulation/grid/lv_feeder.py)."""

from __future__ import annotations

import unittest

from src.simulation.grid.lv_feeder import approx_voltage_rise_pu, feeder_day, solve_feeder


class TestSolveFeeder(unittest.TestCase):
    def test_no_power_means_flat_voltage(self):
        r = solve_feeder(
            n_houses=10,
            length_m=400,
            cable="nayy_4x95",
            pv_kw_per_house=0,
            load_kw_per_house=0,
            v_source_pu=1.02,
        )
        self.assertAlmostEqual(r.v_min_pu, 1.02, places=9)
        self.assertAlmostEqual(r.v_max_pu, 1.02, places=9)
        self.assertAlmostEqual(r.losses_kw, 0.0, places=9)

    def test_export_raises_voltage_along_the_feeder(self):
        r = solve_feeder(
            n_houses=10,
            length_m=400,
            cable="nayy_4x95",
            pv_kw_per_house=8,
            load_kw_per_house=0,
            load_power_factor=1.0,
        )
        self.assertTrue(
            all(b >= a for a, b in zip(r.v_pu, r.v_pu[1:])), "voltage must rise toward the end"
        )
        self.assertGreater(r.v_pu[-1], 1.0)

    def test_matches_the_linearised_formula(self):
        exact = solve_feeder(
            n_houses=10,
            length_m=400,
            cable="nayy_4x95",
            pv_kw_per_house=8,
            load_kw_per_house=0,
            load_power_factor=1.0,
        )
        approx = approx_voltage_rise_pu(
            n_houses=10, length_m=400, cable="nayy_4x95", net_export_kw_per_house=8
        )
        self.assertAlmostEqual(exact.v_pu[-1] - 1.0, approx, delta=0.003)

    def test_load_drops_voltage(self):
        r = solve_feeder(
            n_houses=10, length_m=400, cable="nayy_4x95", pv_kw_per_house=0, load_kw_per_house=8
        )
        self.assertLess(r.v_pu[-1], 1.0)

    def test_reactive_absorption_and_thicker_cable_reduce_the_rise(self):
        base = dict(
            n_houses=10, length_m=400, pv_kw_per_house=8, load_kw_per_house=0, load_power_factor=1.0
        )
        r_thin = solve_feeder(cable="nayy_4x50", **base).v_max_pu
        r_thick = solve_feeder(cable="nayy_4x150", **base).v_max_pu
        r_pf = solve_feeder(cable="nayy_4x50", pv_power_factor=0.9, **base).v_max_pu
        self.assertLess(r_thick, r_thin)
        self.assertLess(r_pf, r_thin)

    def test_bad_input(self):
        with self.assertRaises(ValueError):
            solve_feeder(
                n_houses=0, length_m=400, cable="nayy_4x95", pv_kw_per_house=1, load_kw_per_house=1
            )
        with self.assertRaises(ValueError):
            solve_feeder(
                n_houses=3, length_m=400, cable="copper", pv_kw_per_house=1, load_kw_per_house=1
            )


class TestFeederDay(unittest.TestCase):
    def test_highest_voltage_is_around_noon(self):
        d = feeder_day(
            n_houses=12,
            length_m=800,
            cable="nayy_4x50",
            pv_kw_peak=8,
            load_kw_peak=3,
            v_source_pu=1.02,
        )
        self.assertEqual(len(d["v_max_pu"]), 24)
        self.assertIn(d["worst_hour"], range(11, 16))
        self.assertGreater(d["day_max_pu"], 1.10)
        self.assertGreater(d["hours_over_limit"], 0)
        self.assertEqual(len(d["worst_profile_pu"]), 13)
