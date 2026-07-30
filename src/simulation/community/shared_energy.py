"""
Simplified renewable energy community (REC) accounting for labs.

Educational model — not a full Italian CACER / ARERA incentive engine.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from src.simulation.community.bess_step import bess_step
from src.simulation.community.load_profile import scale_profile, synthetic_load_profile
from src.simulation.microgrid.solar_panel import SolarArray, SolarPanelConfig


def _pv_series_from_weather(
    weather_df: pd.DataFrame,
    num_panels: int,
    panel: SolarPanelConfig | None = None,
) -> np.ndarray:
    panel = panel or SolarPanelConfig()
    arr = SolarArray(panel, num_panels=num_panels)
    return np.array(
        [
            arr.calculate_power(float(r["irradiance_w_m2"]), float(r["temperature_c"])) / 1000.0
            for _, r in weather_df.iterrows()
        ],
        dtype=float,
    )


def run_shared_energy_day(
    weather_df: pd.DataFrame,
    *,
    n_users: int = 3,
    panels_per_user: int = 40,
    peak_load_kw: float = 4.0,
    community_battery_kwh: float = 30.0,
    dod: float = 0.8,
    eta_half: float = 0.95,
    price_import: float = 0.12,
    price_export: float = 0.06,
    seed: int = 42,
) -> dict[str, Any]:
    """
    Toy multi-user community for one weather day.

    Rules
    -----
    1. Each user: self-consume min(pv, load).
    2. Pool residual surplus and residual deficit.
    3. Community battery absorbs/supplies residual pool.
    4. Remaining deficit → grid import; remaining surplus → grid export.
    5. "Shared energy" = energy matched within the community pool
       (before battery and grid), plus battery-mediated local use (simplified).
    """
    n_users = max(1, int(n_users))
    n = len(weather_df)
    users_pv = []
    users_load = []
    for u in range(n_users):
        pv = _pv_series_from_weather(weather_df, panels_per_user + u * 5)
        load_df = scale_profile(
            synthetic_load_profile(n, seed=seed + u),
            peak_kw=peak_load_kw * (0.85 + 0.1 * (u % 3)),
        )
        load = load_df["load_kw"].to_numpy(dtype=float)
        # Align length
        m = min(len(pv), len(load), n)
        users_pv.append(pv[:m])
        users_load.append(load[:m])
    n = min(len(p) for p in users_pv)
    users_pv = [p[:n] for p in users_pv]
    users_load = [p[:n] for p in users_load]

    bmax = float(community_battery_kwh)
    bmin = bmax * (1.0 - float(dod))
    soc = bmax * 0.5

    rows = []
    shared_total = 0.0
    import_total = 0.0
    export_total = 0.0
    self_total = 0.0
    pv_total = 0.0
    load_total = 0.0

    for t in range(n):
        surplus_pool = 0.0
        deficit_pool = 0.0
        self_t = 0.0
        pv_t = 0.0
        load_t = 0.0
        for u in range(n_users):
            pv_u = float(users_pv[u][t])
            ld_u = float(users_load[u][t])
            sc = min(pv_u, ld_u)
            self_t += sc
            surplus_pool += max(0.0, pv_u - ld_u)
            deficit_pool += max(0.0, ld_u - pv_u)
            pv_t += pv_u
            load_t += ld_u

        # Community matching of residual surplus vs deficit
        shared = min(surplus_pool, deficit_pool)
        surplus_pool -= shared
        deficit_pool -= shared
        shared_total += shared

        # Battery sees +surplus charge intent or -deficit discharge intent (kWh, dt=1h)
        e_intent = surplus_pool - deficit_pool
        step = bess_step(
            e_intent,
            soc,
            eta_halfcycle=eta_half,
            battery_min_kwh=bmin,
            battery_max_kwh=bmax,
        )
        soc = step.soc_kwh
        # Map battery action to residual grid
        # If we intended charge and battery took less → export residual
        # If we intended discharge and battery gave less → import residual
        if e_intent > 0:
            # charge path: export what battery didn't absorb (approx)
            absorbed = max(0.0, step.e_terminal_real_kwh)
            export_t = max(0.0, e_intent - absorbed)
            import_t = 0.0
        elif e_intent < 0:
            discharged = max(0.0, -step.e_discharge_net_kwh)
            need = -e_intent
            import_t = max(0.0, need - discharged)
            export_t = 0.0
        else:
            import_t = 0.0
            export_t = 0.0

        import_total += import_t
        export_total += export_t
        self_total += self_t
        pv_total += pv_t
        load_total += load_t

        rows.append(
            {
                "hour": t,
                "pv_kw": pv_t,
                "load_kw": load_t,
                "self_kw": self_t,
                "shared_kw": shared,
                "import_kw": import_t,
                "export_kw": export_t,
                "soc": step.soc_frac,
            }
        )

    bill_import = import_total * float(price_import)
    revenue_export = export_total * float(price_export)
    sc_pct = 100.0 * self_total / pv_total if pv_total > 1e-9 else 0.0
    shared_pct = 100.0 * shared_total / pv_total if pv_total > 1e-9 else 0.0

    return {
        "timeseries": pd.DataFrame(rows),
        "n_users": n_users,
        "pv_kwh": pv_total,
        "load_kwh": load_total,
        "self_kwh": self_total,
        "shared_kwh": shared_total,
        "import_kwh": import_total,
        "export_kwh": export_total,
        "self_consumption_pct": sc_pct,
        "shared_pct_of_pv": shared_pct,
        "bill_import": bill_import,
        "revenue_export": revenue_export,
        "net_bill_proxy": bill_import - revenue_export,
        "final_soc": soc / bmax if bmax > 0 else 0.0,
    }
