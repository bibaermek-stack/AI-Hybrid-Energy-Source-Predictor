# Adapted from RenewableEnergySim (MIT) — nabilkhondaker/RenewableEnergySim
"""Grid-tied inverter with load-dependent efficiency."""

from __future__ import annotations


def calculate_inverter_efficiency_curve(load_percentage: float) -> float:
    """Empirical η(load) peaking mid-load; low at light load."""
    load_percentage = float(load_percentage)
    if load_percentage <= 0.0:
        return 0.0
    efficiency = 0.98 - (0.05 / (load_percentage + 0.01)) - (0.01 * load_percentage)
    return max(0.0, min(0.98, efficiency))


class Inverter:
    def __init__(self, rated_power_kw: float) -> None:
        if rated_power_kw <= 0:
            raise ValueError("rated_power_kw must be > 0")
        self.rated_power_kw = float(rated_power_kw)

    def convert_dc_to_ac(self, dc_power_kw: float) -> float:
        """Convert DC kW to AC kW with overload clip at 110% rated."""
        dc_power_kw = float(dc_power_kw)
        if dc_power_kw <= 0:
            return 0.0
        load_percentage = dc_power_kw / self.rated_power_kw
        if load_percentage > 1.1:
            dc_power_kw = self.rated_power_kw * 1.1
            load_percentage = 1.1
        return dc_power_kw * calculate_inverter_efficiency_curve(load_percentage)
