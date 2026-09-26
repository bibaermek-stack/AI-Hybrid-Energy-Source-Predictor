"""Final tests of the labs (src/education/labs/lab_tests.py)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.education.inverter_lab import CONTROLS
from src.education.labs.lab_registry import LAB_IDS
from src.education.labs.lab_tests import (
    PASS_PERCENT,
    TESTS,
    correct_answers,
    grade_test,
    public_test,
)
from src.education.labs.runner import metric_value, run_lab

ASSEMBLY = Path(__file__).resolve().parents[1] / "static" / "lab3d" / "assembly.json"


class TestBank(unittest.TestCase):
    def test_every_lab_has_a_test_in_both_languages(self):
        for lab_id in LAB_IDS:
            with self.subTest(lab=lab_id):
                self.assertGreaterEqual(len(TESTS[lab_id]), 5)
                for lang in ("kk", "en"):
                    t = public_test(lab_id, lang)
                    for q in t["questions"]:
                        self.assertTrue(q["prompt"].strip())
                        for ch in q.get("choices", []):
                            self.assertTrue(ch.strip())

    def test_questions_do_not_leak_answers(self):
        for lab_id in LAB_IDS:
            blob = json.dumps(public_test(lab_id, "en"))
            for key in ('"correct"', '"answer"', '"part"', '"faults"', '"explain"'):
                self.assertNotIn(key, blob, f"{lab_id} exposes {key}")

    def test_choice_order_is_shuffled_but_stable(self):
        a = public_test("lab_pv_physics", "en")
        b = public_test("lab_pv_physics", "en")
        self.assertEqual(a, b)
        firsts = [
            correct_answers(lid)[q["id"]]
            for lid in LAB_IDS
            for q in TESTS[lid]
            if q["kind"] == "choice"
        ]
        self.assertGreater(len(set(firsts)), 1, "the correct option must not always be first")

    def test_3d_questions_name_real_parts_and_controls(self):
        parts = set(json.loads(ASSEMBLY.read_text(encoding="utf-8"))["parts"])
        for q in TESTS["lab_inverter_wiring"]:
            if q["kind"] == "part3d":
                self.assertIn(q["part"], parts)
            if q["kind"] == "fix":
                self.assertTrue(set(q["faults"]) <= set(CONTROLS))


def _correct(lab_id: str, answers: dict, qid: str) -> bool:
    return {d["id"]: d["correct"] for d in grade_test(lab_id, answers)["details"]}[qid]


class TestGrading(unittest.TestCase):
    def test_full_marks_and_zero(self):
        for lab_id in LAB_IDS:
            with self.subTest(lab=lab_id):
                full = grade_test(lab_id, correct_answers(lab_id))
                self.assertEqual(full["score"], full["total"])
                self.assertTrue(full["passed"])
                empty = grade_test(lab_id, {})
                self.assertEqual(empty["score"], 0)
                self.assertFalse(empty["passed"])

    def test_run_questions_expect_what_the_lab_shows(self):
        for lab_id in LAB_IDS:
            for q in TESTS[lab_id]:
                if q["kind"] != "run":
                    continue
                res = run_lab(lab_id, q["params"])
                value = metric_value(res, q["metric"])
                digits = next(m["digits"] for m in res["metrics"] if m["key"] == q["metric"])
                with self.subTest(lab=lab_id, q=q["id"]):
                    self.assertTrue(_correct(lab_id, {q["id"]: value}, q["id"]))
                    # the value as the lab displays it (rounded) is accepted too
                    self.assertTrue(_correct(lab_id, {q["id"]: f"{value:.{digits}f}"}, q["id"]))

    def test_numbers_accept_a_comma(self):
        self.assertTrue(_correct("lab_grid_impact", {"q2": "1,05"}, "q2"))

    def test_wrong_3d_answers(self):
        sheet = correct_answers("lab_inverter_wiring")
        sheet["q1"] = "inverter"
        sheet["q7"] = {**sheet["q7"], "pe": "open"}
        r = grade_test("lab_inverter_wiring", sheet)
        wrong = [d["id"] for d in r["details"] if not d["correct"]]
        self.assertEqual(wrong, ["q1", "q7"])
        self.assertEqual(r["pass_percent"], PASS_PERCENT)
