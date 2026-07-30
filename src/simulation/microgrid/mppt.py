# Adapted from RenewableEnergySim (MIT) — nabilkhondaker/RenewableEnergySim
"""Perturb & Observe MPPT controller."""

from __future__ import annotations


class MPPTController:
    def __init__(self, step_size: float = 0.5, v_ref: float = 24.0) -> None:
        self.step_size = float(step_size)
        self.v_ref = float(v_ref)
        self.prev_p = 0.0
        self.prev_v = 0.0

    def optimize(self, v_current: float, i_current: float) -> float:
        """
        Update voltage reference from measured V, I (P&O).

        Returns new voltage reference (V).
        """
        v_current = float(v_current)
        i_current = float(i_current)
        p_current = v_current * i_current
        delta_p = p_current - self.prev_p
        delta_v = v_current - self.prev_v

        if delta_p != 0:
            if delta_p > 0:
                self.v_ref += self.step_size if delta_v > 0 else -self.step_size
            else:
                self.v_ref += -self.step_size if delta_v > 0 else self.step_size

        self.prev_p = p_current
        self.prev_v = v_current
        return self.v_ref
