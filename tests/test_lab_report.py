"""The printable lab report (src/education/labs/report.py)."""

from __future__ import annotations

import re
import unittest
from datetime import datetime

from src.education.labs.lab_registry import LAB_IDS
from src.education.labs.lab_tests import correct_answers, grade_test
from src.education.labs.report import (
    build_report_html,
    latex_to_html,
    report_filename,
)
from src.education.labs.runner import run_lab

LAB_3D = "lab_inverter_wiring"


class TestLabReport(unittest.TestCase):
    def test_every_lab_reports_its_run_and_test(self):
        for lab_id in LAB_IDS:
            with self.subTest(lab=lab_id):
                run = None if lab_id == LAB_3D else run_lab(lab_id, {})
                test = grade_test(lab_id, correct_answers(lab_id), "kk")
                page = build_report_html(
                    lab_id,
                    "kk",
                    student="Айгерім",
                    group="ЭЭ-21",
                    run_result=run,
                    test_result=test,
                    generated_at=datetime(2026, 9, 27, 10, 0),
                )
                self.assertIn("Айгерім", page)
                self.assertIn("27.09.2026 10:00", page)
                self.assertIn("Ең жоғары нәтиже: 100 %", page)
                # formulas are HTML now, not LaTeX
                self.assertNotIn("\\mathrm", page)
                self.assertNotRegex(page, r"\$[^$<]*\\[a-zA-Z]")
                if run is not None:
                    self.assertEqual(page.count("<svg"), len(run["charts"]))
                    for m in run["metrics"]:
                        self.assertIn(m["label"]["kk"], page)

    def test_student_text_is_escaped(self):
        page = build_report_html("lab_pv_physics", "en", student="<script>alert(1)</script>")
        self.assertNotIn("<script>alert", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_no_run_and_no_test_are_said_so(self):
        page = build_report_html("lab_bess_soc", "en")
        self.assertIn("The lab was not run in this session.", page)
        self.assertIn("The test was not taken yet.", page)
        self.assertEqual(
            re.findall(r"<h2>(\d)\. ", page), ["1", "2", "3", "4", "5"], "numbered sections"
        )

    def test_best_score_and_solved_tasks(self):
        page = build_report_html(
            "lab_pv_physics", "en", best_test_percent=60, tasks_done=["eta_eff", "nope"]
        )
        self.assertIn("Best score: 60 %", page)
        self.assertIn("Not passed yet.", page)
        self.assertIn("Solved: 1 of 3", page)

    def test_3d_lab_lists_the_fixed_faults(self):
        page = build_report_html(
            LAB_3D,
            "en",
            tasks_done=["scenario_reversed_dc", "scenario_pe_open"],
            last_3d_check={"score": 6, "total": 6, "ok": True},
        )
        self.assertIn("Work in the 3D model", page)
        self.assertIn("Fault A — reversed DC polarity", page)
        self.assertIn("Last system check: 6 of 6 items right", page)
        self.assertNotIn("Parameters of the run", page)

    def test_latex_to_html(self):
        self.assertEqual(
            latex_to_html(r"$\eta_0=0.20$, $T=45^\circ\mathrm{C}$"),
            "<i>η<sub>0</sub>=0.20</i>, <i>T=45°C</i>",
        )
        self.assertEqual(
            latex_to_html(r"price 5 \$ and $x^{2}$"), "price 5 $ and <i>x<sup>2</sup></i>"
        )
        self.assertEqual(latex_to_html("a < b"), "a &lt; b")

    def test_filename_is_ascii(self):
        self.assertEqual(
            report_filename("lab_bess_soc", "Әлия Өмірзақ / ЭЭ-21"),
            "lab03_report_Aliya_Omirzaq_EE-21.html",
        )
        self.assertEqual(report_filename("lab_pv_physics", "  "), "lab01_report.html")
        self.assertTrue(report_filename("lab_pv_physics", "Ұлжан").isascii())


if __name__ == "__main__":
    unittest.main()
