"""
The forecast backtest (src/forecasting/backtest.py) on a made-up station
whose truth is known: 25 kW rated, performance ratio 0.8, weather forecasts
that miss the real sunlight by a known amount.
"""

from __future__ import annotations

import math
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.forecasting import backtest as bt  # noqa: E402

RATED = 25.0
PR = 0.8
TODAY = date(2026, 9, 20)
OFFSET = 5.0  # station time = UTC+5


def true_ghi(t_utc: datetime) -> float:
    """Clear-sky-ish bell from 06:00 to 18:00 station time, cloudier on odd days."""
    local = t_utc + timedelta(hours=OFFSET)
    h = local.hour + local.minute / 60.0
    if not 6 <= h <= 18:
        return 0.0
    cloud = 0.5 if local.day % 2 else 1.0
    return 900.0 * math.sin(math.pi * (h - 6) / 12) * cloud


def fake_day(d: date) -> dict:
    """One day of 5-minute Solarman frames (active power in W, unix collectTime)."""
    start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc) - timedelta(hours=OFFSET)
    frames = []
    for i in range(24 * 12):
        t = start + timedelta(minutes=5 * i)
        ghi = true_ghi(t)
        p_kw = RATED * PR * bt.pv_shape(np.array([ghi]), np.array([20.0]))[0]
        frames.append(
            {
                "collectTime": int(t.timestamp()),
                "dataList": [{"key": "APo_t1", "value": str(round(p_kw * 1000)), "unit": "W"}],
            }
        )
    return {"paramDataList": frames}


def fake_weather(start: date, end: date) -> dict:
    """The forecast: right shape, 10% too sunny, cloud cover from the truth."""
    out = {}
    t = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    while t.date() <= end:
        # hourly mean over the hour ending at t
        g = np.mean([true_ghi(t - timedelta(minutes=m)) for m in range(0, 60, 5)])
        local = t + timedelta(hours=OFFSET)
        out[t] = {"ghi": 1.1 * g, "temp": 20.0, "cloud": 60.0 if local.day % 2 else 0.0}
        t += timedelta(hours=1)
    return out


class ConstantModel:
    """Stands in for solar_model.pkl: power proportional to irradiation (Plant 1 scale)."""

    def predict(self, x):
        return x["IRRADIATION"].to_numpy() * 1000.0


def run(**kw):
    with mock.patch.dict("os.environ", {"STATION_UTC_OFFSET_H": str(OFFSET)}):
        return bt.backtest(
            days=kw.pop("days", 10),
            rated_kw=RATED,
            fetch_day=kw.pop("fetch_day", fake_day),
            fetch_weather=fake_weather,
            rf_model=ConstantModel(),
            today=TODAY,
            **kw,
        )


class TestHourlyActual(unittest.TestCase):
    def test_hourly_mean_keyed_by_hour_end_in_utc(self):
        hourly = bt.hourly_actual_kw(fake_day(date(2026, 9, 10)), OFFSET)
        self.assertEqual(len(hourly), 24)
        noon_end = datetime(2026, 9, 10, 8, tzinfo=timezone.utc)  # 13:00 local
        want = np.mean(
            [
                RATED
                * PR
                * bt.pv_shape(
                    np.array([true_ghi(noon_end - timedelta(minutes=m))]), np.array([20.0])
                )[0]
                for m in range(5, 65, 5)  # samples 12:00 ... 12:55 local
            ]
        )
        self.assertAlmostEqual(hourly[noon_end], want, delta=0.01)
        self.assertEqual(hourly[datetime(2026, 9, 9, 20, tzinfo=timezone.utc)], 0.0)  # 01:00 local

    def test_local_time_strings_are_moved_to_utc(self):
        self.assertEqual(
            bt._to_utc("2026-09-10 13:05:00", OFFSET),
            datetime(2026, 9, 10, 8, 5, tzinfo=timezone.utc),
        )
        self.assertEqual(
            bt._to_utc(1789000000000, OFFSET), datetime.fromtimestamp(1789000000, tz=timezone.utc)
        )


