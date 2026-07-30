"""
Battery energy storage system (BESS) model for hybrid dispatch.

Used by :class:`src.optimization.hybrid_optimizer.HybridEnergyOptimizer`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _validate_nonneg(name: str, value: float) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{name} must be numeric, got {type(value).__name__}")
    value = float(value)
    if math.isnan(value) or math.isinf(value):
        raise ValueError(f"{name} contains NaN or Inf: {value}")
    if value < 0:
        raise ValueError(f"{name} cannot be negative: {value}")
    return value


@dataclass
class BatteryParams:
    """Battery energy storage system (BESS) parameters."""

    capacity_kwh: float = 100.0
    max_charge_kw: float = 50.0
    max_discharge_kw: float = 50.0
    efficiency: float = 0.95
    """One-way charge/discharge efficiency (round-trip ≈ efficiency²)."""
    initial_soc_kwh: float | None = None
    """Initial energy (kWh). Defaults to 50% of capacity."""
    min_soc_frac: float = 0.05
    max_soc_frac: float = 0.95

    def __post_init__(self) -> None:
        self.capacity_kwh = _validate_nonneg("capacity_kwh", self.capacity_kwh)
        self.max_charge_kw = _validate_nonneg("max_charge_kw", self.max_charge_kw)
        self.max_discharge_kw = _validate_nonneg("max_discharge_kw", self.max_discharge_kw)
        self.efficiency = float(self.efficiency)
        if not 0.0 < self.efficiency <= 1.0:
            raise ValueError("efficiency must be in (0, 1]")
        if self.initial_soc_kwh is None:
            self.initial_soc_kwh = 0.5 * self.capacity_kwh
        else:
            self.initial_soc_kwh = _validate_nonneg("initial_soc_kwh", self.initial_soc_kwh)
        if not 0.0 <= self.min_soc_frac < self.max_soc_frac <= 1.0:
            raise ValueError("Require 0 <= min_soc_frac < max_soc_frac <= 1")
        if self.initial_soc_kwh > self.capacity_kwh + 1e-9:
            raise ValueError("initial_soc_kwh cannot exceed capacity_kwh")

    @property
    def soc_min_kwh(self) -> float:
        return self.min_soc_frac * self.capacity_kwh

    @property
    def soc_max_kwh(self) -> float:
        return self.max_soc_frac * self.capacity_kwh

    def clamp_soc(self, soc_kwh: float) -> float:
        return min(max(float(soc_kwh), self.soc_min_kwh), self.soc_max_kwh)
