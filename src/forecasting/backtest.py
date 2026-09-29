"""
How far off the solar forecast is on the real station.

The model's R² 0.997 (artifacts/model_metrics.json) is measured on the Kaggle
Plant 1 data with irradiance MEASURED at the plant. That is converting
measured sunlight to power, not forecasting: a time-ordered split gives the
same 0.996, and a line through irradiance alone gets 0.98. The forecast the
app shows has no measured irradiance. It takes WeatherAPI's cloud-cover
forecast and turns it into sunlight with a sine curve (SolarmanProcessor.
_estimate_shortwave_wm2). So the only honest number is the station's actual
generation against what the forecast would have said.

For each of the last `days` days this module takes:
- actual: the station's hourly mean AC power from Solarman's historical API;
- weather as it was forecast for that day: the Open-Meteo historical
  forecast API (archived model runs; no key), hourly GHI, temperature, cloud.

It runs these methods on the same hours:
- app: what the phone's forecast screen showed — RandomForest solar_model.pkl
  fed with irradiance from the cloud-cover sine formula, scaled to the 50 kWp
  the app asked for; app_rated: the same scaled to the station's rated power;
- rf_ghi: the same model fed with the forecast GHI instead;
- pv: a physical model, rated kW × GHI/1000 × temperature loss × PR, with the
  performance ratio PR fitted on the earlier half of the days;
- persistence: yesterday's actual power at the same hour (the baseline a
  forecast has to beat).

Scores are on the later half of the days (the one PR never saw), sunlit
hours only: MAE, MAE as % of rated power, bias, RMSE, R², and the error of
each day's total energy.
"""

from __future__ import annotations

import math
import os
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Optional

import numpy as np

LAT, LON = 43.3020, 68.2718  # Turkistan (SolarmanProcessor)
OPEN_METEO_HISTORICAL = "https://historical-forecast-api.open-meteo.com/v1/forecast"
NOCT = 45.0
GAMMA = -0.004  # power temperature coefficient, 1/K
TRAIN_CAPACITY_KWP = 1250.0  # Kaggle Plant 1, the RandomForest's training plant


def station_utc_offset_h() -> float:
    """Kazakhstan has been on UTC+5 everywhere since March 2024."""
    return float(os.environ.get("STATION_UTC_OFFSET_H", "5"))


def rated_kw_default() -> float:
    return float(os.environ.get("SOLARMAN_RATED_KW", "25"))


# ---- actual generation ---------------------------------------------------------
def _to_utc(t: Any, offset_h: float) -> Optional[datetime]:
    """Solarman collectTime: unix s/ms (UTC), or 'YYYY-MM-DD HH:MM[:SS]' in station time."""
    if t is None:
        return None
    if isinstance(t, str) and t.strip().isdigit():
        t = int(t)
    if isinstance(t, (int, float)):
        ts = float(t) / (1000.0 if t > 1e12 else 1.0)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    s = str(t).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            local = datetime.strptime(s[:19] if fmt.endswith("%S") else s[:16], fmt)
            return (local - timedelta(hours=offset_h)).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def hourly_actual_kw(hist: dict, offset_h: float) -> dict[datetime, float]:
    """
    Mean AC power per hour from one day of Solarman frames, keyed by the hour's
    END in UTC (Open-Meteo's GHI at 10:00 is the mean over 09:00-10:00).
    """
    from src.utils.solarman_client import parse_historical_for_charts

    candidates = (
        hist.get("paramDataList") or hist.get("dataList") or hist.get("stationDataItems") or []
    )
    rows = parse_historical_for_charts(hist)
    # parse_historical_for_charts formats times in the server's zone; keep the raw ones
    raw_times = [
        (c.get("collectTime") or c.get("time") or c.get("dateTime") or c.get("date"))
        for c in candidates
        if isinstance(c, dict)
    ]
    by_raw = {str(r.get("timestamp")): r for r in rows}
    sums: dict[datetime, list[float]] = {}
    for raw in raw_times:
        r = by_raw.get(str(raw))
        ts = _to_utc(raw, offset_h)
        if r is None or ts is None:
            continue
        power = float(r.get("ac_power_kw") or 0.0) or float(r.get("dc_power_kw") or 0.0)
        # samples from HH:00 to HH:59 make the hour ending at HH+1, so a day's
        # frames never spill into the day before
        end = ts.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        sums.setdefault(end, []).append(max(0.0, power))
    return {k: float(np.mean(v)) for k, v in sums.items() if v}


