"""
Weather / external API clients for real-time monitoring.

- WeatherAPI.com (preferred when ``WEATHERAPI_KEY`` is set)
- Open-Meteo (free fallback, no key)
"""

from __future__ import annotations

import logging
import os
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Turkistan, Kazakhstan (default EcoPredict site)
DEFAULT_LAT = 43.2973
DEFAULT_LON = 68.2517
DEFAULT_LOCATION = "Turkistan"


class WeatherAPIClient:
    """WeatherAPI.com client."""

    BASE = "https://api.weatherapi.com/v1"

    def __init__(self, api_key: str | None = None):
        self.api_key = (
            api_key
            or os.getenv("WEATHERAPI_KEY")
            or os.getenv("WEATHER_API_KEY")
            or ""
        ).strip()

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def current(self, q: str = DEFAULT_LOCATION) -> dict[str, Any]:
        if not self.configured:
            return {"error": "WEATHERAPI_KEY not configured", "source": "weatherapi"}
        r = requests.get(
            f"{self.BASE}/current.json",
            params={"key": self.api_key, "q": q, "aqi": "no"},
            timeout=20,
        )
        r.raise_for_status()
        data = r.json()
        loc = data.get("location") or {}
        cur = data.get("current") or {}
        return {
            "location": f"{loc.get('name', q)}, {loc.get('country', '')}".strip(", "),
            "temp_c": cur.get("temp_c"),
            "humidity": cur.get("humidity"),
            "wind_kph": cur.get("wind_kph"),
            "condition": (cur.get("condition") or {}).get("text"),
            "cloud": cur.get("cloud"),
            "uv": cur.get("uv"),
            "source": "weatherapi",
            "raw": data,
        }

    def hourly_forecast(self, q: str = DEFAULT_LOCATION, days: int = 2) -> dict[str, Any]:
        if not self.configured:
            return {"forecast": [], "error": "WEATHERAPI_KEY not configured", "source": "weatherapi"}
        r = requests.get(
            f"{self.BASE}/forecast.json",
            params={"key": self.api_key, "q": q, "days": days, "aqi": "no", "alerts": "no"},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        hours: list[dict[str, Any]] = []
        for day in (data.get("forecast") or {}).get("forecastday") or []:
            for h in day.get("hour") or []:
                hours.append(
                    {
                        "time": h.get("time"),
                        "temp_c": h.get("temp_c"),
                        "humidity": h.get("humidity"),
                        "cloud": h.get("cloud"),
                        "wind_kph": h.get("wind_kph"),
                        "precip_mm": h.get("precip_mm"),
                        "condition": (h.get("condition") or {}).get("text"),
                        # Approximate shortwave from UV/cloud for education demos
                        "irradiation": max(
                            0.0,
                            (1.0 - float(h.get("cloud") or 0) / 100.0)
                            * float(h.get("uv") or 0)
                            * 80.0,
                        ),
                    }
                )
        return {"forecast": hours[:48], "source": "weatherapi", "raw": data}


class OpenMeteoClient:
    """Free Open-Meteo forecast (no API key)."""

    BASE = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON):
        self.lat = lat
        self.lon = lon

    def hourly_forecast(self, hours: int = 48) -> dict[str, Any]:
        params = {
            "latitude": self.lat,
            "longitude": self.lon,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    "relative_humidity_2m",
                    "cloud_cover",
                    "wind_speed_10m",
                    "precipitation",
                    "shortwave_radiation",
                ]
            ),
            "forecast_days": 3,
            "timezone": "Asia/Almaty",
        }
        r = requests.get(self.BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        hourly = data.get("hourly") or {}
        times = hourly.get("time") or []
        records: list[dict[str, Any]] = []
        for i, t in enumerate(times[:hours]):
            cloud = (hourly.get("cloud_cover") or [None])[i] if i < len(times) else None
            sw = (hourly.get("shortwave_radiation") or [0])[i] if i < len(times) else 0
            records.append(
                {
                    "time": t,
                    "temp_c": (hourly.get("temperature_2m") or [None])[i],
                    "humidity": (hourly.get("relative_humidity_2m") or [None])[i],
                    "cloud": cloud,
                    "wind_kph": (hourly.get("wind_speed_10m") or [None])[i],
                    "precip_mm": (hourly.get("precipitation") or [None])[i],
                    "irradiation": float(sw or 0) / 1000.0,  # W/m² → approx kW/m² scale used in app
                    "shortwave_w_m2": sw,
                    "condition": None,
                }
            )
        return {
            "forecast": records,
            "source": "open-meteo",
            "location": f"{self.lat},{self.lon}",
            "raw": data,
        }


def fetch_hourly_weather(
    location: str = DEFAULT_LOCATION,
    lat: float = DEFAULT_LAT,
    lon: float = DEFAULT_LON,
    prefer: str = "auto",
) -> dict[str, Any]:
    """
    Fetch 24–48h weather. Prefer WeatherAPI when key is set, else Open-Meteo.

    ``prefer``: auto | weatherapi | open-meteo
    """
    wapi = WeatherAPIClient()
    if prefer in ("auto", "weatherapi") and wapi.configured:
        try:
            return wapi.hourly_forecast(q=location)
        except Exception as e:
            logger.warning("WeatherAPI failed, falling back to Open-Meteo: %s", e)
            if prefer == "weatherapi":
                return {"forecast": [], "error": str(e), "source": "weatherapi"}

    try:
        return OpenMeteoClient(lat=lat, lon=lon).hourly_forecast()
    except Exception as e:
        logger.error("Open-Meteo failed: %s", e, exc_info=True)
        return {"forecast": [], "error": str(e), "source": "open-meteo"}
