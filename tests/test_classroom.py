"""Classes (api/classroom.py): the server records what it grades; the teacher reads it."""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

try:
    import flet as ft
except ImportError:  # pragma: no cover
    ft = None


class ClassroomCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "classroom.sqlite3")
        self.env = mock.patch.dict(os.environ, {"CLASSROOM_DB": self.db})
        self.env.start()
        from api.classroom import router as classroom
        from api.labs import router as labs
        from api.learn import router as learn

        app = FastAPI()
        for r in (classroom, labs, learn):
            app.include_router(r)
        self.c = TestClient(app)

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def new_class(self, name="11-А"):
        return self.c.post("/classes", json={"name": name}).json()


class TestClassroomApi(ClassroomCase):
    def test_results_are_the_servers_grades(self):
        from src.education.labs.lab_tests import correct_answers

        cls = self.new_class()
        self.assertEqual(len(cls["code"]), 6)
        joined = self.c.post(
            f"/classes/{cls['code'].lower()}/join", json={"name": "Айгерім"}
        ).json()
        self.assertEqual(joined["class_name"], "11-А")
        me = {"class_code": joined["code"], "token": joined["token"]}

        wrong = {qid: "0" for qid in correct_answers("lab_pv_physics")}
        self.c.post("/labs/lab_pv_physics/test/grade", json={"answers": wrong, "student": me})
        self.c.post(
            "/labs/lab_pv_physics/test/grade",
            json={"answers": correct_answers("lab_pv_physics"), "student": me},
        )
        self.c.post("/labs/lab_pv_physics/tasks/eta_eff/check", json={"number": 0.5, "student": me})
        self.c.post(
            "/labs/lab_pv_physics/tasks/eta_eff/check", json={"number": 0.184, "student": me}
        )
        quiz = self.c.post(
            "/learn/quizzes/lstm_basics/grade", json={"answers": {"q1": 1}, "student": me}
        ).json()
        self.assertFalse(quiz["passed"])

        self.assertEqual(self.c.get(f"/classes/{cls['code']}/results").status_code, 403)
        res = self.c.get(
            f"/classes/{cls['code']}/results", headers={"X-Teacher-Key": cls["teacher_key"]}
        ).json()
        self.assertEqual(len(res["labs"]), 12)
        st = res["students"][0]
        self.assertEqual(st["name"], "Айгерім")
        lab = st["labs"]["lab_pv_physics"]
        self.assertEqual((lab["test"], lab["passed"], lab["attempts"]), (100.0, True, 2))
        self.assertEqual(lab["tasks"], ["eta_eff"])  # the wrong answer is not recorded
        self.assertEqual((st["labs_passed"], st["tasks_done"], st["test_avg"]), (1, 1, 100.0))
        self.assertEqual(st["quizzes"]["lstm_basics"]["passed"], False)

        # removed by the teacher: gone, and the token records nothing any more
        self.assertEqual(
            self.c.delete(
                f"/classes/{cls['code']}/students/{st['id']}",
                headers={"X-Teacher-Key": cls["teacher_key"]},
            ).status_code,
            200,
        )
        r = self.c.post(
            "/labs/lab_pv_physics/tasks/eta_eff/check", json={"number": 0.184, "student": me}
        )
        self.assertEqual(r.json()["status"], "correct")  # the student still gets the answer
        res = self.c.get(
            f"/classes/{cls['code']}/results", headers={"X-Teacher-Key": cls["teacher_key"]}
        ).json()
        self.assertEqual(res["students"], [])

    def test_teacher_key_is_kept_as_a_hash_only(self):
        cls = self.new_class()
        with sqlite3.connect(self.db) as conn:
            dump = "\n".join(conn.iterdump())
        self.assertNotIn(cls["teacher_key"], dump)
        self.assertEqual(
            self.c.get(
                f"/classes/{cls['code']}/results", headers={"X-Teacher-Key": "x"}
            ).status_code,
            403,
        )

    def test_unknown_class_and_bad_input(self):
        self.assertEqual(self.c.post("/classes/ZZZZZZ/join", json={"name": "a"}).status_code, 404)
        self.assertEqual(self.c.post("/classes", json={"name": ""}).status_code, 422)
        cls = self.new_class()
        self.assertEqual(
            self.c.post(f"/classes/{cls['code']}/join", json={"name": "x" * 200}).status_code, 422
        )
        # a made-up token is ignored; grading still answers
        r = self.c.post(
            "/labs/lab_pv_physics/tasks/eta_eff/check",
            json={"number": 0.184, "student": {"class_code": cls["code"], "token": "nope"}},
        )
        self.assertEqual(r.json()["status"], "correct")
        status = self.c.get("/classes/status").json()
        self.assertTrue(status["ok"] and status["persistent"], status)


