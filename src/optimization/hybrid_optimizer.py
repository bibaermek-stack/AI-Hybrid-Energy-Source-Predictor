"""
Hybrid renewable energy dispatch optimizer for EcoPredict AI.

Two layers
----------
1. ``optimize_energy`` — single-timestep heuristic (API ``/predict`` compatibility).
2. ``HybridEnergyOptimizer`` — multi-hour LP via PuLP for solar + wind + battery
   + grid, multi-objective (profit vs CO₂).

Streamlit / API can call::

    opt = HybridEnergyOptimizer(...)
    result = opt.optimize(solar_fc, wind_fc, load=..., mode="balanced")
    fig = opt.plot_results(result)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Single-step heuristic (existing public API — do not break tests / routes)
# ---------------------------------------------------------------------------

_PRIMARY_SHARE = 0.65

ModeName = Literal["max_profit", "min_co2", "balanced"]


def _validate_nonneg(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric, got {type(value).__name__}")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{name} contains NaN or Inf: {value}")
    if value < 0:
        raise ValueError(f"{name} cannot be negative: {value}")
    return value


def _merit_order_dispatch(
    solar: float,
    wind: float,
    load: float,
    solar_cost: float,
    wind_cost: float,
    strategy: str,
) -> tuple[float, float]:
    """Allocate solar/wind to meet ``load`` (kW). Returns (solar_used, wind_used)."""
    if load <= 0:
        return 0.0, 0.0

    if strategy == "balanced":
        total = solar + wind
        if total <= 0:
            return 0.0, 0.0
        serve = min(load, total)
        return serve * (solar / total), serve * (wind / total)

    if strategy == "max_power":
        s = min(solar, load)
        w = min(wind, load - s)
        return s, w

    if abs(solar_cost - wind_cost) < 1e-12:
        total = solar + wind
        if total <= 0:
            return 0.0, 0.0
        serve = min(load, total)
        return serve * (solar / total), serve * (wind / total)

    sources = [
        ("solar", solar, solar_cost),
        ("wind", wind, wind_cost),
    ]
    sources.sort(key=lambda x: x[2])

    remaining = load
    used = {"solar": 0.0, "wind": 0.0}
    for name, available, _cost in sources:
        take = min(available, remaining)
        used[name] = take
        remaining -= take
        if remaining <= 1e-12:
            break
    return used["solar"], used["wind"]


def _recommend(
    solar_used: float, wind_used: float, solar_avail: float, wind_avail: float
) -> str:
    """Name primary source or Hybrid based on contribution shares."""
    served = solar_used + wind_used
    if served <= 1e-9:
        if solar_avail <= 1e-9 and wind_avail <= 1e-9:
            return "Hybrid"
        if solar_avail > wind_avail:
            return "Solar"
        if wind_avail > solar_avail:
            return "Wind"
        return "Hybrid"

    s_share = solar_used / served
    w_share = wind_used / served
    if s_share >= _PRIMARY_SHARE and w_share < (1 - _PRIMARY_SHARE):
        return "Solar"
    if w_share >= _PRIMARY_SHARE and s_share < (1 - _PRIMARY_SHARE):
        return "Wind"
    return "Hybrid"


def optimize_energy(
    solar: float,
    wind: float,
    load_kw: float | None = None,
    battery_kw: float = 0.0,
    solar_cost_per_kwh: float = 1.0,
    wind_cost_per_kwh: float = 1.0,
    strategy: str = "hybrid",
) -> dict[str, Any]:
    """
    Optimize hybrid solar–wind dispatch for a **single** time step.

    Used by FastAPI ``/predict`` and unit tests. For 24–48 h battery/grid
    scheduling, use :class:`HybridEnergyOptimizer`.
    """
    solar = _validate_nonneg("solar", solar)
    wind = _validate_nonneg("wind", wind)
    battery_kw = _validate_nonneg("battery_kw", battery_kw)
    solar_cost_per_kwh = _validate_nonneg("solar_cost_per_kwh", solar_cost_per_kwh)
    wind_cost_per_kwh = _validate_nonneg("wind_cost_per_kwh", wind_cost_per_kwh)

    strategy = (strategy or "hybrid").lower().strip()
    if strategy not in {"hybrid", "min_cost", "max_power", "balanced"}:
        raise ValueError(
            f"Unknown strategy '{strategy}'. "
            "Use hybrid | min_cost | max_power | balanced"
        )

    available = solar + wind
    full_offtake = load_kw is None
    if full_offtake:
        load = available
    else:
        load = _validate_nonneg("load_kw", load_kw)

    solar_used, wind_used = _merit_order_dispatch(
        solar, wind, load, solar_cost_per_kwh, wind_cost_per_kwh, strategy
    )

    renewable_used = solar_used + wind_used
    residual_load = max(0.0, load - renewable_used)
    battery_used = min(battery_kw, residual_load)
    shortfall = max(0.0, residual_load - battery_used)
    curtailment = max(0.0, available - renewable_used)

    if full_offtake:
        solar_used = solar
        wind_used = wind
        renewable_used = available
        curtailment = 0.0
        shortfall = 0.0
        battery_used = 0.0

    served = renewable_used + battery_used
    solar_share = (solar_used / renewable_used) if renewable_used > 1e-12 else 0.0
    wind_share = (wind_used / renewable_used) if renewable_used > 1e-12 else 0.0
    hybrid_share = 2.0 * min(solar_share, wind_share) if renewable_used > 1e-12 else 0.0

    if load > 1e-12:
        reliability = min(1.0, served / load)
    else:
        reliability = 1.0

    recommended = _recommend(solar_used, wind_used, solar, wind)
    estimated_cost = solar_used * solar_cost_per_kwh + wind_used * wind_cost_per_kwh

    return {
        "solar_power": float(solar),
        "wind_power": float(wind),
        "total_energy": float(available),
        "recommended_source": recommended,
        "solar_used": float(solar_used),
        "wind_used": float(wind_used),
        "battery_used": float(battery_used),
        "load_kw": float(load),
        "shortfall_kw": float(shortfall),
        "curtailment_kw": float(curtailment),
        "solar_share": float(round(solar_share, 4)),
        "wind_share": float(round(wind_share, 4)),
        "hybrid_share": float(round(hybrid_share, 4)),
        "reliability_index": float(round(reliability, 4)),
        "strategy": strategy,
        "estimated_cost": float(round(estimated_cost, 4)),
    }


# ---------------------------------------------------------------------------
# Multi-hour LP optimizer (PuLP)
# ---------------------------------------------------------------------------


from src.optimization.battery_model import BatteryParams  # noqa: E402



@dataclass
class HybridEnergyOptimizer:
    """
    Multi-hour hybrid dispatch optimizer (solar + wind + battery + grid).

    Formulates a linear program (PuLP) over a 24–48 h horizon.

    **Energy balance** (each hour ``t``, resolution ``dt`` hours)::

        solar_t + wind_t + discharge_t + grid_import_t
            = load_t + charge_t + grid_export_t + curtail_t

    Renewables are free at the margin; economics come from grid prices.
    CO₂ is attributed only to grid imports.

    Parameters
    ----------
    battery :
        BatteryParams instance.
    co2_grid_kg_per_kwh :
        Grid emission factor (kg CO₂ / kWh imported).
    price_import :
        Default grid import price ($/kWh) if no series provided.
    price_export :
        Default export (feed-in) price ($/kWh).
    dt_hours :
        Time step length (1.0 = hourly).
    """

    battery: BatteryParams = field(default_factory=BatteryParams)
    co2_grid_kg_per_kwh: float = 0.45
    price_import: float = 0.12
    price_export: float = 0.06
    dt_hours: float = 1.0

    def optimize(
        self,
        solar_forecast: Sequence[float] | pd.Series | np.ndarray,
        wind_forecast: Sequence[float] | pd.Series | np.ndarray,
        load: Sequence[float] | pd.Series | np.ndarray | float | None = None,
        price_import: Sequence[float] | pd.Series | np.ndarray | float | None = None,
        price_export: Sequence[float] | pd.Series | np.ndarray | float | None = None,
        *,
        mode: ModeName = "balanced",
        weight_profit: float | None = None,
        weight_co2: float | None = None,
        allow_grid_export: bool = True,
        time_index: Sequence | None = None,
    ) -> dict[str, Any]:
        """
        Solve optimal dispatch.

        Parameters
        ----------
        solar_forecast, wind_forecast :
            Available generation (kW) per time step. Negative values clipped to 0.
        load :
            Demand (kW). ``None`` → use renewable total each hour (self-consume all).
            Scalar → constant load.
        price_import, price_export :
            $/kWh series or scalars. Defaults from instance fields.
        mode :
            ``max_profit`` | ``min_co2`` | ``balanced`` (sets objective weights).
        weight_profit, weight_co2 :
            Override mode weights (non-negative). Objective maximizes::

                w_p * profit - w_c * (co2_kg * scale)

            where scale converts kg to $ units for balanced mode.
        allow_grid_export :
            If False, export variables are fixed at 0.
        time_index :
            Optional labels for schedule rows (hours / timestamps).

        Returns
        -------
        dict
            schedule (DataFrame), total_profit, total_co2_kg, self_consumption_rate,
            mode, weights, status, objective_value
        """
        try:
            import pulp
        except ImportError as e:
            raise ImportError(
                "PuLP is required for HybridEnergyOptimizer. "
                "Install with: pip install pulp"
            ) from e

        solar = self._to_array(solar_forecast, "solar_forecast")
        wind = self._to_array(wind_forecast, "wind_forecast")
        if len(solar) != len(wind):
            raise ValueError(
                f"solar and wind length mismatch: {len(solar)} vs {len(wind)}"
            )
        n = len(solar)
        if n < 1:
            raise ValueError("Forecast horizon must be at least 1 hour")

        load_arr = self._resolve_load(load, solar, wind)
        p_imp = self._resolve_price(price_import, n, self.price_import, "price_import")
        p_exp = self._resolve_price(price_export, n, self.price_export, "price_export")

        w_p, w_c = self._mode_weights(mode, weight_profit, weight_co2)

        bat = self.battery
        dt = float(self.dt_hours)
        if dt <= 0:
            raise ValueError("dt_hours must be positive")

        eta = bat.efficiency
        soc0 = float(bat.initial_soc_kwh)
        soc_min = bat.min_soc_frac * bat.capacity_kwh
        soc_max = bat.max_soc_frac * bat.capacity_kwh
        # Clamp initial SOC into allowed band
        soc0 = min(max(soc0, soc_min), soc_max)

        # --- LP model -------------------------------------------------------
        prob = pulp.LpProblem("HybridEnergyDispatch", pulp.LpMaximize)

        # Decision variables (kW for powers; kWh for SOC)
        ch = pulp.LpVariable.dicts("charge", range(n), lowBound=0)
        dis = pulp.LpVariable.dicts("discharge", range(n), lowBound=0)
        g_in = pulp.LpVariable.dicts("grid_import", range(n), lowBound=0)
        g_out = pulp.LpVariable.dicts(
            "grid_export", range(n), lowBound=0 if allow_grid_export else 0, upBound=None
        )
        if not allow_grid_export:
            for t in range(n):
                g_out[t].upBound = 0

        # Curtailment (unused renewable) kW
        curt = pulp.LpVariable.dicts("curtail", range(n), lowBound=0)
        # How much solar/wind is actually used (for reporting; optional free within avail)
        # We model renewable as must-be-absorbed via balance; curtail absorbs excess.

        soc = pulp.LpVariable.dicts("soc", range(n + 1), lowBound=soc_min, upBound=soc_max)

        # Binary: prevent simultaneous charge & discharge
        is_ch = pulp.LpVariable.dicts("is_charging", range(n), cat="Binary")

        # Initial SOC
        prob += soc[0] == soc0

        for t in range(n):
            s_t = float(solar[t])
            w_t = float(wind[t])
            L_t = float(load_arr[t])

            # Power limits
            prob += ch[t] <= bat.max_charge_kw
            prob += dis[t] <= bat.max_discharge_kw
            # Mutual exclusion via binary
            prob += ch[t] <= bat.max_charge_kw * is_ch[t]
            prob += dis[t] <= bat.max_discharge_kw * (1 - is_ch[t])

            # Export cannot exceed residual generation after load/charge (soft via balance)
            # Energy balance (kW, instantaneous power):
            #   solar + wind + discharge + import = load + charge + export + curtail
            prob += (
                s_t + w_t + dis[t] + g_in[t]
                == L_t + ch[t] + g_out[t] + curt[t]
            ), f"balance_{t}"

            # Curtailment cannot exceed available renewable
            prob += curt[t] <= s_t + w_t

            # Battery SOC dynamics (kWh)
            # charge adds eta * P_ch * dt; discharge removes P_dis / eta * dt
            prob += (
                soc[t + 1]
                == soc[t] + eta * ch[t] * dt - (dis[t] / eta) * dt
            ), f"soc_{t}"

        # Objective: economic profit and CO₂ (import only)
        # profit ($) = sum( export * p_exp - import * p_imp ) * dt
        profit_terms = []
        co2_terms = []
        for t in range(n):
            profit_terms.append((g_out[t] * p_exp[t] - g_in[t] * p_imp[t]) * dt)
            co2_terms.append(g_in[t] * self.co2_grid_kg_per_kwh * dt)

        total_profit = pulp.lpSum(profit_terms)
        total_co2 = pulp.lpSum(co2_terms)

        # Scale CO₂ into roughly comparable magnitude for balanced mode
        # (use price_import mean as $ per kg proxy when w_c > 0)
        co2_dollar_scale = float(np.mean(p_imp)) if np.mean(p_imp) > 0 else 0.1
        # Maximize w_p * profit - w_c * co2_kg * $/kg_proxy
        prob += w_p * total_profit - w_c * total_co2 * co2_dollar_scale

        # Solve
        solver = pulp.PULP_CBC_CMD(msg=False)
        status = prob.solve(solver)
        status_name = pulp.LpStatus.get(status, str(status))

        if status_name not in ("Optimal", "Optimal Infeasible"):
            # CBC returns Optimal; if not optimal, still extract if possible
            if pulp.value(prob.objective) is None:
                raise RuntimeError(f"Optimization failed with status={status_name}")

        # Extract schedule
        hours = list(time_index) if time_index is not None else list(range(n))
        if len(hours) != n:
            hours = list(range(n))

        rows = []
        for t in range(n):
            ch_v = float(pulp.value(ch[t]) or 0.0)
            dis_v = float(pulp.value(dis[t]) or 0.0)
            gin_v = float(pulp.value(g_in[t]) or 0.0)
            gout_v = float(pulp.value(g_out[t]) or 0.0)
            curt_v = float(pulp.value(curt[t]) or 0.0)
            soc_v = float(pulp.value(soc[t]) or 0.0)
            s_t = float(solar[t])
            w_t = float(wind[t])
            # Attribution: solar/wind "used" ≈ available - share of curtailment
            ren = s_t + w_t
            if ren > 1e-9:
                solar_used = s_t * (1.0 - curt_v / ren)
                wind_used = w_t * (1.0 - curt_v / ren)
            else:
                solar_used = 0.0
                wind_used = 0.0

            rows.append(
                {
                    "hour": hours[t],
                    "solar_avail": s_t,
                    "wind_avail": w_t,
                    "solar_used": solar_used,
                    "wind_used": wind_used,
                    "load": float(load_arr[t]),
                    "battery_charge": ch_v,
                    "battery_discharge": dis_v,
                    "grid_import": gin_v,
                    "grid_export": gout_v,
                    "curtailment": curt_v,
                    "soc": soc_v,
                    "soc_pct": 100.0 * soc_v / bat.capacity_kwh if bat.capacity_kwh else 0.0,
                    "price_import": p_imp[t],
                    "price_export": p_exp[t],
                }
            )

        schedule = pd.DataFrame(rows)
        # Final SOC
        schedule.attrs["final_soc"] = float(pulp.value(soc[n]) or 0.0)

        profit_val = float(pulp.value(total_profit) or 0.0)
        co2_val = float(pulp.value(total_co2) or 0.0)

        # Self-consumption: renewable used on-site / total renewable available
        ren_avail = float(schedule["solar_avail"].sum() + schedule["wind_avail"].sum()) * dt
        ren_curtailed = float(schedule["curtailment"].sum()) * dt
        ren_used = max(0.0, ren_avail - ren_curtailed)
        # On-site = used - export (export is surplus sold)
        # Approx: min(ren_used, load_served_from_ren)
        load_energy = float(schedule["load"].sum()) * dt
        export_energy = float(schedule["grid_export"].sum()) * dt
        import_energy = float(schedule["grid_import"].sum()) * dt
        # Self-consumed renewable ≈ ren_used - export (clipped)
        self_consumed = max(0.0, ren_used - export_energy)
        if ren_avail > 1e-9:
            self_consumption_rate = 100.0 * min(1.0, self_consumed / ren_avail)
        else:
            self_consumption_rate = 0.0

        return {
            "schedule": schedule,
            "total_profit": profit_val,
            "total_co2_kg": co2_val,
            "self_consumption_rate": self_consumption_rate,
            "renewable_available_kwh": ren_avail,
            "renewable_used_kwh": ren_used,
            "grid_import_kwh": import_energy,
            "grid_export_kwh": export_energy,
            "load_kwh": load_energy,
            "mode": mode,
            "weights": {"profit": w_p, "co2": w_c},
            "status": status_name,
            "objective_value": float(pulp.value(prob.objective) or 0.0),
            "battery": {
                "capacity_kwh": bat.capacity_kwh,
                "initial_soc_kwh": soc0,
                "final_soc_kwh": schedule.attrs["final_soc"],
            },
        }

    # ----- helpers ----------------------------------------------------------

    @staticmethod
    def _to_array(x: Sequence[float] | pd.Series | np.ndarray, name: str) -> np.ndarray:
        if isinstance(x, pd.Series):
            arr = x.astype(float).to_numpy()
        else:
            arr = np.asarray(x, dtype=float).reshape(-1)
        if arr.size == 0:
            raise ValueError(f"{name} is empty")
        if np.any(~np.isfinite(arr)):
            raise ValueError(f"{name} contains NaN or Inf")
        # Edge case: negative forecasts → clip
        return np.maximum(arr, 0.0)

    def _resolve_load(
        self,
        load: Sequence[float] | pd.Series | np.ndarray | float | None,
        solar: np.ndarray,
        wind: np.ndarray,
    ) -> np.ndarray:
        n = len(solar)
        if load is None:
            # Self-consume all renewable each hour (no forced grid demand)
            return solar + wind
        if isinstance(load, (int, float)) and not isinstance(load, bool):
            v = _validate_nonneg("load", float(load))
            return np.full(n, v, dtype=float)
        arr = self._to_array(load, "load")
        if len(arr) != n:
            raise ValueError(f"load length {len(arr)} != horizon {n}")
        return arr

    def _resolve_price(
        self,
        price: Sequence[float] | pd.Series | np.ndarray | float | None,
        n: int,
        default: float,
        name: str,
    ) -> np.ndarray:
        if price is None:
            return np.full(n, float(default), dtype=float)
        if isinstance(price, (int, float)) and not isinstance(price, bool):
            return np.full(n, max(0.0, float(price)), dtype=float)
        arr = self._to_array(price, name)
        if len(arr) != n:
            raise ValueError(f"{name} length {len(arr)} != horizon {n}")
        return arr

    @staticmethod
    def _mode_weights(
        mode: str,
        weight_profit: float | None,
        weight_co2: float | None,
    ) -> tuple[float, float]:
        mode = (mode or "balanced").lower().strip()
        presets: Mapping[str, tuple[float, float]] = {
            "max_profit": (1.0, 0.0),
            "min_co2": (0.0, 1.0),
            "balanced": (0.5, 0.5),
        }
        if mode not in presets:
            raise ValueError(
                f"Unknown mode '{mode}'. Use max_profit | min_co2 | balanced"
            )
        w_p, w_c = presets[mode]
        if weight_profit is not None:
            w_p = _validate_nonneg("weight_profit", weight_profit)
        if weight_co2 is not None:
            w_c = _validate_nonneg("weight_co2", weight_co2)
        if w_p + w_c <= 1e-15:
            raise ValueError("At least one of weight_profit / weight_co2 must be > 0")
        return w_p, w_c

    def plot_results(
        self,
        result: dict[str, Any],
        *,
        backend: str = "plotly",
        title: str | None = None,
    ):
        """
        Plot dispatch schedule. Returns a plotly Figure or matplotlib Figure.

        Parameters
        ----------
        result :
            Output of :meth:`optimize`.
        backend :
            ``plotly`` (default, Streamlit-friendly) or ``matplotlib``.
        """
        schedule: pd.DataFrame = result["schedule"]
        title = title or (
            f"Hybrid dispatch ({result.get('mode')}) | "
            f"profit=${result.get('total_profit', 0):.2f} | "
            f"CO₂={result.get('total_co2_kg', 0):.1f} kg | "
            f"self-cons={result.get('self_consumption_rate', 0):.1f}%"
        )

        if backend == "matplotlib":
            import matplotlib.pyplot as plt

            fig, axes = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
            x = schedule["hour"]
            axes[0].stackplot(
                x,
                schedule["solar_used"],
                schedule["wind_used"],
                schedule["battery_discharge"],
                schedule["grid_import"],
                labels=["Solar", "Wind", "Batt dis.", "Grid in"],
                alpha=0.85,
            )
            axes[0].plot(x, schedule["load"], "k--", label="Load", linewidth=1.5)
            axes[0].set_ylabel("kW")
            axes[0].legend(loc="upper right", fontsize=8)
            axes[0].set_title(title)

            axes[1].bar(x, schedule["battery_charge"], label="Charge", color="tab:blue", alpha=0.7)
            axes[1].bar(
                x,
                -schedule["battery_discharge"],
                label="Discharge",
                color="tab:orange",
                alpha=0.7,
            )
            axes[1].set_ylabel("Battery kW")
            axes[1].legend(fontsize=8)

            axes[2].plot(x, schedule["soc_pct"], "g-", label="SOC %")
            axes[2].set_ylabel("SOC %")
            axes[2].set_xlabel("Hour")
            axes[2].legend(fontsize=8)
            fig.tight_layout()
            return fig

        # plotly
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=("Generation & load", "Battery power", "State of charge"),
        )
        x = schedule["hour"]
        fig.add_trace(
            go.Scatter(x=x, y=schedule["solar_used"], name="Solar used", stackgroup="sup"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(x=x, y=schedule["wind_used"], name="Wind used", stackgroup="sup"),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=schedule["battery_discharge"],
                name="Batt discharge",
                stackgroup="sup",
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x, y=schedule["grid_import"], name="Grid import", stackgroup="sup"
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x,
                y=schedule["load"],
                name="Load",
                line=dict(color="black", dash="dash", width=2),
            ),
            row=1,
            col=1,
        )
        fig.add_trace(
            go.Bar(x=x, y=schedule["battery_charge"], name="Charge"), row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=x, y=-schedule["battery_discharge"], name="Discharge"),
            row=2,
            col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=x, y=schedule["soc_pct"], name="SOC %", line=dict(color="green")
            ),
            row=3,
            col=1,
        )
        fig.update_layout(
            title=title,
            barmode="relative",
            height=720,
            legend=dict(orientation="h", y=1.12),
            template="plotly_white",
        )
        fig.update_yaxes(title_text="kW", row=1, col=1)
        fig.update_yaxes(title_text="kW", row=2, col=1)
        fig.update_yaxes(title_text="%", row=3, col=1)
        fig.update_xaxes(title_text="Hour", row=3, col=1)
        return fig


def optimize_horizon(
    solar_forecast: Sequence[float] | pd.Series,
    wind_forecast: Sequence[float] | pd.Series,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Convenience wrapper for Streamlit / notebooks.

    Example::

        result = optimize_horizon(solar_s, wind_s, load=80, mode="balanced")
        st.plotly_chart(HybridEnergyOptimizer().plot_results(result), width="stretch")
    """
    battery_kw = kwargs.pop("battery", None)
    if isinstance(battery_kw, dict):
        battery = BatteryParams(**battery_kw)
    elif isinstance(battery_kw, BatteryParams):
        battery = battery_kw
    else:
        battery = BatteryParams()
    opt = HybridEnergyOptimizer(
        battery=battery,
        co2_grid_kg_per_kwh=kwargs.pop("co2_grid_kg_per_kwh", 0.45),
        price_import=kwargs.pop("default_price_import", 0.12),
        price_export=kwargs.pop("default_price_export", 0.06),
        dt_hours=kwargs.pop("dt_hours", 1.0),
    )
    return opt.optimize(solar_forecast, wind_forecast, **kwargs)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Single-step optimize_energy (API compatible) ===")
    print(optimize_energy(800.5, 600.3))
    print(optimize_energy(400, 400, load_kw=500, battery_kw=50, strategy="hybrid"))

    print("\n=== HybridEnergyOptimizer 24h demo ===")
    rng = np.random.default_rng(42)
    hours = np.arange(24)
    # Synthetic clear-sky-ish solar + wind
    solar_fc = np.clip(np.sin((hours - 6) * np.pi / 14) * 120, 0, None)
    solar_fc = np.where((hours >= 6) & (hours <= 18), solar_fc, 0.0)
    wind_fc = 40 + 15 * np.sin(hours * np.pi / 12) + rng.normal(0, 3, 24)
    wind_fc = np.clip(wind_fc, 0, None)
    load_fc = 70 + 20 * np.sin((hours - 8) * np.pi / 12)
    load_fc = np.clip(load_fc, 40, None)

    optimizer = HybridEnergyOptimizer(
        battery=BatteryParams(
            capacity_kwh=200,
            max_charge_kw=50,
            max_discharge_kw=50,
            efficiency=0.95,
            initial_soc_kwh=100,
        ),
        co2_grid_kg_per_kwh=0.5,
        price_import=0.15,
        price_export=0.05,
    )

    for mode in ("max_profit", "min_co2", "balanced"):
        res = optimizer.optimize(
            solar_fc, wind_fc, load=load_fc, mode=mode, time_index=hours
        )
        print(
            f"[{mode:11}] status={res['status']:8}  "
            f"profit=${res['total_profit']:8.2f}  "
            f"CO2={res['total_co2_kg']:7.2f} kg  "
            f"self={res['self_consumption_rate']:5.1f}%"
        )

    # Optional plot when run interactively
    try:
        fig = optimizer.plot_results(res, backend="plotly")
        # fig.show()  # uncomment locally
        print("Plotly figure built:", type(fig).__name__)
    except Exception as exc:
        print("Plot skipped:", exc)
