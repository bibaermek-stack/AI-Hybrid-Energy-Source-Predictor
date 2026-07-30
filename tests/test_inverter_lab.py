"""Tests for inverter wiring trainer."""

from __future__ import annotations

import unittest

from src.education.inverter_lab import (
    CORRECT,
    diagnose_faults,
    grade_wiring,
    initial_state,
    list_scenarios,
)
from src.education.lab_tasks import check_task_answer, list_lab_task_ids


class TestInverterLab(unittest.TestCase):
    def test_scenarios_exist(self):
        sc = list_scenarios("en")
        ids = {s["id"] for s in sc}
        self.assertIn("reversed_dc", ids)
        self.assertIn("compound", ids)

    def test_healthy_grades_ok(self):
        r = grade_wiring(dict(CORRECT))
        self.assertTrue(r["ok"])
        self.assertEqual(r["score"], r["total"])

    def test_reversed_dc_fault(self):
        st = initial_state("reversed_dc")
        tags = diagnose_faults(st)
        self.assertIn("reversed_dc", tags)
        r = grade_wiring(st)
        self.assertFalse(r["ok"])
        # Fix
        st["dc_pos"] = "pv_pos"
        st["dc_neg"] = "pv_neg"
        self.assertTrue(grade_wiring(st)["ok"])

    def test_compound_needs_multiple_fixes(self):
        st = initial_state("compound")
        self.assertGreaterEqual(len(diagnose_faults(st)), 2)
        st.update(CORRECT)
        self.assertTrue(grade_wiring(st)["ok"])

    def test_lab_tasks_bank(self):
        ids = list_lab_task_ids("lab_inverter_wiring")
        self.assertGreaterEqual(len(ids), 3)
        r = check_task_answer("lab_inverter_wiring", "dc_polarity", choice_index=1)
        self.assertTrue(r["ok"])
        r2 = check_task_answer("lab_inverter_wiring", "dc_polarity", choice_index=0)
        self.assertEqual(r2["status"], "wrong")


if __name__ == "__main__":
    unittest.main()
