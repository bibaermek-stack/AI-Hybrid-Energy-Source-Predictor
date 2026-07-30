"""
Economic sustainability metrics: LCOE, ROI, simple payback.
"""

from __future__ import annotations

from typing import Any


def lcoe(
    capex: float,
    annual_generation_kwh: float,
    opex_annual: float = 0.0,
    lifetime_years: float = 25.0,
    discount_rate: float = 0.05,
) -> float:
    """
    Levelized cost of energy ($/kWh) with simple annuity discounting.

    LCOE ≈ (capex * CRF + opex) / annual_generation
    where CRF = r(1+r)^n / ((1+r)^n - 1)
    """
    annual_generation_kwh = float(annual_generation_kwh)
    if annual_generation_kwh <= 0:
        return float("inf")
    r = float(discount_rate)
    n = float(lifetime_years)
    if r <= 0 or n <= 0:
        annualized_capex = float(capex) / max(n, 1.0)
    else:
        crf = r * (1 + r) ** n / ((1 + r) ** n - 1)
        annualized_capex = float(capex) * crf
    return (annualized_capex + float(opex_annual)) / annual_generation_kwh


def roi_percent(
    net_profit: float,
    investment: float,
) -> float:
    """Simple ROI = net_profit / investment * 100."""
    investment = float(investment)
    if abs(investment) < 1e-12:
        return 0.0
    return 100.0 * float(net_profit) / investment


def payback_years(
    investment: float,
    annual_savings: float,
) -> float:
    """Simple payback period in years (no discounting)."""
    annual_savings = float(annual_savings)
    if annual_savings <= 0:
        return float("inf")
    return max(0.0, float(investment)) / annual_savings


def npv(
    cashflows: list[float],
    discount_rate: float = 0.05,
) -> float:
    """Net present value of a cash-flow series (t=0..T-1)."""
    r = float(discount_rate)
    total = 0.0
    for t, cf in enumerate(cashflows):
        total += float(cf) / ((1 + r) ** t)
    return total


def project_economics(
    capex: float,
    annual_kwh: float,
    price_per_kwh: float,
    opex_annual: float = 0.0,
    lifetime_years: int = 25,
    discount_rate: float = 0.05,
) -> dict[str, Any]:
    """Bundle of LCOE / ROI / payback for education and dashboard."""
    revenue = float(annual_kwh) * float(price_per_kwh)
    savings = revenue - float(opex_annual)
    lc = lcoe(capex, annual_kwh, opex_annual, lifetime_years, discount_rate)
    pb = payback_years(capex, savings)
    # cumulative profit over lifetime (undiscounted) for simple ROI
    lifetime_profit = savings * lifetime_years - float(capex)
    return {
        "lcoe": lc,
        "annual_revenue": revenue,
        "annual_net_savings": savings,
        "payback_years": pb,
        "roi_percent_lifetime": roi_percent(lifetime_profit, capex),
        "lifetime_years": lifetime_years,
        "price_per_kwh": price_per_kwh,
    }
