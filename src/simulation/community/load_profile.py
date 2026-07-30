"""Synthetic domestic load profiles for education labs (CACER-inspired, simplified)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def synthetic_load_profile(
    hours: int = 24,
    *,
    base_kw: float = 0.8,
    morning_peak_kw: float = 2.0,
    evening_peak_kw: float = 3.5,
    noise_pct: float = 5.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Build an hourly load shape with morning/evening peaks.

    Returns DataFrame columns: ``hour``, ``load_kw``.
    """
    hours = int(hours)
    if hours < 1:
        raise ValueError("hours must be >= 1")
    rng = np.random.default_rng(seed)
    t = np.arange(hours) % 24
    # Base + peaks (Gaussian bumps)
    load = np.full(hours, float(base_kw), dtype=float)
    load += float(morning_peak_kw - base_kw) * np.exp(-0.5 * ((t - 8) / 1.5) ** 2)
    load += float(evening_peak_kw - base_kw) * np.exp(-0.5 * ((t - 19) / 2.0) ** 2)
    # Night valley
    load *= np.where((t >= 0) & (t < 5), 0.55, 1.0)
    noise = 1.0 + (float(noise_pct) / 100.0) * rng.normal(0, 1, size=hours)
    load = np.maximum(0.05, load * noise)
    return pd.DataFrame({"hour": np.arange(hours), "load_kw": load})


def scale_profile(df: pd.DataFrame, peak_kw: float) -> pd.DataFrame:
    """Rescale so max load equals ``peak_kw``."""
    out = df.copy()
    m = float(out["load_kw"].max())
    if m <= 0:
        return out
    out["load_kw"] = out["load_kw"] * (float(peak_kw) / m)
    return out
