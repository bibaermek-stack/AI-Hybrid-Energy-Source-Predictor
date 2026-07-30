# Concept adapted from CACER_Simulator Functions_Energy_Model.BESS (BSD-3-Clause)
"""Single-timestep BESS update with DoD limits and half-cycle efficiency."""

from __future__ import annotations

from typing import NamedTuple


class BessStepResult(NamedTuple):
    e_terminal_real_kwh: float
    e_loss_kwh: float
    e_discharge_net_kwh: float
    soc_kwh: float
    soc_frac: float


def bess_step(
    e_terminal_theor_kwh: float,
    soc_kwh_tm1: float,
    *,
    eta_halfcycle: float = 0.95,
    battery_min_kwh: float = 0.0,
    battery_max_kwh: float = 100.0,
    flag_battery_to_grid: int = 0,
    battery_to_grid_capacity_kwh: float = 0.0,
) -> BessStepResult:
    """
    Simplified BESS energy step (no voltage / C-rate physics).

    Sign convention for ``e_terminal_theor_kwh``:
    positive = charge intention, negative = discharge intention.
    """
    eta = float(eta_halfcycle)
    if not 0.0 < eta <= 1.0:
        raise ValueError("eta_halfcycle must be in (0, 1]")
    bmin = float(battery_min_kwh)
    bmax = float(battery_max_kwh)
    if bmax <= bmin:
        raise ValueError("battery_max_kwh must be > battery_min_kwh")

    e = float(e_terminal_theor_kwh)
    soc0 = float(soc_kwh_tm1)
    e_charge_theor_gross = max(0.0, e)
    e_discharge_theor_gross = min(
        0.0, e - float(battery_to_grid_capacity_kwh) * int(flag_battery_to_grid)
    )
    e_half_theor = e_charge_theor_gross * eta + e_discharge_theor_gross / eta

    if soc0 + e_half_theor > bmax:
        soc1 = bmax
    elif soc0 + e_half_theor <= bmin:
        soc1 = bmin
    else:
        soc1 = soc0 + e_half_theor

    soc_frac = soc1 / bmax
    e_half_real = soc1 - soc0
    e_charge_real_net = max(0.0, e_half_real)
    e_charge_real_brut = e_charge_real_net / eta if eta > 0 else 0.0
    e_discharge_real_brut = min(0.0, e_half_real)
    e_discharge_real_net = e_discharge_real_brut * eta

    e_terminal_real = e_charge_real_brut + e_discharge_real_net
    e_loss = abs(e_charge_real_net - e_charge_real_brut) + abs(
        e_discharge_real_brut - e_discharge_real_net
    )

    return BessStepResult(
        e_terminal_real_kwh=e_terminal_real,
        e_loss_kwh=e_loss,
        e_discharge_net_kwh=e_discharge_real_net,
        soc_kwh=soc1,
        soc_frac=soc_frac,
    )


def simulate_bess_series(
    net_energy_kwh: list[float] | tuple[float, ...],
    *,
    capacity_kwh: float = 50.0,
    dod: float = 0.8,
    eta_halfcycle: float = 0.95,
    initial_soc_frac: float = 0.5,
) -> list[BessStepResult]:
    """
    Apply ``bess_step`` over a series of terminal energy intents (kWh).

    ``net_energy_kwh[t] > 0`` means surplus available to charge;
    ``< 0`` means deficit to discharge.
    """
    bmax = float(capacity_kwh)
    bmin = bmax * (1.0 - float(dod))
    soc = bmax * float(initial_soc_frac)
    out: list[BessStepResult] = []
    for e in net_energy_kwh:
        r = bess_step(
            float(e),
            soc,
            eta_halfcycle=eta_halfcycle,
            battery_min_kwh=bmin,
            battery_max_kwh=bmax,
        )
        soc = r.soc_kwh
        out.append(r)
    return out
