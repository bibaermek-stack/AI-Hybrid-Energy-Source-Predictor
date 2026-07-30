"""
Multi-objective weights for hybrid energy dispatch.

Modes map to (weight_profit, weight_co2) used by HybridEnergyOptimizer.
"""

from __future__ import annotations

from typing import Literal, Mapping

ModeName = Literal["max_profit", "min_co2", "balanced"]

MODE_WEIGHTS: Mapping[str, tuple[float, float]] = {
    "max_profit": (1.0, 0.0),
    "min_co2": (0.0, 1.0),
    "balanced": (0.5, 0.5),
}


def resolve_weights(
    mode: str = "balanced",
    weight_profit: float | None = None,
    weight_co2: float | None = None,
) -> tuple[float, float]:
    """
    Return (w_profit, w_co2) for the scalarized objective:

        maximize  w_profit * profit - w_co2 * co2_scaled
    """
    mode = (mode or "balanced").lower().strip()
    if mode not in MODE_WEIGHTS:
        raise ValueError(
            f"Unknown mode '{mode}'. Use max_profit | min_co2 | balanced"
        )
    w_p, w_c = MODE_WEIGHTS[mode]
    if weight_profit is not None:
        w_p = float(weight_profit)
        if w_p < 0:
            raise ValueError("weight_profit must be >= 0")
    if weight_co2 is not None:
        w_c = float(weight_co2)
        if w_c < 0:
            raise ValueError("weight_co2 must be >= 0")
    if w_p + w_c <= 1e-15:
        raise ValueError("At least one weight must be > 0")
    return w_p, w_c


def describe_mode(mode: str, lang: str = "en") -> str:
    mode = (mode or "balanced").lower()
    texts = {
        "max_profit": {
            "en": "Maximize economic profit from grid arbitrage / export.",
            "kk": "Grid сату/сатып алу арқылы экономикалық пайданы максимумдау.",
        },
        "min_co2": {
            "en": "Minimize CO₂ by reducing grid imports.",
            "kk": "Grid import-ты азайтып CO₂-ні минимумдау.",
        },
        "balanced": {
            "en": "Balance profit and carbon (equal weights by default).",
            "kk": "Пайда мен көміртекті теңестіру (әдепкі салмақ тең).",
        },
    }
    lang = "kk" if lang == "kk" else "en"
    return texts.get(mode, texts["balanced"])[lang]
