"""
Community / shared-energy simulation helpers.

Concepts adapted from CACER_Simulator (BSD-3-Clause, RSE) — pure functions only,
no Excel/xlwings/Italian market engine. See ``third_party/NOTICE.md``.
"""

from src.simulation.community.bess_step import BessStepResult, bess_step, simulate_bess_series
from src.simulation.community.cacer_path import get_cacer_root, sim_cacer_status
from src.simulation.community.financial_kpis import community_project_kpis, irr
from src.simulation.community.load_profile import scale_profile, synthetic_load_profile
from src.simulation.community.shared_energy import run_shared_energy_day

__all__ = [
    "BessStepResult",
    "bess_step",
    "simulate_bess_series",
    "synthetic_load_profile",
    "scale_profile",
    "run_shared_energy_day",
    "community_project_kpis",
    "irr",
    "get_cacer_root",
    "sim_cacer_status",
]
