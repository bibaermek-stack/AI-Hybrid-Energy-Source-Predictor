"""
CO₂ and environmental equivalent calculators.

Default grid emission factor tuned for Kazakhstan-like grids (~0.45–0.65 kg/kWh).
"""

from __future__ import annotations

# kg CO2 per kWh for grid electricity (approximate regional default)
DEFAULT_GRID_KG_PER_KWH = 0.45
# Rough rule of thumb: one mature tree absorbs ~21 kg CO2 / year
KG_CO2_PER_TREE_YEAR = 21.0


def co2_avoided_kg(
    renewable_kwh: float,
    grid_factor_kg_per_kwh: float = DEFAULT_GRID_KG_PER_KWH,
    residual_import_kwh: float = 0.0,
) -> float:
    """
    CO₂ avoided by using renewable energy instead of grid power.

    ``residual_import_kwh`` is still attributed as emitted (not avoided).
    """
    renewable_kwh = max(0.0, float(renewable_kwh))
    residual_import_kwh = max(0.0, float(residual_import_kwh))
    avoided = renewable_kwh * float(grid_factor_kg_per_kwh)
    emitted = residual_import_kwh * float(grid_factor_kg_per_kwh)
    return max(0.0, avoided - 0.0 * emitted)  # avoided is gross from renewables


def co2_emitted_from_grid(
    grid_import_kwh: float,
    grid_factor_kg_per_kwh: float = DEFAULT_GRID_KG_PER_KWH,
) -> float:
    return max(0.0, float(grid_import_kwh)) * float(grid_factor_kg_per_kwh)


def trees_equivalent(co2_kg: float, kg_per_tree_year: float = KG_CO2_PER_TREE_YEAR) -> float:
    """Years of tree absorption equivalent for given CO₂ mass."""
    if kg_per_tree_year <= 0:
        return 0.0
    return max(0.0, float(co2_kg)) / float(kg_per_tree_year)


def cars_off_road_equivalent(co2_kg: float, kg_per_car_year: float = 4600.0) -> float:
    """Very rough passenger-car annual emission equivalent."""
    if kg_per_car_year <= 0:
        return 0.0
    return max(0.0, float(co2_kg)) / float(kg_per_car_year)
