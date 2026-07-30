"""Prediction / dispatch result card."""

from __future__ import annotations

from html import escape
from typing import Any

import streamlit as st

from dashboard.components.ui_kit import _html


def prediction_card(
    *,
    title: str,
    recommendation: str,
    solar_kw: float | None = None,
    wind_kw: float | None = None,
    total_kw: float | None = None,
    reliability: float | None = None,
    extra_rows: list[tuple[str, str]] | None = None,
) -> None:
    """
    Card summarizing a hybrid prediction / dispatch result.

    Parameters
    ----------
    title :
        Card heading.
    recommendation :
        Primary recommendation label (Solar / Wind / Hybrid).
    solar_kw, wind_kw, total_kw :
        Optional power values.
    reliability :
        Optional 0–1 reliability index.
    extra_rows :
        Optional (label, value) pairs.
    """
    rows_html = ""
    if solar_kw is not None:
        rows_html += _row("Solar", f"{float(solar_kw):.2f} kW")
    if wind_kw is not None:
        rows_html += _row("Wind", f"{float(wind_kw):.2f} kW")
    if total_kw is not None:
        rows_html += _row("Total", f"{float(total_kw):.2f} kW")
    if reliability is not None:
        rows_html += _row("Reliability", f"{float(reliability) * 100:.1f}%")
    for lab, val in extra_rows or []:
        rows_html += _row(lab, val)

    _html(
        f"""
        <div class="ep-card ep-prediction-card">
          <div class="ep-card-label">{escape(title)}</div>
          <div class="ep-prediction-rec">{escape(recommendation)}</div>
          <div class="ep-prediction-rows">{rows_html}</div>
        </div>
        """
    )


def prediction_metrics(
    solar_kw: float,
    wind_kw: float,
    total_kw: float,
    recommendation: str,
    *,
    lang: str = "en",
) -> None:
    """Native Streamlit metrics + recommendation banner."""
    c1, c2, c3 = st.columns(3)
    c1.metric("Solar" if lang != "kk" else "Күн", f"{solar_kw:.2f} kW")
    c2.metric("Wind" if lang != "kk" else "Жел", f"{wind_kw:.2f} kW")
    c3.metric("Total" if lang != "kk" else "Жиын", f"{total_kw:.2f} kW")
    st.success(
        (f"Recommended: **{recommendation}**" if lang != "kk" else f"Ұсыныс: **{recommendation}**")
    )


def _row(label: str, value: str) -> str:
    return (
        f'<div class="ep-prediction-row">'
        f'<span class="ep-prediction-k">{escape(label)}</span>'
        f'<span class="ep-prediction-v">{escape(value)}</span>'
        f"</div>"
    )


def result_from_dict(data: dict[str, Any], *, title: str = "Result") -> None:
    """Build a prediction card from a loose dict (API / optimizer output)."""
    prediction_card(
        title=title,
        recommendation=str(
            data.get("recommendation")
            or data.get("recommended_source")
            or data.get("status")
            or "—"
        ),
        solar_kw=_maybe_float(data.get("solar_kw") or data.get("solar")),
        wind_kw=_maybe_float(data.get("wind_kw") or data.get("wind")),
        total_kw=_maybe_float(data.get("total_kw") or data.get("total")),
        reliability=_maybe_float(data.get("reliability")),
    )


def _maybe_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None
