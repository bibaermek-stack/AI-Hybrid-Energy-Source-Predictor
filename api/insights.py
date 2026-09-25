"""
Read-only endpoints behind the mobile Training, Sustainability and Labs screens.

Those screens used to print constants (R² 98.4%, 412.8 t CO₂, 18 650 trees)
and made-up formulas. These routes serve the same metrics file, sustainability
helpers and microgrid simulator the Streamlit dashboard already uses, so the
phone shows the project's real numbers.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


def _importances(model: Any) -> list[dict[str, Any]]:
    """Feature importances of a fitted tree model, largest first."""
    values = getattr(model, "feature_importances_", None)
    if values is None:
        return []
    names = getattr(model, "feature_names_in_", None)
    if names is None:
        names = [f"feature_{i}" for i in range(len(values))]
    pairs = sorted(
        ((str(name), float(value)) for name, value in zip(names, values)),
        key=lambda pair: pair[1],
        reverse=True,
    )
    return [{"feature": name, "importance": round(value, 4)} for name, value in pairs]


@router.get("/metrics")
def model_metrics() -> dict[str, Any]:
    """
    Paper-locked model metrics (artifacts/model_metrics.json) plus the feature
    importances of the solar and wind models /predict actually serves.
    """
    # Imported lazily: api.routes includes this router at import time.
    from api import routes

    path = routes.ARTIFACT_PATH / "model_metrics.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail=f"{path.name} not found on the server")
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"{path.name} is not valid JSON: {e}")

    yolo = data.get("yolo11n_fault_detection") or {}
    return {
        "source": "artifacts/model_metrics.json",
        "solar_forecast": data.get("solar_forecast") or {},
        "yolo11n": {
            "best": yolo.get("best") or {},
            "test": yolo.get("test_set_all") or {},
            "classes": yolo.get("classes") or [],
        },
        "production_models": data.get("production_models") or {},
        "feature_importance": {
            "solar": _importances(routes.solar_model),
            "wind": _importances(routes.wind_model),
        },
    }


class ImpactRequest(BaseModel):
    renewable_kwh: float = Field(..., ge=0, le=1e10, description="Renewable energy over the period")
    grid_import_kwh: float = Field(0.0, ge=0, le=1e10, description="Grid energy still imported")
    grid_factor_kg_per_kwh: float = Field(0.45, gt=0, le=2.0, description="Grid kg CO₂ per kWh")
    lang: Literal["kk", "en"] = "kk"


@router.post("/sustainability/impact")
def sustainability_impact(request: ImpactRequest) -> dict[str, Any]:
    """CO₂ avoided and its equivalents, via src.sustainability.analyze_impact."""
    from src.sustainability import analyze_impact

    return analyze_impact(
        request.renewable_kwh,
        request.grid_import_kwh,
        request.grid_factor_kg_per_kwh,
        lang=request.lang,
    )


class MicrogridDayRequest(BaseModel):
    num_panels: int = Field(100, ge=1, le=2000)
    battery_kwh: float = Field(50.0, ge=1.0, le=5000.0)
    load_kw: float = Field(15.0, ge=0.0, le=5000.0)
    inverter_kw: float = Field(40.0, gt=0.0, le=5000.0)
    weather: Literal["sample", "synthetic", "open-meteo"] = "sample"


def _lab_weather(source: str):
    from src.simulation.adapters.weather_profile import (
        load_weather_profile,
        synthetic_day_profile,
    )
    from src.utils.config import SITE_LAT, SITE_LON

    if source == "synthetic":
        return synthetic_day_profile()
    if source == "open-meteo":
        # Falls back to the sample CSV when Open-Meteo is unreachable; the
        # frame's attrs record which profile was really used.
        return load_weather_profile(lat=SITE_LAT, lon=SITE_LON, prefer="open-meteo")
    return load_weather_profile(prefer="sample")


@router.post("/labs/microgrid-day")
def microgrid_day(request: MicrogridDayRequest) -> dict[str, Any]:
    """
    24 h PV + battery + grid simulation — the dashboard's microgrid dispatch
    lab (src.simulation.microgrid.engine) for the mobile Labs screen.
    """
    from src.simulation.microgrid.engine import run_day_simulation, summarize_day

    weather = _lab_weather(request.weather)
    try:
        df = run_day_simulation(
            weather,
            num_panels=request.num_panels,
            battery_kwh=request.battery_kwh,
            load_kw=request.load_kw,
            inverter_kw=request.inverter_kw,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    hours = [
        {
            "hour": i,
            "pv_kw": round(float(row.pv_kw), 3),
            "load_kw": round(float(row.load_kw), 3),
            "soc": round(float(row.soc), 4),
            "grid_import_kw": round(float(row.grid_import_kw), 3),
            "grid_export_kw": round(float(row.grid_export_kw), 3),
        }
        for i, row in enumerate(df.itertuples(index=False))
    ]
    summary = {key: round(float(value), 3) for key, value in summarize_day(df).items()}
    return {
        "summary": summary,
        "hours": hours,
        "weather_source": weather.attrs.get("source", request.weather),
        "inputs": request.model_dump(),
    }
