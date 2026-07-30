"""
Hands-on educational exercises (logic + synthetic data).

Streamlit rendering lives in dashboard/views/learn.py — these helpers
return DataFrames / metrics for plots and teaching feedback.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.education.explainable_ai import predict_solar
from src.optimization.hybrid_optimizer import BatteryParams, HybridEnergyOptimizer


def forecast_sensitivity_curve(
    hour: int = 12,
    ambient: float = 30.0,
    module: float = 45.0,
    day: int = 15,
    month: int = 6,
    irr_min: float = 50.0,
    irr_max: float = 1000.0,
    steps: int = 20,
) -> pd.DataFrame:
    """Predicted power vs irradiation at fixed hour/temps (teaching curve)."""
    xs = np.linspace(irr_min, irr_max, steps)
    ys = [
        predict_solar(float(g), ambient, module, hour, day, month) for g in xs
    ]
    return pd.DataFrame({"irradiation_wm2": xs, "predicted_kw": ys})


def forecast_what_if(
    irradiation: float,
    ambient_temp: float,
    module_temp: float,
    hour: int,
    day: int = 15,
    month: int = 6,
) -> dict[str, Any]:
    """Single scenario prediction + short teaching note keys."""
    y = predict_solar(irradiation, ambient_temp, module_temp, hour, day, month)
    note_en = "Higher irradiance → higher power; very hot modules slightly hurt efficiency."
    note_kk = "Сәуле жоғары → қуат жоғары; өте ыстық панель тиімділікті сәл төмендетеді."
    return {
        "predicted_kw": y,
        "inputs": {
            "IRRADIATION": irradiation,
            "AMBIENT_TEMPERATURE": ambient_temp,
            "MODULE_TEMPERATURE": module_temp,
            "hour": hour,
            "day": day,
            "month": month,
        },
        "note_en": note_en,
        "note_kk": note_kk,
    }


def battery_scenario(
    solar: np.ndarray | list[float],
    wind: np.ndarray | list[float],
    load: float | np.ndarray | list[float],
    capacity_kwh: float = 100.0,
    max_power_kw: float = 40.0,
    mode: str = "balanced",
    price_import: float = 0.12,
    price_export: float = 0.05,
    co2_kg_per_kwh: float = 0.45,
) -> dict[str, Any]:
    """
    Run HybridEnergyOptimizer for a student-chosen battery size.
    Returns profit, CO₂, self-consumption, schedule head.
    """
    bat = BatteryParams(
        capacity_kwh=float(capacity_kwh),
        max_charge_kw=float(max_power_kw),
        max_discharge_kw=float(max_power_kw),
        efficiency=0.95,
        initial_soc_kwh=float(capacity_kwh) * 0.5,
    )
    opt = HybridEnergyOptimizer(
        battery=bat,
        co2_grid_kg_per_kwh=co2_kg_per_kwh,
        price_import=price_import,
        price_export=price_export,
    )
    result = opt.optimize(
        solar,
        wind,
        load=load,
        mode=mode if mode in ("max_profit", "min_co2", "balanced") else "balanced",
    )
    return {
        "total_profit": result["total_profit"],
        "total_co2_kg": result["total_co2_kg"],
        "self_consumption_rate": result["self_consumption_rate"],
        "status": result["status"],
        "mode": result["mode"],
        "schedule": result["schedule"],
        "plot_fn": lambda: opt.plot_results(result),
    }


def synthetic_day_profiles(seed: int = 0) -> dict[str, np.ndarray]:
    """Simple 24h solar/wind/load profiles for labs."""
    rng = np.random.default_rng(seed)
    h = np.arange(24)
    solar = np.clip(np.sin((h - 6) * np.pi / 14) * 100, 0, None)
    solar = np.where((h >= 6) & (h <= 18), solar, 0.0)
    wind = np.clip(35 + 12 * np.sin(h * np.pi / 10) + rng.normal(0, 2, 24), 0, None)
    load = np.clip(55 + 25 * np.sin((h - 7) * np.pi / 14), 30, None)
    return {"hour": h, "solar": solar, "wind": wind, "load": load}


def fault_image_teaching_notes(lang: str = "en") -> str:
    """Text shown when student uploads an image (detection may be separate page)."""
    if lang == "kk":
        return (
            "Суретті **Fault Detection** бетінде де тексеріңіз. "
            "AI тек көмекші: ыстық нүкте, шаң, жарық күдігін оператор растауы керек. "
            "Тазалау кеңестері: knowledge_base/cleaning/."
        )
    return (
        "Also run the image on the **Fault Detection** page. "
        "AI is assistive: hotspots, soiling, cracks need human confirmation. "
        "Cleaning tips live in knowledge_base/cleaning/."
    )
