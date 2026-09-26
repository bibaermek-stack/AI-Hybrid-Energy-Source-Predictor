"""
The mobile labs screen end to end, without a server or a device: the API
client calls are answered by the real API routes in-process, and the tasks the
screen schedules with page.run_task are run by the test.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import unittest
from unittest import mock

try:
    import flet as ft
except ImportError:  # pragma: no cover
    ft = None


class FakePage:
    def __init__(self, platform=None, web=False):
        self.services, self.overlay = [], []
        self.navigation_bar = self.appbar = None
        self.platform, self.web = platform, web
        self.tasks = []

    def update(self, *args, **kwargs):
        pass

    def run_task(self, fn, *args, **kwargs):
        self.tasks.append(fn(*args, **kwargs))


def walk(control):
    """Every control under ``control`` (Flet controls are dataclasses)."""
    seen, stack = set(), [control]
    while stack:
        c = stack.pop()
        if id(c) in seen:
            continue
        seen.add(id(c))
        yield c
        for f in dataclasses.fields(c):
            if f.name.startswith("_") or f.name in ("parent", "page"):
                continue
            v = getattr(c, f.name, None)
            for item in (v if isinstance(v, list) else [v]):
                if ft is not None and isinstance(item, ft.BaseControl):
                    stack.append(item)


def texts(control):
    out = [c.value for c in walk(control) if isinstance(c, ft.Text) and isinstance(c.value, str)]
    content = getattr(control, "content", None)
    return out + ([content] if isinstance(content, str) else [])


class _Api:
    """api_client methods backed by the in-process API."""

    def __init__(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from api.labs import router

        app = FastAPI()
        app.include_router(router)
        self.c = TestClient(app)

    async def labs_list(self):
        return self.c.get("/labs").json()["labs"]

    async def lab_detail(self, lab_id):
        return self.c.get(f"/labs/{lab_id}").json()

    async def lab_run(self, lab_id, params):
        return self.c.post(f"/labs/{lab_id}/run", json={"params": params}).json()

    async def lab_test(self, lab_id):
        return self.c.get(f"/labs/{lab_id}/test?lang=kk").json()

    async def lab_grade(self, lab_id, answers):
        return self.c.post(
            f"/labs/{lab_id}/test/grade", json={"answers": answers, "lang": "kk"}
        ).json()

    @staticmethod
    def lab_viewer_url(path):
        from mobile.api_client import APIClient

        return APIClient.lab_viewer_url(path)


class FakePrefs:
    def __init__(self):
        self.store = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value):
        self.store[key] = value


@unittest.skipIf(ft is None, "flet is not installed")
class TestMobileLabs(unittest.TestCase):
    def setUp(self):
        from mobile.state import state

        self.state = state
        self.saved = (state.lang, state.theme_mode, state.api_base_url)
        state.lang, state.theme_mode, state.api_base_url = "kk", "dark", "https://api.example"
        self.api = _Api()

    def tearDown(self):
        self.state.lang, self.state.theme_mode, self.state.api_base_url = self.saved

    async def _drain(self, page):
        while page.tasks:
            await page.tasks.pop(0)

    def test_list_run_test_and_back(self):
        from mobile.views import labs_view

        page, prefs, back = FakePage(), FakePrefs(), {}
        with mock.patch.object(labs_view, "api_client", self.api):
            view = labs_view.build_labs_view(page, lambda h: back.__setitem__("h", h), prefs)

            async def scenario():
                await view.data()
                cards = [
                    c
                    for c in walk(view)
                    if isinstance(c, ft.Container) and c.data == "lab_grid_impact"
                ]
                self.assertEqual(len(cards), 1)
                cards[0].on_click(None)
                await self._drain(page)
                self.assertIsNotNone(back.get("h"), "a lab page must register Back")

                # Lab tab: run with the defaults
                run_btn = next(
                    c for c in walk(view) if isinstance(c, ft.Button) and "Іске қосу" in texts(c)
                )
                await run_btn.on_click(None)
                self.assertTrue(
                    any(
                        isinstance(c, ft.Container)
                        and any("Тәуліктегі ең жоғары кернеу" in t for t in texts(c))
                        for c in walk(view)
                    )
                )

                # Test tab: answer everything right
                await self._drain(page)
                seg = next(c for c in walk(view) if isinstance(c, ft.SegmentedButton))
                seg.selected = ["test"]
                seg.on_change(mock.Mock(control=seg))
                from src.education.labs.lab_tests import correct_answers

                right = correct_answers("lab_grid_impact")
                fields = self._fields(view)
                self.assertEqual(set(fields), set(right))
                for qid, c in fields.items():
                    c.value = (
                        str(right[qid]) if isinstance(c, ft.RadioGroup) else f"{right[qid]:.4f}"
                    )
                submit = next(
                    c
                    for c in walk(view)
                    if isinstance(c, ft.Button) and "Тестті тапсыру" in texts(c)
                )
                await submit.on_click(None)
                self.assertTrue(any("Өтті" in t for t in texts(view)))
                self.assertEqual(
                    json.loads(prefs.store["ecopredict.labs_passed"]), ["lab_grid_impact"]
                )

                # Back returns to the list, which now marks the lab passed
                self.assertTrue(back["h"]())
                self.assertIsNone(back.get("h"))
                self.assertIn("✅ Өтті", texts(view))

            asyncio.run(scenario())

    @staticmethod
    def _fields(view):
        """question id -> its answer control (the screen tags them with .data)."""
        return {
            c.data: c for c in walk(view) if isinstance(c, (ft.RadioGroup, ft.TextField)) and c.data
        }

    def test_3d_lab_uses_a_webview_on_android_and_records_the_test(self):
        from mobile.views import labs_view

        page, prefs, back = FakePage(platform=ft.PagePlatform.ANDROID), FakePrefs(), {}
        with mock.patch.object(labs_view, "api_client", self.api):
            view = labs_view.build_labs_view(page, lambda h: back.__setitem__("h", h), prefs)

            async def scenario():
                await view.data()
                card = next(
                    c
                    for c in walk(view)
                    if isinstance(c, ft.Container) and c.data == "lab_inverter_wiring"
                )
                card.on_click(None)
                await self._drain(page)
                import flet_webview as fwv

                web = [c for c in walk(view) if isinstance(c, fwv.WebView)]
                self.assertEqual(len(web), 1)
                self.assertTrue(
                    web[0].url.startswith("https://api.example/static/lab3d/index.html?lang=kk")
                )
                event = mock.Mock(
                    message='LAB3D {"type":"test_result","score":7,"total":7,"percent":100,"passed":true}'
                )
                await web[0].on_console_message(event)
                self.assertEqual(
                    json.loads(prefs.store["ecopredict.labs_passed"]), ["lab_inverter_wiring"]
                )

            asyncio.run(scenario())

    def test_3d_lab_falls_back_to_a_link_on_the_web_preview(self):
        from mobile.views import labs_view

        self.assertFalse(
            labs_view.webview_supported(FakePage(platform=ft.PagePlatform.ANDROID, web=True))
        )
        self.assertFalse(labs_view.webview_supported(FakePage(platform=ft.PagePlatform.LINUX)))
        self.assertTrue(labs_view.webview_supported(FakePage(platform=ft.PagePlatform.IOS)))


@unittest.skipIf(ft is None, "flet is not installed")
class TestLineChart(unittest.TestCase):
    def test_shapes_and_ticks(self):
        from mobile.components.line_chart import _shapes, _tick

        chart = {
            "x": [0, 1, 2, 3],
            "series": [{"name": {"en": "a", "kk": "a"}, "values": [1.0, 1.05, None, 1.02]}],
            "limits": [{"value": 1.1, "label": {"en": "max", "kk": "max"}}],
        }
        self.assertTrue(_shapes(chart, 320, 180))
        self.assertEqual(_shapes({"x": [0], "series": []}, 320, 180), [])
        self.assertEqual(_tick(1.037, 0.075), "1.04")
        self.assertEqual(_tick(250.0, 250.0), "250")

    def test_viewer_url_encodes_the_api_base(self):
        from mobile.api_client import APIClient
        from mobile.state import state

        saved = state.api_base_url
        try:
            state.api_base_url = "https://x.example"
            url = APIClient.lab_viewer_url("/static/lab3d/index.html")
            self.assertIn("api=https%3A%2F%2Fx.example", url)
        finally:
            state.api_base_url = saved


if __name__ == "__main__":
    unittest.main()