class TestBacktest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = run()

    def test_uses_the_days_and_splits_them(self):
        r = self.res
        self.assertEqual(r["days_with_data"], 10)
        self.assertEqual(len(r["fit_days"]), 5)
        self.assertEqual(len(r["test_days"]), 5)
        self.assertEqual(r["test_days"][-1], "2026-09-19")  # yesterday; today is not complete

    def test_physical_model_recovers_the_performance_ratio(self):
        # the forecast is 10% too sunny, so the fitted PR absorbs it: 0.8 / 1.1
        self.assertAlmostEqual(self.res["pv_performance_ratio"], PR / 1.1, delta=0.01)
        self.assertLess(self.res["methods"]["pv"]["mae_pct_of_rated"], 1.0)

    def test_the_apps_50_kwp_request_shows_as_bias(self):
        m = self.res["methods"]
        self.assertGreater(m["app"]["bias_kw"], m["app_rated"]["bias_kw"])
        self.assertEqual(self.res["app_capacity_kwp"], 50.0)

    def test_every_method_is_scored_on_the_same_kind_of_hours(self):
        m = self.res["methods"]
        for name in ("app", "app_rated", "rf_ghi", "pv", "persistence"):
            self.assertIn(name, m)
            self.assertGreater(m[name]["hours"], 20)
            self.assertIsNotNone(m[name]["daily_energy_error_pct"])
        # odd/even days alternate clouds, so yesterday is a poor guess here
        self.assertGreater(m["persistence"]["mae_kw"], m["pv"]["mae_kw"])
        self.assertEqual(self.res["best"], "pv")

    def test_too_few_days_with_data_is_an_error_not_a_score(self):
        def mostly_empty(d):
            return fake_day(d) if d.day % 4 == 0 else {"paramDataList": []}

        with self.assertRaises(RuntimeError) as ctx:
            run(fetch_day=mostly_empty)
        self.assertIn("days have station data", str(ctx.exception))


class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from main import app

        cls.client = TestClient(app)

    def test_backtest_without_credentials_says_why(self):
        with mock.patch(
            "src.forecasting.backtest.cached_backtest",
            side_effect=RuntimeError("No Solarman credentials on the server."),
        ):
            r = self.client.get("/forecast/backtest?days=14")
        self.assertEqual(r.status_code, 503)
        self.assertIn("No Solarman credentials", r.json()["detail"])

    def test_forecast_defaults_to_the_station_rating_and_reports_its_input(self):
        hours = [
            {
                "time": f"2026-09-20T{h:02d}:00",
                "temperature": 20.0,
                "cloud_cover": 0.0,
                "shortwave_radiation": 800.0 if 9 <= h <= 15 else 0.0,
                "radiation_source": "estimated_from_cloud_cover",
                "uv_index": 1.0,
            }
            for h in range(24)
        ]
        with (
            mock.patch(
                "src.utils.solarman_processor.SolarmanProcessor.fetch_turkistan_hourly_forecast",
                return_value={"forecast": hours},
            ),
            mock.patch.dict("os.environ", {"SOLARMAN_RATED_KW": "10"}),
            mock.patch("src.forecasting.backtest.latest", return_value=None),
        ):
            body = self.client.get("/solarman/forecast").json()
            with_50 = self.client.get("/solarman/forecast?dc_capacity_kwp=50").json()
        self.assertEqual(body["dc_capacity_kwp"], 10.0)
        self.assertEqual(body["irradiance_source"], "estimated_from_cloud_cover")
        self.assertIsNone(body["accuracy"])
        noon = [h for h in body["forecasts"] if h["hour"] == 12][0]["predicted_power_kw"]
        noon_50 = [h for h in with_50["forecasts"] if h["hour"] == 12][0]["predicted_power_kw"]
        self.assertAlmostEqual(noon_50, noon * 5, delta=0.01)


if __name__ == "__main__":
    unittest.main()
