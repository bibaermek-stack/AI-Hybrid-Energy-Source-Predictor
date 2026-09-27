"""Station alerts in the app (mobile/solar_alerts.py) and the Home alert card."""

from __future__ import annotations

import asyncio
import calendar
import time
import unittest

try:
    import flet as ft
except ImportError:  # pragma: no cover
    ft = None

# 12:00 and 23:00 in Turkistan (UTC+5)
NOON = calendar.timegm((2026, 9, 27, 7, 0, 0))
NIGHT = calendar.timegm((2026, 9, 27, 18, 0, 0))


def live(status=1, fault=0, collected=None, ac_kw=6.5, source="solarman_api"):
    return {
        "source": source,
        "basic": {"status": status},
        "raw_flat": {
            "deviceStatus": status,
            "faultCode": fault,
            "collectionTime": NOON - 300 if collected is None else collected,
        },
        "generation": {"ac_active_power_kw": ac_kw},
    }


class TestEvaluate(unittest.TestCase):
    def kinds(self, reply, now=NOON):
        from mobile.solar_alerts import evaluate

        return [a["kind"] for a in evaluate("SN1", reply, now=now)]

    def test_healthy_station_and_sample_data_raise_nothing(self):
        self.assertEqual(self.kinds(live()), [])
        self.assertEqual(self.kinds(live(status=0, source="demo")), [])
        self.assertEqual(self.kinds(None), [])

    def test_offline_fault_and_stale(self):
        self.assertEqual(self.kinds(live(status=0)), ["offline"])  # no "no output" on top
        self.assertEqual(self.kinds(live(fault=17)), ["fault"])
        self.assertEqual(self.kinds(live(collected=NOON - 4 * 3600)), ["stale"])

    def test_no_output_only_in_daylight(self):
        self.assertEqual(self.kinds(live(ac_kw=0.0)), ["no_power"])
        self.assertEqual(self.kinds(live(ac_kw=0.0, collected=NIGHT - 60), now=NIGHT), [])

    def test_described_in_kazakh(self):
        from mobile.solar_alerts import describe, evaluate
        from mobile.state import state

        saved, state.lang = state.lang, "kk"
        try:
            lines = [describe(a, state.text) for a in evaluate("SN1", live(fault=17), now=NOON)]
        finally:
            state.lang = saved
        self.assertEqual(lines, ["Инвертор SN1: ақау коды 17"])


class _Client:
    def __init__(self, replies, cached=()):
        self.replies, self.cached, self.last = replies, set(cached), None

    async def get_solarman_live(self, sn):
        self.last = sn
        return self.replies.get(sn)

    def cache_note(self, name):
        return "saved" if self.last in self.cached else ""


class TestCheck(unittest.TestCase):
    def test_saved_copies_raise_no_alerts(self):
        from mobile import solar_alerts

        now = time.time()
        client = _Client(
            {"A": live(status=0, collected=now), "B": live(status=0, collected=now)}, cached={"B"}
        )
        alerts = asyncio.run(solar_alerts.check(client, ["A", "B"]))
        self.assertEqual([(a["sn"], a["kind"]) for a in alerts], [("A", "offline")])


class FakePage:
    def update(self, *args, **kwargs):
        pass

    def run_task(self, fn, *args, **kwargs):
        pass


@unittest.skipIf(ft is None, "flet is not installed")
class TestHomeCard(unittest.TestCase):
    def test_home_shows_and_hides_the_alert_card(self):
        from mobile.state import state
        from mobile.views.overview_view import build_overview_view

        went = []
        view = build_overview_view(FakePage(), went.append)
        card = next(c for c in view.controls if getattr(c, "data", None) == "station_alerts")
        self.assertFalse(card.visible)
        try:
            state.set_solar_alerts([{"sn": "SN1", "kind": "offline", "level": "error"}])
            self.assertTrue(card.visible)
            state.set_solar_alerts([])
            self.assertFalse(card.visible)
        finally:
            state.alert_listeners.pop("overview", None)
            state.solar_alerts = []


if __name__ == "__main__":
    unittest.main()