PG_URL = os.environ.get("CLASSROOM_TEST_PG")


@unittest.skipUnless(PG_URL, "set CLASSROOM_TEST_PG to a Postgres URL to run these on Postgres")
class TestClassroomOnPostgres(TestClassroomApi):
    """The same routes on Postgres, as on Railway (DATABASE_URL, postgresql://)."""

    test_teacher_key_is_kept_as_a_hash_only = None  # reads the SQLite file

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {"DATABASE_URL": PG_URL})
        self.env.start()
        os.environ.pop("CLASSROOM_DB", None)
        self.tmp = tempfile.TemporaryDirectory()
        from api import classroom

        classroom.meta.drop_all(classroom.engine())
        classroom.meta.create_all(classroom.engine())
        from api.labs import router as labs
        from api.learn import router as learn

        app = FastAPI()
        for r in (classroom.router, labs, learn):
            app.include_router(r)
        self.c = TestClient(app)

    def test_status_reports_postgres(self):
        status = self.c.get("/classes/status").json()
        self.assertEqual(
            (status["backend"], status["persistent"], status["ok"]), ("postgresql", True, True)
        )


class TestDbUrl(unittest.TestCase):
    def test_railway_urls_get_the_installed_driver(self):
        from src.utils.db_url import normalize_db_url

        self.assertEqual(
            normalize_db_url("postgres://u:p@h:5432/db"), "postgresql+psycopg2://u:p@h:5432/db"
        )
        self.assertEqual(normalize_db_url("postgresql://u@h/db"), "postgresql+psycopg2://u@h/db")
        self.assertEqual(
            normalize_db_url("postgresql+psycopg2://u@h/db"), "postgresql+psycopg2://u@h/db"
        )
        self.assertEqual(normalize_db_url("sqlite:///x.db"), "sqlite:///x.db")


class TestMobileStudentIdentity(unittest.TestCase):
    def test_graded_calls_and_the_3d_viewer_carry_the_class(self):
        from mobile import api_client as mod
        from mobile.state import state

        saved = (state.classroom, state.api_base_url)
        try:
            state.api_base_url = "https://api.example"
            state.classroom = None
            self.assertIsNone(mod._student())
            self.assertNotIn("token=", mod.APIClient.lab_viewer_url("/static/lab3d/index.html"))
            state.classroom = {"code": "K7M2QX", "token": "tok", "class_name": "11-А", "name": "A"}
            self.assertEqual(mod._student(), {"class_code": "K7M2QX", "token": "tok"})
            url = mod.APIClient.lab_viewer_url("/static/lab3d/index.html")
            self.assertIn("class=K7M2QX", url)
            self.assertIn("token=tok", url)
            with mock.patch.object(mod, "_http_post_sync", return_value={"percent": 100}) as post:
                asyncio.run(mod.APIClient().lab_grade("lab_pv_physics", {"q1": "1"}))
            self.assertEqual(
                post.call_args.args[1]["student"], {"class_code": "K7M2QX", "token": "tok"}
            )
        finally:
            state.classroom, state.api_base_url = saved


class _Api:
    """Classroom calls answered by the real routes in-process."""

    def __init__(self, client):
        self.c = client

    async def classroom_create(self, name):
        return self.c.post("/classes", json={"name": name}).json()

    async def classroom_join(self, code, name):
        r = self.c.post(f"/classes/{code}/join", json={"name": name})
        return r.json() if r.status_code == 200 else None

    async def classroom_results(self, code, key):
        r = self.c.get(f"/classes/{code}/results", headers={"X-Teacher-Key": key})
        return r.json() if r.status_code == 200 else None

    async def labs_list(self):
        return self.c.get("/labs").json()["labs"]

    @staticmethod
    def cache_note(name):
        return ""