# ---- weather as forecast -------------------------------------------------------
def fetch_forecast_weather(start: date, end: date, get: Callable = None) -> dict[datetime, dict]:
    """Archived Open-Meteo forecasts, hourly, keyed by UTC hour."""
    import requests

    get = get or requests.get
    resp = get(
        OPEN_METEO_HISTORICAL,
        params={
            "latitude": LAT,
            "longitude": LON,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": "shortwave_radiation,temperature_2m,cloud_cover",
            "timezone": "UTC",
        },
        timeout=30,
    )
    resp.raise_for_status()
    h = resp.json()["hourly"]
    out = {}
    for i, t in enumerate(h["time"]):
        out[datetime.fromisoformat(t).replace(tzinfo=timezone.utc)] = {
            "ghi": float(h["shortwave_radiation"][i] or 0.0),
            "temp": float(h["temperature_2m"][i] if h["temperature_2m"][i] is not None else 20.0),
            "cloud": float(h["cloud_cover"][i] if h["cloud_cover"][i] is not None else 50.0),
        }
    return out


# ---- forecast methods ----------------------------------------------------------
def sine_irradiance(local_hour: int, cloud_pct: float) -> float:
    """The app's formula (SolarmanProcessor._estimate_shortwave_wm2)."""
    cloud = max(0.0, min(100.0, cloud_pct)) / 100.0
    if 6 <= local_hour <= 18:
        return max(
            0.0, math.sin(math.pi * (local_hour - 6.0) / 12.0) * 950.0 * (1.0 - 0.75 * cloud)
        )
    return 0.0


def rf_power(
    model, ghi_wm2: np.ndarray, temp: np.ndarray, local: list[datetime], rated_kw: float
) -> np.ndarray:
    """The fallback path of /solarman/forecast (6-feature solar_model.pkl)."""
    import pandas as pd

    irr = ghi_wm2 / 1000.0
    x = pd.DataFrame(
        {
            "IRRADIATION": irr,
            "AMBIENT_TEMPERATURE": temp,
            "MODULE_TEMPERATURE": temp + irr * ((NOCT - 20.0) / 800.0),
            "hour": [t.hour for t in local],
            "day": [t.day for t in local],
            "month": [t.month for t in local],
        }
    )
    p = np.maximum(0.0, model.predict(x)) * (rated_kw / TRAIN_CAPACITY_KWP)
    return np.where(ghi_wm2 > 0, p, 0.0)


def pv_shape(ghi_wm2: np.ndarray, temp: np.ndarray) -> np.ndarray:
    """kW per kW rated before the performance ratio."""
    t_cell = temp + ghi_wm2 / 800.0 * (NOCT - 20.0)
    return np.maximum(0.0, ghi_wm2 / 1000.0 * (1.0 + GAMMA * (t_cell - 25.0)))


# ---- scores --------------------------------------------------------------------
def scores(
    actual: np.ndarray, pred: np.ndarray, days: list[date], rated_kw: float
) -> dict[str, Any]:
    err = pred - actual
    ss_tot = float(((actual - actual.mean()) ** 2).sum())
    by_day: dict[date, list[float]] = {}
    for d, a, p in zip(days, actual, pred):
        by_day.setdefault(d, [0.0, 0.0])
        by_day[d][0] += a
        by_day[d][1] += p
    day_err = [abs(p - a) / a * 100 for a, p in by_day.values() if a > 0.05 * rated_kw]
    return {
        "mae_kw": round(float(np.abs(err).mean()), 3),
        "mae_pct_of_rated": round(float(np.abs(err).mean()) / rated_kw * 100, 1),
        "bias_kw": round(float(err.mean()), 3),
        "rmse_kw": round(float(np.sqrt((err**2).mean())), 3),
        "r2": round(1.0 - float((err**2).sum()) / ss_tot, 3) if ss_tot > 0 else None,
        "daily_energy_error_pct": round(float(np.mean(day_err)), 1) if day_err else None,
    }


