"""Tests for the 3D inverter trainer's board (src/education/inverter_lab.py)."""

from __future__ import annotations

import unittest

from src.education.inverter_lab import (
    CORRECT,
    diagnose_faults,
    grade_wiring,
    initial_state,
    list_scenarios,
    normalize_state,
    status_table,
)
from src.education.lab_tasks import check_task_answer, list_lab_task_ids


class TestInverterLab(unittest.TestCase):
    def test_scenarios_exist(self):
        ids = {s["id"] for s in list_scenarios("en")}
        self.assertIn("reversed_dc", ids)
        self.assertIn("compound", ids)
        self.assertEqual(len({s["title"] for s in list_scenarios("kk")}), len(ids))

    def test_healthy_grades_ok(self):
        r = grade_wiring(dict(CORRECT))
        self.assertTrue(r["ok"])
        self.assertEqual(r["score"], r["total"])

    def test_reversed_dc_fault(self):
        st = initial_state("reversed_dc")
        self.assertEqual(diagnose_faults(st), ["dc_polarity"])
        self.assertFalse(grade_wiring(st)["ok"])
        st["dc_polarity"] = "ok"
        self.assertTrue(grade_wiring(st)["ok"])

    def test_compound_needs_multiple_fixes(self):
        st = initial_state("compound")
        self.assertGreaterEqual(len(diagnose_faults(st)), 3)
        st.update(CORRECT)
        self.assertTrue(grade_wiring(st)["ok"])

    def test_unknown_values_are_not_trusted(self):
        self.assertEqual(normalize_state({"dc_isolator": "sideways"})["dc_isolator"], "on")
        self.assertEqual(len(status_table()), 64)

    def test_lab_tasks_bank(self):
        ids = list_lab_task_ids("lab_inverter_wiring")
        self.assertGreaterEqual(len(ids), 3)
        r = check_task_answer("lab_inverter_wiring", "dc_polarity", choice_index=1)
        self.assertTrue(r["ok"])
        r2 = check_task_answer("lab_inverter_wiring", "dc_polarity", choice_index=0)
        self.assertEqual(r2["status"], "wrong")


if __name__ == "__main__":
    unittest.main()
