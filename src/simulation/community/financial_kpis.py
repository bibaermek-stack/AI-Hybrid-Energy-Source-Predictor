"""Community / project financial KPIs for labs (wrap EcoPradict sustainability)."""

from __future__ import annotations

from typing import Any

from src.sustainability.economic_metrics import lcoe, npv, payback_years, project_economics, roi_percent


def irr(cashflows: list[float], guess: float = 0.1, tol: float = 1e-6, max_iter: int = 100) -> float:
    """
    Internal rate of return via Newton method on NPV(r)=0.

    Returns float('nan') if no convergence.
    """
    if not cashflows:
        return float("nan")
    r = float(guess)
    for _ in range(max_iter):
        npv_v = 0.0
        d_npv = 0.0
        for t, cf in enumerate(cashflows):
            den = (1.0 + r) ** t
            npv_v += float(cf) / den
            if t > 0:
                d_npv -= t * float(cf) / ((1.0 + r) ** (t + 1))
        if abs(d_npv) < 1e-12:
            break
        r_new = r - npv_v / d_npv
        if abs(r_new - r) < tol:
            return r_new
        r = r_new
    return float("nan")


def community_project_kpis(
    *,
    capex: float,
    annual_generation_kwh: float,
    price_per_kwh: float,
    opex_annual: float = 0.0,
    lifetime_years: int = 20,
    discount_rate: float = 0.05,
) -> dict[str, Any]:
    """
    Bundle LCOE / payback / ROI / NPV / IRR for a simplified community PV project.

    Cash-flow model: t=0 → -capex; t=1..N → annual net savings.
    """
    base = project_economics(
        capex=capex,
        annual_kwh=annual_generation_kwh,
        price_per_kwh=price_per_kwh,
        opex_annual=opex_annual,
        lifetime_years=lifetime_years,
        discount_rate=discount_rate,
    )
    annual_net = float(base["annual_net_savings"])
    cfs = [-float(capex)] + [annual_net] * int(lifetime_years)
    return {
        **base,
        "npv": npv(cfs, discount_rate),
        "irr": irr(cfs),
        "irr_pct": (irr(cfs) * 100.0) if irr(cfs) == irr(cfs) else float("nan"),
        "lcoe_check": lcoe(
            capex, annual_generation_kwh, opex_annual, lifetime_years, discount_rate
        ),
        "payback_years": payback_years(capex, annual_net),
        "roi_percent_lifetime": roi_percent(
            annual_net * lifetime_years - float(capex), capex
        ),
    }