def backtest(
    days: int = 14,
    rated_kw: Optional[float] = None,
    app_capacity_kwp: float = 50.0,
    fetch_day: Optional[Callable[[date], dict]] = None,
    fetch_weather: Optional[Callable[[date, date], dict]] = None,
    rf_model=None,
    today: Optional[date] = None,
) -> dict[str, Any]:
    """Score the forecast methods on the station's last `days` complete days."""
    offset = station_utc_offset_h()
    rated = float(rated_kw or rated_kw_default())
    today = today or (datetime.now(timezone.utc) + timedelta(hours=offset)).date()
    day_list = [today - timedelta(days=i) for i in range(days, 0, -1)]  # yesterday last

    if fetch_day is None:
        from src.utils.solarman_client import SolarmanClient

        client = SolarmanClient()
        if not client.credentials_configured:
            raise RuntimeError("No Solarman credentials on the server.")

        def fetch_day(d: date) -> dict:
            return client.get_historical(d.isoformat(), d.isoformat(), time_type=1)

    actual: dict[datetime, float] = {}
    days_ok, days_missing, errors = [], [], []
    for d in day_list:
        try:
            got = hourly_actual_kw(fetch_day(d), offset)
        except Exception as err:
            got = {}
            if len(errors) < 3:
                errors.append(f"{d}: {type(err).__name__}: {err}"[:200])
        if sum(1 for v in got.values() if v > 0) >= 3:
            actual.update(got)
            days_ok.append(d)
        else:
            days_missing.append(d.isoformat())
    if len(days_ok) < 4:
        raise RuntimeError(
            f"Only {len(days_ok)} of {days} days have station data "
            f"(missing: {', '.join(days_missing) or '-'}). {' | '.join(errors)}"
        )

    weather = (fetch_weather or fetch_forecast_weather)(
        day_list[0] - timedelta(days=1), day_list[-1] + timedelta(days=1)
    )
    if rf_model is None:
        from pathlib import Path

        import joblib

        rf_model = joblib.load(
            Path(__file__).resolve().parents[2] / "artifacts" / "solar_model.pkl"
        )

    hours = sorted(t for t in actual if t in weather)
    local = [t + timedelta(hours=offset) for t in hours]  # local hour END
    local_start = [t - timedelta(hours=1) for t in local]  # how the forecast labels it
    local_day = [t.date() for t in local_start]
    a = np.array([actual[t] for t in hours])
    ghi = np.array([weather[t]["ghi"] for t in hours])
    temp = np.array([weather[t]["temp"] for t in hours])
    cloud = np.array([weather[t]["cloud"] for t in hours])
    # the app's input: its sine formula of the local hour (WeatherAPI labels hours by start)
    sine = np.array([sine_irradiance(t.hour, c) for t, c in zip(local_start, cloud)])

    pred = {
        # as the phone asks for it: scaled to app_capacity_kwp (it sent 50 kWp)
        "app": rf_power(rf_model, sine, temp, local_start, app_capacity_kwp),
        "app_rated": rf_power(rf_model, sine, temp, local_start, rated),
        "rf_ghi": rf_power(rf_model, ghi, temp, local_start, rated),
    }
    shape = pv_shape(ghi, temp)
    half = days_ok[len(days_ok) // 2]
    fit = np.array([d < half for d in local_day])
    test = ~fit
    denom = float((shape[fit] ** 2).sum()) * rated
    pr = float((a[fit] * shape[fit]).sum()) / denom if denom > 0 else 0.8
    pred["pv"] = rated * pr * shape
    prev = {t: actual.get(t - timedelta(days=1)) for t in hours}
    pred["persistence"] = np.array([prev[t] if prev[t] is not None else np.nan for t in hours])

    sunlit = test & ((ghi > 0) | (a > 0.01 * rated))
    results = {}
    for name, p in pred.items():
        m = sunlit & ~np.isnan(p)
        if m.sum() < 10:
            continue
        results[name] = scores(a[m], p[m], [d for d, keep in zip(local_day, m) if keep], rated)
        results[name]["hours"] = int(m.sum())
    best = min(results, key=lambda k: results[k]["mae_kw"]) if results else None
    return {
        "station_rated_kw": rated,
        "app_capacity_kwp": app_capacity_kwp,
        "days_requested": days,
        "days_with_data": len(days_ok),
        "days_missing": days_missing,
        "fit_days": [d.isoformat() for d in days_ok if d < half],
        "test_days": [d.isoformat() for d in days_ok if d >= half],
        "pv_performance_ratio": round(pr, 3),
        "methods": results,
        "best": best,
        "weather_source": "Open-Meteo historical forecast (archived model runs)",
        "actual_source": "Solarman historical, hourly mean AC power",
    }


_cache: dict[tuple, tuple[float, dict]] = {}
_lock = threading.Lock()  # one backtest at a time: it makes a Solarman call per day


def cached_backtest(
    days: int = 14, rated_kw: Optional[float] = None, ttl_s: float = 6 * 3600
) -> dict:
    key = (days, rated_kw)
    with _lock:
        hit = _cache.get(key)
        if hit and time.time() - hit[0] < ttl_s:
            return hit[1]
        res = backtest(days=days, rated_kw=rated_kw)
        res["computed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _cache[key] = (time.time(), res)
        return res


def latest() -> Optional[dict]:
    """The most recent backtest this process computed, if any (never computes)."""
    if not _cache:
        return None
    return max(_cache.values(), key=lambda v: v[0])[1]