class FakePage:
    def __init__(self):
        self.tasks, self.dialogs, self.services = [], [], []

    def update(self, *args, **kwargs):
        pass

    def run_task(self, fn, *args, **kwargs):
        self.tasks.append(fn(*args, **kwargs))

    def show_dialog(self, d):
        self.dialogs.append(d)

    def pop_dialog(self):
        return self.dialogs.pop() if self.dialogs else None


class FakePrefs:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value):
        self.store[key] = value


@unittest.skipIf(ft is None, "flet is not installed")
class TestClassScreens(ClassroomCase):
    def walk(self):
        try:
            from test_mobile_labs import texts, walk
        except ImportError:
            from tests.test_mobile_labs import texts, walk
        return texts, walk

    def test_teacher_creates_a_student_joins_and_the_teacher_sees_them(self):
        from mobile.state import state
        from mobile.views import labs_view, teacher_view

        texts, walk = self.walk()
        api = _Api(self.c)
        saved = (state.classroom, state.lang)
        state.lang, state.classroom = "kk", None
        teacher_prefs, student_prefs = FakePrefs(), FakePrefs()
        try:
            with (
                mock.patch.object(teacher_view, "api_client", api),
                mock.patch.object(labs_view, "api_client", api),
            ):

                async def scenario():
                    tpage = FakePage()
                    tview = teacher_view.build_teacher_view(tpage, lambda h: None, teacher_prefs)
                    await tview.data()
                    name = next(
                        c
                        for c in walk(tview)
                        if isinstance(c, ft.TextField) and c.label == "Сынып атауы"
                    )
                    name.value = "11-А"
                    create = next(
                        c for c in walk(tview) if isinstance(c, ft.Button) and c.data == "create"
                    )
                    await create.on_click(None)
                    saved_classes = json.loads(teacher_prefs.store["ecopredict.teacher_classes"])
                    code = saved_classes[0]["code"]
                    self.assertTrue(any(code == x for x in texts(tpage.dialogs[-1])))

                    # a student joins from the labs list
                    spage = FakePage()
                    sview = labs_view.build_labs_view(spage, lambda h: None, student_prefs)
                    await sview.data()
                    join = next(
                        c
                        for c in walk(sview)
                        if isinstance(c, ft.TextButton) and c.data == "class_join"
                    )
                    join.on_click(None)
                    dialog = spage.dialogs[-1]
                    fields = {c.label: c for c in walk(dialog) if isinstance(c, ft.TextField)}
                    fields["Сынып коды"].value = code.lower()
                    fields["Аты-жөні"].value = "Айгерім"
                    ok = next(
                        c for c in walk(dialog) if isinstance(c, ft.Button) and c.data == "join"
                    )
                    await ok.on_click(None)
                    self.assertEqual(state.classroom["class_name"], "11-А")
                    self.assertEqual(
                        json.loads(student_prefs.store["ecopredict.classroom"])["code"], code
                    )
                    self.assertTrue(any("Сынып: 11-А · Айгерім" in x for x in texts(sview)))

                    # the teacher opens the class and sees the student
                    tile = next(
                        c
                        for c in walk(tview)
                        if isinstance(c, ft.Container) and c.data == f"class:{code}"
                    )
                    tile.on_click(None)
                    while tpage.tasks:
                        await tpage.tasks.pop(0)
                    self.assertTrue(any(x == "Айгерім" for x in texts(tview)))

                asyncio.run(scenario())
        finally:
            state.classroom, state.lang = saved

    def test_csv_has_a_row_per_student(self):
        from mobile.views.teacher_view import results_csv

        res = {
            "labs": [{"id": "a", "title": {}, "tasks": 2}],
            "students": [
                {"name": "Ә", "labs_passed": 1, "test_avg": 90.0, "tasks_done": 2, "last_seen": 0,
                 "labs": {"a": {"test": 90.0, "tasks": ["t1", "t2"]}}},
            ],
        }  # fmt: skip
        rows = results_csv(res).strip().splitlines()
        self.assertEqual(rows[0].split(",")[:2], ["student", "labs_passed"])
        self.assertTrue(rows[1].startswith("Ә,1,90.0,2,"))
        self.assertTrue(rows[1].endswith(",90.0,2"))


if __name__ == "__main__":
    unittest.main()
