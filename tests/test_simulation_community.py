"""Unit tests for CACER-inspired community adapters and P2 compare."""

from __future__ import annotations

import unittest

import numpy as np

from src.education.labs.lab_registry import LAB_IDS, LABS, list_labs
from src.education.progress import ProgressTracker
from src.education.quiz import get_quiz, grade_quiz
from src.simulation.adapters.weather_profile import synthetic_day_profile
from src.simulation.community.bess_step import bess_step, simulate_bess_series
from src.simulation.community.cacer_path import get_cacer_root, power_flow_notebook_path, sim_cacer_status
from src.simulation.community.financial_kpis import community_project_kpis, irr
from src.simulation.community.load_profile import scale_profile, synthetic_load_profile
from src.simulation.community.shared_energy import run_shared_energy_day
from src.simulation.microgrid.compare_pulp import compare_heuristic_vs_pulp


class TestBessStep(unittest.TestCase):
    def test_charge_raises_soc(self):
        r = bess_step(10.0, 20.0, eta_halfcycle=1.0, battery_min_kwh=0.0, battery_max_kwh=100.0)
        self.assertGreater(r.soc_kwh, 20.0)
        self.assertAlmostEqual(r.soc_frac, r.soc_kwh / 100.0)

    def test_discharge_floor(self):
        r = bess_step(-50.0, 5.0, eta_halfcycle=1.0, battery_min_kwh=5.0, battery_max_kwh=100.0)
        self.assertAlmostEqual(r.soc_kwh, 5.0)

    def test_series_length(self):
        steps = simulate_bess_series([5, -3, 2, -1], capacity_kwh=20, dod=0.8)
        self.assertEqual(len(steps), 4)
        self.assertTrue(all(0.0 <= s.soc_frac <= 1.0 for s in steps))


class TestLoadProfile(unittest.TestCase):
    def test_deterministic_seed(self):
        a = synthetic_load_profile(24, seed=7)
        b = synthetic_load_profile(24, seed=7)
        np.testing.assert_allclose(a["load_kw"].to_numpy(), b["load_kw"].to_numpy())

    def test_scale_peak(self):
        df = synthetic_load_profile(24, seed=1)
        scaled = scale_profile(df, peak_kw=10.0)
        self.assertAlmostEqual(float(scaled["load_kw"].max()), 10.0, places=5)


class TestSharedEnergy(unittest.TestCase):
    def test_day_kpis(self):
        weather = synthetic_day_profile()
        out = run_shared_energy_day(
            weather,
            n_users=3,
            panels_per_user=40,
            peak_load_kw=4.0,
            community_battery_kwh=30.0,
            seed=42,
        )
        self.assertIn("timeseries", out)
        self.assertEqual(len(out["timeseries"]), 24)
        self.assertGreaterEqual(out["pv_kwh"], 0)
        self.assertGreaterEqual(out["shared_kwh"], 0)
        self.assertGreaterEqual(out["import_kwh"], 0)
        # energy accounting soft check
        self.assertGreater(out["load_kwh"], 0)


class TestFinancialKpis(unittest.TestCase):
    def test_simple_project(self):
        k = community_project_kpis(
            capex=100_000,
            annual_generation_kwh=150_000,
            price_per_kwh=0.12,
            opex_annual=2000,
            lifetime_years=20,
            discount_rate=0.05,
        )
        self.assertIn("lcoe", k)
        self.assertIn("npv", k)
        self.assertIn("irr", k)
        self.assertGreater(k["annual_net_savings"], 0)
        self.assertLess(k["payback_years"], 20)

    def test_irr_known(self):
        # -100 then +60 +60 → IRR ~ 13.7%
        r = irr([-100.0, 60.0, 60.0])
        self.assertTrue(r == r)  # not nan
        self.assertGreater(r, 0.1)
        self.assertLess(r, 0.2)


class TestComparePulp(unittest.TestCase):
    def test_compare_runs(self):
        weather = synthetic_day_profile()
        res = compare_heuristic_vs_pulp(
            weather,
            num_panels=60,
            battery_kwh=30.0,
            load_kw=10.0,
            mode="balanced",
        )
        self.assertIn("heuristic_summary", res)
        self.assertIn("pulp_import_kwh", res)
        self.assertIn("delta_import_kwh", res)
        self.assertGreaterEqual(res["heuristic_summary"]["pv_kwh"], 0)
        self.assertIsNotNone(res["pulp_schedule"])


class TestCacerPath(unittest.TestCase):
    def test_status_keys(self):
        s = sim_cacer_status()
        for key in (
            "cacer_present",
            "pandapower",
            "pvlib",
            "install_hint",
            "ecopredict_notebook",
        ):
            self.assertIn(key, s)
        self.assertTrue(str(s["install_hint"]).startswith("pip"))

    def test_notebook_path(self):
        p = power_flow_notebook_path()
        self.assertTrue(str(p).endswith("power_flow.ipynb"))

    def test_submodule_if_present(self):
        root = get_cacer_root()
        # CI without submodule: None is OK; local/dev with submodule: dir exists
        if root is not None:
            self.assertTrue(root.is_dir())


class TestLabRegistryAndProgress(unittest.TestCase):
    def test_registry_complete(self):
        labs = list_labs()
        self.assertGreaterEqual(len(labs), 10)
        for lid in LAB_IDS:
            self.assertIn(lid, LABS)
            self.assertIn("title", LABS[lid])
            self.assertIn("render", LABS[lid])

    def test_progress_labs_done(self):
        store: dict = {}
        p = ProgressTracker(store)
        p.mark_lab("lab_shared_energy")
        self.assertTrue(p.lab_done("lab_shared_energy"))
        sm = p.summary()
        self.assertEqual(sm["labs_completed"], 1)
        self.assertIn("lab_shared_energy", sm["labs_list"])

    def test_lab_quiz_grades(self):
        qid = "lab_shared_energy_quiz"
        quiz = get_quiz(qid, "en")
        self.assertIsNotNone(quiz)
        answers = {q["id"]: 0 for q in quiz["questions"]}  # type: ignore[index]
        # force correct indices from bank via grade after reading correct
        from src.education.quiz import QUIZ_BANK

        answers = {
            q["id"]: q["correct_index"] for q in QUIZ_BANK[qid]["questions"]
        }
        g = grade_quiz(qid, answers)
        self.assertEqual(g["percent"], 100.0)


if __name__ == "__main__":
    unittest.main()
