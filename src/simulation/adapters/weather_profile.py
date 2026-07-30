"""Weather profiles for microgrid labs (sample CSV + Open-Meteo)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
SAMPLE_CSV = ROOT / "data" / "sample" / "historical_weather.csv"


def synthetic_day_profile(seed: int = 42) -> pd.DataFrame:
    """24h synthetic irradiance bell curve (°C / W/m²)."""
    rng = np.random.default_rng(seed)
    hours = pd.date_range("2024-06-15", periods=24, freq="h")
    t = np.arange(24)
    irradiance = 1000.0 * np.exp(-((t - 12) ** 2) / 18.0)
    irradiance = np.maximum(0.0, irradiance + rng.normal(0, 15, size=24))
    temp = 18.0 + 10.0 * np.exp(-((t - 14) ** 2) / 20.0)
    return pd.DataFrame(
        {
            "time": hours,
            "temperature_c": temp,
            "irradiance_w_m2": irradiance,
        }
    )


def load_sample_csv(path: Path | None = None) -> pd.DataFrame:
    path = path or SAMPLE_CSV
    if not path.is_file():
        return synthetic_day_profile()
    df = pd.read_csv(path)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    # Expand sparse sample to 24h if needed
    if len(df) < 12:
        return synthetic_day_profile()
    return df


def load_weather_profile(
    *,
    lat: float | None = None,
    lon: float | None = None,
    prefer: str = "auto",
) -> pd.DataFrame:
    """
    Load hourly weather with columns irradiance_w_m2, temperature_c, time.

    prefer: auto | sample | open-meteo | synthetic
    """
    prefer = (prefer or "auto").lower()
    if prefer == "synthetic":
        return synthetic_day_profile()
    if prefer == "sample":
        return load_sample_csv()

    if prefer in ("auto", "open-meteo") and lat is not None and lon is not None:
        try:
            from src.monitoring.api_client import OpenMeteoClient

            raw = OpenMeteoClient(lat=float(lat), lon=float(lon)).hourly_forecast(hours=24)
            hours = raw.get("forecast") or []
            if hours:
                rows = []
                for h in hours[:24]:
                    sw = h.get("shortwave_w_m2")
                    if sw is None:
                        # Open-Meteo client stores irradiation as approx scale
                        irr = float(h.get("irradiation") or 0) * 1000.0
                    else:
                        irr = float(sw or 0)
                    rows.append(
                        {
                            "time": h.get("time"),
                            "temperature_c": float(h.get("temp_c") or 15),
                            "irradiance_w_m2": max(0.0, irr),
                        }
                    )
                df = pd.DataFrame(rows)
                if not df.empty:
                    return df
        except Exception:
            pass

    return load_sample_csv()
