"""The shared engine of the 12 labs (src/education/labs/runner.py)."""

from __future__ import annotations

import json
import unittest

from src.education.labs.lab_registry import LAB_IDS
from src.education.labs.runner import LABS, default_params, metric_value, run_lab, validate_params


class TestEveryLabRuns(unittest.TestCase):
    def test_registry_and_engine_list_the_same_12_labs(self):
        self.assertEqual(len(LAB_IDS), 12)
        self.assertEqual(set(LABS), set(LAB_IDS))

    def test_default_run_is_plain_json(self):
        for lab_id in LAB_IDS:
            with self.subTest(lab=lab_id):
                res = run_lab(lab_id)
                json.dumps(res, allow_nan=False)  # NaN would break the phone's JSON parser
                self.assertTrue(res["metrics"])
                for m in res["metrics"]:
                    self.assertIn("en", m["label"])
                    self.assertIn("kk", m["label"])
                for ch in res["charts"]:
                    for s in ch["series"]:
                        self.assertEqual(len(s["values"]), len(ch["x"]), f"{lab_id}/{ch['id']}")

    def test_every_parameter_is_labelled_in_both_languages(self):
        for lab_id in LAB_IDS:
            for spec in LABS[lab_id]["params"]:
                self.assertTrue(
                    spec["label"]["en"] and spec["label"]["kk"], f"{lab_id}.{spec['key']}"
                )


class TestValidation(unittest.TestCase):
    def test_missing_keys_take_defaults_and_numbers_are_clamped(self):
        p = validate_params("lab_pv_physics", {"n": 100000, "irr": -5})
        self.assertEqual(p["n"], 400)
        self.assertEqual(p["irr"], 0)
        self.assertEqual(p["area"], default_params("lab_pv_physics")["area"])

    def test_unknown_choice_and_bad_numbers_are_rejected(self):
        with self.assertRaises(ValueError):
            validate_params("lab_grid_impact", {"cable": "copper"})
        with self.assertRaises(ValueError):
            validate_params("lab_pv_physics", {"n": "many"})
        with self.assertRaises(KeyError):
            run_lab("lab_unknown")


class TestPhysicsFixes(unittest.TestCase):
    def test_battery_never_goes_below_the_dod_floor(self):
        # Before: SOC fell to 0 % while the lab's theory said SOC_min = 1 − DoD.
        for dod in (0.5, 0.8):
            res = run_lab("lab_bess_soc", {"dod": dod, "weather": "synthetic"})
            self.assertGreaterEqual(metric_value(res, "soc_min_pct"), 100 * (1 - dod) - 1e-6)

    def test_shared_energy_needs_consumers(self):
        # Before: every household had PV, so nothing was ever shared.
        mixed = run_lab("lab_shared_energy", {"n_users": 4, "pv_users": 2, "weather": "synthetic"})
        all_pv = run_lab("lab_shared_energy", {"n_users": 4, "pv_users": 4, "weather": "synthetic"})
        self.assertGreater(metric_value(mixed, "shared_kwh"), 0)
        self.assertLess(metric_value(all_pv, "shared_kwh"), metric_value(mixed, "shared_kwh"))

    def test_shared_energy_without_a_battery(self):
        # Before: bat = 0 (allowed by the slider) raised "battery_max_kwh must be > battery_min_kwh".
        res = run_lab("lab_shared_energy", {"bat": 0, "weather": "synthetic"})
        self.assertGreater(metric_value(res, "import_kwh"), 0)

    def test_grid_lab_runs_without_pandapower(self):
        res = run_lab(
            "lab_grid_impact", {"houses": 12, "length": 800, "cable": "nayy_4x50", "pv_kw": 8}
        )
        self.assertGreater(metric_value(res, "v_max_pu"), 1.10)
        thick = run_lab(
            "lab_grid_impact", {"houses": 12, "length": 800, "cable": "nayy_4x150", "pv_kw": 8}
        )
        self.assertLess(metric_value(thick, "v_max_pu"), metric_value(res, "v_max_pu"))

    def test_inverter_board_is_graded(self):
        ok = run_lab("lab_inverter_wiring")
        self.assertTrue(ok["grade"]["ok"])
        bad = run_lab("lab_inverter_wiring", {"dc_polarity": "reversed"})
        self.assertFalse(bad["grade"]["ok"])
        self.assertEqual(bad["grade"]["status"]["code"], "DC_POLARITY")


class TestProgressCountsLabs(unittest.TestCase):
    def test_simulation_runs_do_not_count_as_completed_labs(self):
        # The site marked "lab_x_sim" exercises, which the tracker back-filled as
        # completed labs: 11 runs showed "22 of 12 labs".
        from src.education.progress import ProgressTracker

        store = {}
        p = ProgressTracker(store)
        p.mark_exercise("sim:lab_pv_physics")
        p.mark_exercise("lab_pv_physics_sim")  # old sessions
        p.mark_lab("lab_grid_impact")
        again = ProgressTracker(store)  # re-open the session: migration runs
        self.assertEqual(again.summary()["labs_completed"], 1)
        self.assertEqual(again.summary()["labs_list"], ["lab_grid_impact"])
