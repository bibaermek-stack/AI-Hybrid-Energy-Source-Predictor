"""HTTP routes of the labs for the mobile app (api/labs.py)."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from api.labs import router
from src.education.labs.lab_tests import correct_answers
from src.education.labs.theory import theory_markdown, to_flet_markdown

STATIC = Path(__file__).resolve().parents[1] / "static"


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=str(STATIC), html=True), name="static")
    return TestClient(app)


class TestLabsApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = _client()

    def test_list(self):
        labs = self.c.get("/labs").json()["labs"]
        self.assertEqual(len(labs), 12)
        self.assertEqual([lab["id"] for lab in labs if lab["has_3d"]], ["lab_inverter_wiring"])

    def test_detail_has_params_theory_and_viewer(self):
        d = self.c.get("/labs/lab_grid_impact").json()
        self.assertTrue(d["params"])
        self.assertTrue(d["theory"]["kk"] and d["theory"]["en"])
        self.assertIsNone(d["viewer_path"])
        d3 = self.c.get("/labs/lab_inverter_wiring").json()
        self.assertEqual(d3["viewer_path"], "/static/lab3d/index.html")
        self.assertEqual(self.c.get(d3["viewer_path"]).status_code, 200)
        self.assertEqual(self.c.get("/static/lab3d/lab3d.js").status_code, 200)

    def test_run_and_errors(self):
        r = self.c.post("/labs/lab_pv_physics/run", json={"params": {"n": 120}})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["params"]["n"], 120)
        self.assertEqual(
            self.c.post("/labs/lab_grid_impact/run", json={"params": {"cable": "x"}}).status_code,
            422,
        )
        self.assertEqual(self.c.get("/labs/nope").status_code, 404)
        self.assertEqual(self.c.post("/labs/nope/run", json={}).status_code, 404)

    def test_test_and_grading(self):
        t = self.c.get("/labs/lab_inverter_wiring/test?lang=kk").json()
        self.assertEqual({q["kind"] for q in t["questions"]}, {"part3d", "choice", "fix"})
        r = self.c.post(
            "/labs/lab_inverter_wiring/test/grade",
            json={"answers": correct_answers("lab_inverter_wiring"), "lang": "kk"},
        ).json()
        self.assertTrue(r["passed"])
        self.assertEqual(r["score"], r["total"])

    def test_practice_task_check(self):
        self.assertEqual(
            self.c.post("/labs/lab_pv_physics/tasks/eta_eff/check", json={"number": 0.184}).json()[
                "status"
            ],
            "correct",
        )
        self.assertEqual(
            self.c.post("/labs/lab_pv_physics/tasks/zzz/check", json={"number": 1}).status_code, 404
        )


class TestTheoryForFlet(unittest.TestCase):
    def test_suffix_after_inline_math_is_spaced(self):
        self.assertEqual(
            to_flet_markdown(r"$25^{\circ}\mathrm{C}$-пен, $x$."),
            r"$25^{\circ}\mathrm{C}$ -пен, $x$.",
        )
        self.assertEqual(to_flet_markdown(r"$\mathrm{\$/kWh}$-ge"), r"$\mathrm{\$/kWh}$ -ge")
        self.assertIn("$$\nP\n$$", to_flet_markdown("\\[\nP\n\\]"))

    def test_every_theory_file_is_flet_ready(self):
        from src.education.labs.lab_registry import list_labs

        for lab in list_labs():
            for lang, text in theory_markdown(lab["theory"]).items():
                with self.subTest(lab=lab["id"], lang=lang):
                    self.assertTrue(text)
                    self.assertNotIn("\\[", text)
                    body = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
                    opened = False
                    for i, ch in enumerate(body):
                        if ch == "$" and (i == 0 or body[i - 1] != "\\"):
                            if opened and i + 1 < len(body):
                                self.assertIn(
                                    body[i + 1], " \t\n.,;:!?)]", body[max(0, i - 30) : i + 3]
                                )
                            opened = not opened
                    self.assertFalse(opened, "unbalanced $")
