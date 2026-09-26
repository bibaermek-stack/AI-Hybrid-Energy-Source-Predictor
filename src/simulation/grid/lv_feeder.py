"""
Radial low-voltage feeder load flow for the power-flow lab.

Replaces the offline pandapower notebook as the lab's engine, so the lab runs
on the website and in the mobile app (numpy only). The physics is the same
backward/forward sweep pandapower uses for radial networks, on a balanced
three-phase feeder solved per phase:

    bus 0 (transformer LV busbar, fixed voltage) — segment — bus 1 — … — bus N

Every house bus has the same load and the same PV export. A PV inverter may
absorb reactive power (power factor < 1), the standard counter-measure to
voltage rise, which the lab lets students try.

Sign convention: an injection S_i > 0 means power flows *into* the feeder at
bus i (PV export exceeds load). Branch k joins bus k-1 and bus k and carries
the sum of the injections downstream of it toward the transformer, so

    V_k = V_{k-1} + Z_k * J_k      (J_k: current from bus k toward bus k-1)

With export the voltage therefore rises along the feeder, which is the effect
the lab is about. Limits follow EN 50160: 0.90–1.10 pu.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

V_MIN_PU = 0.90
V_MAX_PU = 1.10

# Typical buried LV cables (NAYY-J aluminium, 4 cores), per phase, 20 °C.
CABLES: dict[str, dict[str, Any]] = {
    "nayy_4x50": {
        "r_ohm_per_km": 0.642,
        "x_ohm_per_km": 0.083,
        "i_max_a": 142.0,
        "label": "NAYY 4×50 mm²",
    },
    "nayy_4x95": {
        "r_ohm_per_km": 0.320,
        "x_ohm_per_km": 0.082,
        "i_max_a": 215.0,
        "label": "NAYY 4×95 mm²",
    },
    "nayy_4x150": {
        "r_ohm_per_km": 0.206,
        "x_ohm_per_km": 0.080,
        "i_max_a": 275.0,
        "label": "NAYY 4×150 mm²",
    },
}


@dataclass
class FeederResult:
    v_pu: np.ndarray  # per bus, bus 0 = transformer
    branch_current_a: np.ndarray  # per segment 1..N
    losses_kw: float
    iterations: int

    @property
    def v_max_pu(self) -> float:
        return float(self.v_pu.max())

    @property
    def v_min_pu(self) -> float:
        return float(self.v_pu.min())


def solve_feeder(
    *,
    n_houses: int,
    length_m: float,
    cable: str,
    pv_kw_per_house: float,
    load_kw_per_house: float,
    pv_power_factor: float = 1.0,
    load_power_factor: float = 0.95,
    v_source_pu: float = 1.0,
    v_nominal_ll: float = 400.0,
    tol: float = 1e-9,
    max_iter: int = 100,
) -> FeederResult:
    """Balanced three-phase radial feeder with identical houses at equal spacing."""
    n = int(n_houses)
    if n < 1:
        raise ValueError("n_houses must be >= 1")
    if cable not in CABLES:
        raise ValueError(f"unknown cable {cable!r}")
    if not 0.0 < pv_power_factor <= 1.0 or not 0.0 < load_power_factor <= 1.0:
        raise ValueError("power factors must be in (0, 1]")

    spec = CABLES[cable]
    seg_km = float(length_m) / 1000.0 / n
    z = complex(spec["r_ohm_per_km"], spec["x_ohm_per_km"]) * seg_km

    v_ph = v_nominal_ll / math.sqrt(3.0)
    # Per-phase complex injection (W, var). PV absorbing Q: Q_pv = -P tan(phi).
    p_pv = pv_kw_per_house * 1000.0 / 3.0
    q_pv = -p_pv * math.tan(math.acos(pv_power_factor))
    p_ld = load_kw_per_house * 1000.0 / 3.0
    q_ld = p_ld * math.tan(math.acos(load_power_factor))
    s_inj = complex(p_pv - p_ld, q_pv - q_ld)

    v = np.full(n + 1, complex(v_source_pu * v_ph, 0.0))
    it = 0
    j = np.zeros(n + 1, dtype=complex)
    for it in range(1, max_iter + 1):
        i_inj = np.conj(s_inj / v[1:])  # injection current at buses 1..N
        # Backward sweep: branch k carries everything injected at buses k..N.
        j[1:] = np.cumsum(i_inj[::-1])[::-1]
        v_new = v.copy()
        for k in range(1, n + 1):
            v_new[k] = v_new[k - 1] + z * j[k]
        done = np.max(np.abs(v_new - v)) < tol * v_ph
        v = v_new
        if done:
            break

    losses_w = 3.0 * float(np.sum(np.abs(j[1:]) ** 2) * z.real)
    return FeederResult(
        v_pu=np.abs(v) / v_ph,
        branch_current_a=np.abs(j[1:]),
        losses_kw=losses_w / 1000.0,
        iterations=it,
    )


def approx_voltage_rise_pu(
    *,
    n_houses: int,
    length_m: float,
    cable: str,
    net_export_kw_per_house: float,
    q_kvar_per_house: float = 0.0,
    v_nominal_ll: float = 400.0,
) -> float:
    """
    Linearised end-of-feeder rise, ΔV/V ≈ Σ (R_k P_k + X_k Q_k) / V², for checking
    the sweep and for the lab's worked example. P, Q are the three-phase powers
    flowing toward the transformer through each segment.
    """
    spec = CABLES[cable]
    seg_km = float(length_m) / 1000.0 / n_houses
    r = spec["r_ohm_per_km"] * seg_km
    x = spec["x_ohm_per_km"] * seg_km
    total = 0.0
    for k in range(1, n_houses + 1):
        downstream = n_houses - k + 1
        total += (
            r * downstream * net_export_kw_per_house * 1000.0
            + x * downstream * q_kvar_per_house * 1000.0
        )
    return total / (v_nominal_ll**2)


def pv_shape(hour: int) -> float:
    """Clear-sky PV output as a fraction of peak (sunrise 6 h, sunset 20 h)."""
    if hour <= 6 or hour >= 20:
        return 0.0
    return max(0.0, math.sin(math.pi * (hour - 6) / 14.0)) ** 1.3


def load_shape(hour: int) -> float:
    """Residential demand as a fraction of the evening peak."""
    base = 0.30
    morning = 0.35 * math.exp(-((hour - 7.5) ** 2) / 2.0)
    evening = 0.70 * math.exp(-((hour - 19.5) ** 2) / 3.0)
    return min(1.0, base + morning + evening)


def feeder_day(
    *,
    n_houses: int,
    length_m: float,
    cable: str,
    pv_kw_peak: float,
    load_kw_peak: float,
    pv_power_factor: float = 1.0,
    v_source_pu: float = 1.0,
) -> dict[str, Any]:
    """
    Solve the feeder for every hour of a clear day and return the voltage
    profile along the feeder at the worst (highest-voltage) hour.
    """
    hours = list(range(24))
    v_max, v_min, loss = [], [], []
    worst_hour, worst = 0, None
    for h in hours:
        res = solve_feeder(
            n_houses=n_houses,
            length_m=length_m,
            cable=cable,
            pv_kw_per_house=pv_kw_peak * pv_shape(h),
            load_kw_per_house=load_kw_peak * load_shape(h),
            pv_power_factor=pv_power_factor,
            v_source_pu=v_source_pu,
        )
        v_max.append(res.v_max_pu)
        v_min.append(res.v_min_pu)
        loss.append(res.losses_kw)
        if worst is None or res.v_max_pu > worst.v_max_pu:
            worst, worst_hour = res, h
    assert worst is not None
    spec = CABLES[cable]
    return {
        "hours": hours,
        "v_max_pu": v_max,
        "v_min_pu": v_min,
        "losses_kw": loss,
        "worst_hour": worst_hour,
        "worst_profile_pu": worst.v_pu.tolist(),
        "distance_m": [float(length_m) * k / n_houses for k in range(n_houses + 1)],
        "worst_max_current_a": float(worst.branch_current_a.max()),
        "cable_i_max_a": float(spec["i_max_a"]),
        "day_max_pu": max(v_max),
        "day_min_pu": min(v_min),
        "hours_over_limit": sum(1 for v in v_max if v > V_MAX_PU),
        "hours_under_limit": sum(1 for v in v_min if v < V_MIN_PU),
        "energy_losses_kwh": float(sum(loss)),
    }
