"""The Learn lessons and quizzes: the API (api/learn.py) and the app screen."""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.learn import router
from src.education.lessons import LESSON_IDS
from src.education.quiz import QUIZ_BANK

try:
    import flet as ft
except ImportError:  # pragma: no cover
    ft = None


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestLearnApi(unittest.TestCase):
    def setUp(self):
        self.c = _client()

    def test_every_lesson_comes_as_markdown_with_its_quiz(self):
        cards = self.c.get("/learn/lessons?lang=kk").json()["lessons"]
        self.assertEqual([c["id"] for c in cards], list(LESSON_IDS))
        for lesson_id in LESSON_IDS:
            with self.subTest(lesson=lesson_id):
                d = self.c.get(f"/learn/lessons/{lesson_id}?lang=kk").json()
                self.assertTrue(d["markdown"].startswith("### "))
                self.assertIn(d["quiz"], QUIZ_BANK)
                self.assertTrue(d["key_takeaways"])
                for lab in d["related_labs"]:
                    self.assertTrue(lab["title"]["kk"])
        self.assertEqual(self.c.get("/learn/lessons/nope").status_code, 404)

    def test_formulas_become_display_math(self):
        md = self.c.get("/learn/lessons/hybrid_optimization?lang=en").json()["markdown"]
        self.assertIn("$$\nP_{pv}+P_{wind}", md)
        self.assertIn("1. ", md)  # the student tasks are numbered

    def test_quiz_hides_answers_and_is_graded_here(self):
        q = self.c.get("/learn/quizzes/lstm_basics?lang=kk").json()
        self.assertTrue(q["questions"])
        for question in q["questions"]:
            self.assertEqual(set(question), {"id", "prompt", "choices"})
        right = {x["id"]: x["correct_index"] for x in QUIZ_BANK["lstm_basics"]["questions"]}
        r = self.c.post(
            "/learn/quizzes/lstm_basics/grade", json={"answers": right, "lang": "kk"}
        ).json()
        self.assertEqual(r["percent"], 100.0)
        self.assertTrue(all(d["explain"] for d in r["details"]))
        self.assertEqual(self.c.get("/learn/quizzes/nope").status_code, 404)
        self.assertEqual(self.c.post("/learn/quizzes/nope/grade", json={}).status_code, 404)


class _Api:
    def __init__(self):
        self.c = _client()

    async def learn_lessons(self):
        return self.c.get("/learn/lessons?lang=kk").json()["lessons"]

    async def learn_lesson(self, lesson_id):
        return self.c.get(f"/learn/lessons/{lesson_id}?lang=kk").json()

    async def learn_quiz(self, quiz_id):
        return self.c.get(f"/learn/quizzes/{quiz_id}?lang=kk").json()

    async def learn_grade(self, quiz_id, answers):
        return self.c.post(
            f"/learn/quizzes/{quiz_id}/grade", json={"answers": answers, "lang": "kk"}
        ).json()

    @staticmethod
    def cache_note(name):
        return ""


class FakePrefs:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value):
        self.store[key] = value


class FakePage:
    def __init__(self):
        self.tasks = []

    def update(self, *args, **kwargs):
        pass

    def run_task(self, fn, *args, **kwargs):
        self.tasks.append(fn(*args, **kwargs))


@unittest.skipIf(ft is None, "flet is not installed")
class TestLearnScreen(unittest.TestCase):
    def setUp(self):
        from mobile.state import state

        self.state = state
        self.saved = state.lang
        state.lang = "kk"

    def tearDown(self):
        self.state.lang = self.saved

    def test_lesson_quiz_related_lab_and_back(self):
        from mobile.views import learn_view
        try:
            from test_mobile_labs import texts, walk
        except ImportError:  # run as tests.test_learn
            from tests.test_mobile_labs import texts, walk

        page, prefs, back, went = FakePage(), FakePrefs(), {}, []
        with mock.patch.object(learn_view, "api_client", _Api()):
            view = learn_view.build_learn_view(
                page, went.append, lambda h: back.__setitem__("h", h), prefs
            )

            async def drain():
                while page.tasks:
                    await page.tasks.pop(0)

            async def scenario():
                await view.data()
                card = next(
                    c
                    for c in walk(view)
                    if isinstance(c, ft.Container) and c.data == "lesson:hybrid_optimization"
                )
                card.on_click(None)
                await drain()
                self.assertIsNotNone(back.get("h"))
                self.assertTrue(any(isinstance(c, ft.Markdown) for c in walk(view)))

                lab_btn = next(
                    c
                    for c in walk(view)
                    if isinstance(c, ft.OutlinedButton) and c.data == "lab:lab_microgrid_dispatch"
                )
                lab_btn.on_click(None)
                self.assertEqual(went, ["labs:lab_microgrid_dispatch"])

                quiz_btn = next(
                    c for c in walk(view) if isinstance(c, ft.Button) and c.data == "quiz"
                )
                quiz_btn.on_click(None)
                await drain()
                groups = {c.data: c for c in walk(view) if isinstance(c, ft.RadioGroup)}
                right = {
                    q["id"]: q["correct_index"]
                    for q in QUIZ_BANK["optimization_basics"]["questions"]
                }
                self.assertEqual(set(groups), set(right))
                submit = next(
                    c for c in walk(view) if isinstance(c, ft.Button) and c.data == "quiz_submit"
                )
                await submit.on_click(None)
                self.assertTrue(any("жауап беріңіз" in t for t in texts(view)))  # none picked yet
                for qid, g in groups.items():
                    g.value = str(right[qid])
                await submit.on_click(None)
                self.assertTrue(any("Өтті" in t for t in texts(view)))
                self.assertEqual(
                    json.loads(prefs.store["ecopredict.learn_best"]), {"optimization_basics": 100.0}
                )

                self.assertTrue(back["h"]())  # Back returns to the lessons
                self.assertTrue(any("Ең жоғары: 100%" in t for t in texts(view)))

            asyncio.run(scenario())


if __name__ == "__main__":
    unittest.main()
