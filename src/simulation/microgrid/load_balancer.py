# Adapted from RenewableEnergySim (MIT) — nabilkhondaker/RenewableEnergySim
"""Heuristic PV–battery–grid dispatch for labs."""

from __future__ import annotations

from typing import Any

from src.simulation.microgrid.battery_ess import BatteryESS
from src.simulation.microgrid.inverter import Inverter


class LoadBalancer:
    """Priority: meet load, then charge battery, then export; import residual."""

    def __init__(self, inverter: Inverter, battery: BatteryESS) -> None:
        self.inverter = inverter
        self.battery = battery

    def dispatch(self, pv_dc_kw: float, demand_ac_kw: float, dt_hours: float = 1.0) -> dict[str, Any]:
        """
        Balance PV (DC kW), load (AC kW), battery, and grid for one timestep.
        """
        pv_dc_kw = max(0.0, float(pv_dc_kw))
        demand_ac_kw = max(0.0, float(demand_ac_kw))
        dt_hours = float(dt_hours)

        pv_ac_kw = self.inverter.convert_dc_to_ac(pv_dc_kw)
        net_power = pv_ac_kw - demand_ac_kw
        grid_import_kw = 0.0
        grid_export_kw = 0.0
        battery_charge_kw = 0.0
        battery_discharge_kw = 0.0

        if net_power > 0:
            excess_dc = net_power * 0.95  # rectifier-ish loss for AC-coupled charge
            unabsorbed_dc = self.battery.charge(excess_dc * 1000.0, dt_hours) / 1000.0
            absorbed = excess_dc - unabsorbed_dc
            battery_charge_kw = max(0.0, absorbed)
            grid_export_kw = max(0.0, unabsorbed_dc * 0.95)
        elif net_power < 0:
            deficit_dc = abs(net_power) / 0.95
            unmet_dc = self.battery.discharge(deficit_dc * 1000.0, dt_hours) / 1000.0
            served = deficit_dc - unmet_dc
            battery_discharge_kw = max(0.0, served)
            grid_import_kw = max(0.0, unmet_dc / 0.95)

        return {
            "pv_dc_kw": pv_dc_kw,
            "pv_ac_kw": pv_ac_kw,
            "load_kw": demand_ac_kw,
            "grid_import_kw": grid_import_kw,
            "grid_export_kw": grid_export_kw,
            "battery_charge_kw": battery_charge_kw,
            "battery_discharge_kw": battery_discharge_kw,
            "battery_soc": self.battery.get_soc(),
        }
