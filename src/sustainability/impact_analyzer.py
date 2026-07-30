"""
Combine energy, CO₂, and economic metrics into a single impact report.
"""

from __future__ import annotations

from typing import Any

from src.sustainability.co2_calculator import (
    DEFAULT_GRID_KG_PER_KWH,
    cars_off_road_equivalent,
    co2_avoided_kg,
    co2_emitted_from_grid,
    trees_equivalent,
)
from src.sustainability.economic_metrics import project_economics


def analyze_impact(
    renewable_kwh: float,
    grid_import_kwh: float = 0.0,
    grid_factor_kg_per_kwh: float = DEFAULT_GRID_KG_PER_KWH,
    *,
    capex: float | None = None,
    price_per_kwh: float = 0.12,
    opex_annual: float = 0.0,
    lifetime_years: int = 25,
    lang: str = "en",
) -> dict[str, Any]:
    """
    Build a structured sustainability impact summary.

    ``renewable_kwh`` can be daily or annual — label it via meta if needed.
    When ``capex`` is set, economic block is included (treat kWh as annual).
    """
    renewable_kwh = max(0.0, float(renewable_kwh))
    grid_import_kwh = max(0.0, float(grid_import_kwh))
    avoided = co2_avoided_kg(renewable_kwh, grid_factor_kg_per_kwh)
    emitted = co2_emitted_from_grid(grid_import_kwh, grid_factor_kg_per_kwh)
    net_co2 = max(0.0, avoided - emitted)

    report: dict[str, Any] = {
        "energy": {
            "renewable_kwh": renewable_kwh,
            "grid_import_kwh": grid_import_kwh,
            "self_sufficiency_pct": (
                100.0 * renewable_kwh / (renewable_kwh + grid_import_kwh)
                if (renewable_kwh + grid_import_kwh) > 0
                else 0.0
            ),
        },
        "carbon": {
            "grid_factor_kg_per_kwh": grid_factor_kg_per_kwh,
            "co2_avoided_kg": avoided,
            "co2_emitted_kg": emitted,
            "co2_net_benefit_kg": net_co2,
            "trees_year_equiv": trees_equivalent(net_co2),
            "cars_year_equiv": cars_off_road_equivalent(net_co2),
        },
    }

    if capex is not None:
        report["economics"] = project_economics(
            capex=float(capex),
            annual_kwh=renewable_kwh,
            price_per_kwh=price_per_kwh,
            opex_annual=opex_annual,
            lifetime_years=lifetime_years,
        )

    if lang == "kk":
        report["narrative"] = (
            f"Жаңартылатын энергия {renewable_kwh:.1f} кВт·сағ; "
            f"CO₂ пайдасы ≈ {net_co2:.1f} кг "
            f"(~{trees_equivalent(net_co2):.1f} ағаш·жыл)."
        )
    else:
        report["narrative"] = (
            f"Renewable energy {renewable_kwh:.1f} kWh; "
            f"net CO₂ benefit ≈ {net_co2:.1f} kg "
            f"(~{trees_equivalent(net_co2):.1f} tree-years)."
        )
    return report
