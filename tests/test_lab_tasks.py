"""Tests for graded lab tasks (correct / wrong / try again)."""

from __future__ import annotations

import unittest

from src.education.lab_tasks import (
    LAB_TASKS,
    check_task_answer,
    get_lab_tasks,
    lab_tasks_progress,
    list_lab_task_ids,
)
from src.education.progress import ProgressTracker


class TestLabTasksBank(unittest.TestCase):
    def test_every_lab_has_tasks(self):
        # Core interactive labs (grid impact included)
        expected = [
            "lab_pv_physics",
            "lab_mppt_po",
            "lab_bess_soc",
            "lab_microgrid_dispatch",
            "lab_heuristic_vs_pulp",
            "lab_pv_yield",
            "lab_load_shape",
            "lab_bess_community",
            "lab_shared_energy",
            "lab_rec_finance",
            "lab_grid_impact",
            "lab_inverter_wiring",
        ]
        for lid in expected:
            self.assertIn(lid, LAB_TASKS, msg=lid)
            self.assertGreaterEqual(len(LAB_TASKS[lid]), 2, msg=lid)

    def test_resolved_ui_strings(self):
        tasks = get_lab_tasks("lab_pv_physics", "kk")
        self.assertTrue(tasks[0]["prompt"])
        self.assertIn(tasks[0]["kind"], ("number", "choice"))


class TestCheckAnswer(unittest.TestCase):
    def test_number_correct(self):
        r = check_task_answer("lab_pv_physics", "eta_eff", number=0.184)
        self.assertTrue(r["ok"])
        self.assertEqual(r["status"], "correct")

    def test_number_wrong(self):
        r = check_task_answer("lab_pv_physics", "eta_eff", number=0.99)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "wrong")
        self.assertIn("Try again", r["message_en"])
        self.assertIn("Қайтадан", r["message_kk"])

    def test_number_missing(self):
        r = check_task_answer("lab_pv_physics", "eta_eff", number=None)
        self.assertEqual(r["status"], "missing")

    def test_choice_correct(self):
        r = check_task_answer("lab_mppt_po", "po_direction", choice_index=1)
        self.assertTrue(r["ok"])

    def test_choice_wrong(self):
        r = check_task_answer("lab_mppt_po", "po_direction", choice_index=0)
        self.assertFalse(r["ok"])
        self.assertEqual(r["status"], "wrong")

    def test_payback(self):
        r = check_task_answer("lab_rec_finance", "payback", number=6.67)
        self.assertTrue(r["ok"])

    def test_e_min(self):
        r = check_task_answer("lab_bess_community", "e_min", number=10)
        self.assertTrue(r["ok"])


class TestProgressTasks(unittest.TestCase):
    def test_mark_and_complete(self):
        p = ProgressTracker({})
        lab = "lab_bess_community"
        ids = list_lab_task_ids(lab)
        self.assertFalse(lab_tasks_progress(lab, p.tasks_done_for(lab))["complete"])
        for tid in ids:
            p.mark_task(lab, tid)
        prog = lab_tasks_progress(lab, p.tasks_done_for(lab))
        self.assertTrue(prog["complete"])
        self.assertEqual(prog["done"], prog["total"])
        sm = p.summary()
        self.assertEqual(sm["tasks_completed"], len(ids))


if __name__ == "__main__":
    unittest.main()
