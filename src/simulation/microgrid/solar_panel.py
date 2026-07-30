# Adapted from RenewableEnergySim (MIT) — nabilkhondaker/RenewableEnergySim
"""PV array physics for education labs."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class SolarPanelConfig:
    """Single-panel parameters."""

    area: float = 1.6  # m²
    efficiency: float = 0.20
    temp_coefficient: float = 0.004  # relative loss per °C above 25
    nominal_voltage: float = 36.0  # V


class SolarArray:
    """Array of identical panels."""

    def __init__(self, config: SolarPanelConfig, num_panels: int) -> None:
        if num_panels < 1:
            raise ValueError("num_panels must be >= 1")
        self.config = config
        self.num_panels = int(num_panels)
        self.total_area = config.area * self.num_panels

    def calculate_power(self, irradiance: float, temp_c: float) -> float:
        """
        DC power output (W) from plane irradiance (W/m²) and ambient temp (°C).
        """
        irradiance = float(irradiance)
        if irradiance <= 0:
            return 0.0
        temp_loss = max(0.0, (float(temp_c) - 25.0) * self.config.temp_coefficient)
        actual_efficiency = self.config.efficiency * (1.0 - temp_loss)
        if actual_efficiency < 0:
            actual_efficiency = 0.0
        return actual_efficiency * self.total_area * irradiance

    def get_iv_curve(self, irradiance: float) -> tuple[np.ndarray, np.ndarray]:
        """Simplified I–V curve for MPPT teaching (V, I)."""
        irradiance = max(0.0, float(irradiance))
        v = np.linspace(0, self.config.nominal_voltage * 1.2, 100)
        i_sc = (irradiance / 1000.0) * 8.5
        i = i_sc - 1e-7 * (np.exp(v / 2.5) - 1)
        i = np.maximum(i, 0.0)
        return v, i
