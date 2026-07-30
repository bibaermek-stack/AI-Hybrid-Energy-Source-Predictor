"""Compare heuristic microgrid balancer vs EcoPradict PuLP optimizer."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.optimization.battery_model import BatteryParams
from src.optimization.hybrid_optimizer import HybridEnergyOptimizer
from src.simulation.microgrid.engine import run_day_simulation, summarize_day


def compare_heuristic_vs_pulp(
    weather_df: pd.DataFrame,
    *,
    num_panels: int = 100,
    battery_kwh: float = 50.0,
    load_kw: float = 15.0,
    price_import: float = 0.12,
    price_export: float = 0.06,
    co2_kg_per_kwh: float = 0.45,
    mode: str = "balanced",
) -> dict[str, Any]:
    """
    Run the same solar/load profile through:

    1. RenewableEnergySim-style heuristic ``run_day_simulation``
    2. ``HybridEnergyOptimizer`` (wind = 0)

    Returns both result frames and KPI deltas.
    """
    heur_df = run_day_simulation(
        weather_df,
        num_panels=num_panels,
        battery_kwh=battery_kwh,
        load_kw=load_kw,
    )
    heur = summarize_day(heur_df)

    solar = heur_df["pv_dc_kw"].to_numpy(dtype=float)
    # Prefer AC series if available
    if "pv_kw" in heur_df.columns:
        solar = heur_df["pv_kw"].to_numpy(dtype=float)
    wind = np.zeros_like(solar)
    load = np.full_like(solar, float(load_kw), dtype=float)

    opt = HybridEnergyOptimizer(
        battery=BatteryParams(
            capacity_kwh=float(battery_kwh),
            max_charge_kw=max(float(battery_kwh) / 2.0, 1.0),
            max_discharge_kw=max(float(battery_kwh) / 2.0, 1.0),
        ),
        co2_grid_kg_per_kwh=float(co2_kg_per_kwh),
        price_import=float(price_import),
        price_export=float(price_export),
    )
    pulp_res = opt.optimize(
        solar_forecast=solar,
        wind_forecast=wind,
        load=load,
        mode=mode,  # type: ignore[arg-type]
    )
    schedule: pd.DataFrame = pulp_res["schedule"]

    pulp_import = float(pulp_res.get("grid_import_kwh") or 0.0)
    pulp_export = float(pulp_res.get("grid_export_kwh") or 0.0)
    pulp_co2 = float(pulp_res.get("total_co2_kg") or 0.0)
    pulp_profit = float(pulp_res.get("total_profit") or 0.0)

    # Heuristic economic proxy
    heur_cost = heur["import_kwh"] * price_import - heur["export_kwh"] * price_export
    heur_co2 = heur["import_kwh"] * co2_kg_per_kwh

    return {
        "heuristic_df": heur_df,
        "heuristic_summary": heur,
        "heuristic_cost_proxy": heur_cost,
        "heuristic_co2_kg": heur_co2,
        "pulp_result": pulp_res,
        "pulp_schedule": schedule,
        "pulp_import_kwh": pulp_import,
        "pulp_export_kwh": pulp_export,
        "pulp_co2_kg": pulp_co2,
        "pulp_profit": pulp_profit,
        "delta_import_kwh": heur["import_kwh"] - pulp_import,
        "delta_co2_kg": heur_co2 - pulp_co2,
    }
