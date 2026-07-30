"""
Live data aggregation for dashboard / education demos.

Combines weather client + optional Solarman live status into one snapshot.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from src.monitoring.api_client import (
    DEFAULT_LAT,
    DEFAULT_LON,
    DEFAULT_LOCATION,
    WeatherAPIClient,
    fetch_hourly_weather,
)

logger = logging.getLogger(__name__)


def weather_snapshot(location: str = DEFAULT_LOCATION) -> dict[str, Any]:
    """Current weather + next hours summary."""
    client = WeatherAPIClient()
    current: dict[str, Any] = {}
    if client.configured:
        try:
            current = client.current(q=location)
        except Exception as e:
            logger.warning("current weather failed: %s", e)
            current = {"error": str(e)}

    hourly = fetch_hourly_weather(location=location)
    forecast = hourly.get("forecast") or []
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "location": location,
        "current": current,
        "hourly_count": len(forecast),
        "hourly_source": hourly.get("source"),
        "next_6h": forecast[:6],
        "error": hourly.get("error") or current.get("error"),
    }


def solarman_live_snapshot() -> dict[str, Any]:
    """Best-effort Solarman live dashboard (demo if credentials missing)."""
    try:
        from src.utils.solarman_client import credentials_status, get_live_dashboard

        status = credentials_status()
        data = get_live_dashboard()
        return {
            "credentials": status,
            "dashboard": data,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.warning("Solarman live snapshot failed: %s", e)
        return {
            "credentials": {"configured": False},
            "dashboard": None,
            "error": str(e),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }


def platform_live_bundle(
    location: str = DEFAULT_LOCATION,
    include_solarman: bool = True,
) -> dict[str, Any]:
    """Combined monitoring payload for API or Streamlit."""
    bundle: dict[str, Any] = {
        "weather": weather_snapshot(location),
        "site": {"lat": DEFAULT_LAT, "lon": DEFAULT_LON, "name": location},
    }
    if include_solarman:
        bundle["solarman"] = solarman_live_snapshot()
    return bundle
