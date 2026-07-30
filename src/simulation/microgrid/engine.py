"""Day / profile simulation runners for education labs."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.simulation.microgrid.battery_ess import BatteryESS
from src.simulation.microgrid.inverter import Inverter
from src.simulation.microgrid.load_balancer import LoadBalancer
from src.simulation.microgrid.mppt import MPPTController
from src.simulation.microgrid.solar_panel import SolarArray, SolarPanelConfig


def run_day_simulation(
    weather_df: pd.DataFrame,
    *,
    num_panels: int = 100,
    battery_kwh: float = 50.0,
    max_charge_kw: float | None = None,
    load_kw: float = 15.0,
    inverter_kw: float = 40.0,
    panel: SolarPanelConfig | None = None,
    dt_hours: float = 1.0,
    initial_soc_frac: float = 0.5,
) -> pd.DataFrame:
    """
    Run heuristic PV–BESS–grid dispatch over a weather profile.

    Parameters
    ----------
    weather_df :
        Columns: ``irradiance_w_m2``, ``temperature_c``; optional ``time``.
    num_panels, battery_kwh, load_kw :
        Lab control parameters.
    Returns
    -------
    DataFrame with time, pv_kw, load_kw, soc, grid_import_kw, grid_export_kw, ...
    """
    required = {"irradiance_w_m2", "temperature_c"}
    missing = required - set(weather_df.columns)
    if missing:
        raise ValueError(f"weather_df missing columns: {sorted(missing)}")

    panel = panel or SolarPanelConfig()
    max_charge_kw = float(max_charge_kw if max_charge_kw is not None else max(battery_kwh / 2.0, 1.0))
    array = SolarArray(panel, num_panels=num_panels)
    battery = BatteryESS(
        capacity_kwh=battery_kwh,
        max_charge_kw=max_charge_kw,
        initial_soc_frac=initial_soc_frac,
    )
    inverter = Inverter(rated_power_kw=inverter_kw)
    balancer = LoadBalancer(inverter, battery)

    rows: list[dict[str, Any]] = []
    for i, row in weather_df.iterrows():
        irr = float(row["irradiance_w_m2"])
        temp = float(row["temperature_c"])
        pv_w = array.calculate_power(irr, temp)
        pv_kw = pv_w / 1000.0
        state = balancer.dispatch(pv_kw, float(load_kw), dt_hours=dt_hours)
        tval = row["time"] if "time" in weather_df.columns else i
        rows.append(
            {
                "time": tval,
                "irradiance_w_m2": irr,
                "temperature_c": temp,
                "pv_kw": state["pv_ac_kw"],
                "pv_dc_kw": state["pv_dc_kw"],
                "load_kw": state["load_kw"],
                "soc": state["battery_soc"],
                "grid_import_kw": state["grid_import_kw"],
                "grid_export_kw": state["grid_export_kw"],
                "battery_charge_kw": state["battery_charge_kw"],
                "battery_discharge_kw": state["battery_discharge_kw"],
            }
        )
    return pd.DataFrame(rows)


def run_mppt_trace(
    irradiance: float = 800.0,
    *,
    step_size: float = 0.5,
    steps: int = 80,
    panel: SolarPanelConfig | None = None,
) -> pd.DataFrame:
    """
    Simulate P&O walking along a synthetic I–V curve.

    Returns columns: step, v, i, p, v_ref.
    """
    panel = panel or SolarPanelConfig()
    array = SolarArray(panel, num_panels=1)
    v_curve, i_curve = array.get_iv_curve(irradiance)
    # Use curve as lookup by nearest V
    ctrl = MPPTController(step_size=step_size, v_ref=float(panel.nominal_voltage) * 0.7)
    rows = []
    v = ctrl.v_ref
    for s in range(int(steps)):
        idx = int(np.argmin(np.abs(v_curve - v)))
        i = float(i_curve[idx])
        v_meas = float(v_curve[idx])
        p = v_meas * i
        v_ref = ctrl.optimize(v_meas, i)
        rows.append({"step": s, "v": v_meas, "i": i, "p": p, "v_ref": v_ref})
        v = v_ref
        # clamp to curve range
        v = float(np.clip(v, v_curve.min(), v_curve.max()))
    return pd.DataFrame(rows)


def summarize_day(df: pd.DataFrame, dt_hours: float = 1.0) -> dict[str, float]:
    """Energy totals (kWh) and self-consumption proxy for lab KPIs."""
    if df.empty:
        return {
            "pv_kwh": 0.0,
            "load_kwh": 0.0,
            "import_kwh": 0.0,
            "export_kwh": 0.0,
            "self_consumption_pct": 0.0,
        }
    dt = float(dt_hours)
    pv = float(df["pv_kw"].sum() * dt)
    load = float(df["load_kw"].sum() * dt)
    imp = float(df["grid_import_kw"].sum() * dt)
    exp = float(df["grid_export_kw"].sum() * dt)
    # self-consumed PV ≈ pv - export (clipped)
    self_c = max(0.0, pv - exp)
    sc_pct = 100.0 * self_c / pv if pv > 1e-9 else 0.0
    return {
        "pv_kwh": pv,
        "load_kwh": load,
        "import_kwh": imp,
        "export_kwh": exp,
        "self_consumption_pct": sc_pct,
        "final_soc": float(df["soc"].iloc[-1]) if "soc" in df.columns else 0.0,
    }
