# Adapted from RenewableEnergySim (MIT) — nabilkhondaker/RenewableEnergySim
"""Runtime BESS SOC simulator (not PuLP BatteryParams)."""

from __future__ import annotations


class BatteryESS:
    """Discrete-time battery energy storage for microgrid labs."""

    def __init__(
        self,
        capacity_kwh: float,
        max_charge_kw: float,
        efficiency: float = 0.95,
        initial_soc_frac: float = 0.5,
    ) -> None:
        if capacity_kwh <= 0:
            raise ValueError("capacity_kwh must be > 0")
        if max_charge_kw < 0:
            raise ValueError("max_charge_kw must be >= 0")
        if not 0.0 < efficiency <= 1.0:
            raise ValueError("efficiency must be in (0, 1]")
        self.capacity_wh = float(capacity_kwh) * 1000.0
        self.max_charge_w = float(max_charge_kw) * 1000.0
        self.efficiency = float(efficiency)
        frac = min(1.0, max(0.0, float(initial_soc_frac)))
        self.current_charge_wh = self.capacity_wh * frac

    def charge(self, power_w: float, dt_hours: float) -> float:
        """Charge with power_w (W). Returns unabsorbed excess power (W)."""
        power_w = max(0.0, float(power_w))
        dt_hours = float(dt_hours)
        if dt_hours <= 0 or power_w <= 0:
            return power_w
        available = self.capacity_wh - self.current_charge_wh
        max_input = min(power_w, self.max_charge_w)
        energy_to_add = max_input * dt_hours * self.efficiency
        if energy_to_add <= available:
            self.current_charge_wh += energy_to_add
            return power_w - max_input
        self.current_charge_wh = self.capacity_wh
        excess_energy = energy_to_add - available
        absorbed_w = max_input - (excess_energy / dt_hours / self.efficiency)
        return power_w - absorbed_w

    def discharge(self, required_power_w: float, dt_hours: float) -> float:
        """Discharge to meet required_power_w (W). Returns unmet deficit (W)."""
        required_power_w = max(0.0, float(required_power_w))
        dt_hours = float(dt_hours)
        if dt_hours <= 0 or required_power_w <= 0:
            return 0.0
        energy_needed = (required_power_w * dt_hours) / self.efficiency
        if self.current_charge_wh >= energy_needed:
            self.current_charge_wh -= energy_needed
            return 0.0
        provided = self.current_charge_wh
        self.current_charge_wh = 0.0
        deficit_energy = energy_needed - provided
        return (deficit_energy * self.efficiency) / dt_hours

    def get_soc(self) -> float:
        """State of charge in [0, 1]."""
        if self.capacity_wh <= 0:
            return 0.0
        return self.current_charge_wh / self.capacity_wh
