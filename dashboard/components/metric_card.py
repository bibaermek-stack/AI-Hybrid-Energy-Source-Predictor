"""Reusable metric card component."""

from __future__ import annotations

from html import escape
from typing import Literal

import streamlit as st

from dashboard.components.ui_kit import _html

Variant = Literal["solar", "wind", "total", "default", "success", "warn", "danger"]


def metric_card(
    label: str,
    value: str,
    *,
    hint: str | None = None,
    icon: str = "◆",
    variant: Variant = "default",
) -> None:
    """
    Glass-style metric card.

    Parameters
    ----------
    label :
        Short metric name.
    value :
        Formatted primary value (include unit in the string if needed).
    hint :
        Optional secondary line.
    icon :
        Single character / short emoji.
    variant :
        Color accent: solar | wind | total | default | success | warn | danger.
    """
    hint_html = f'<div class="ep-card-hint">{escape(hint)}</div>' if hint else ""
    _html(
        f"""
        <div class="ep-card ep-metric-card">
          <div class="ep-card-label"><span>{escape(icon)}</span>{escape(label)}</div>
          <div class="ep-card-value ep-card-value--{variant}">{escape(value)}</div>
          {hint_html}
        </div>
        """
    )


def metric_row(items: list[dict]) -> None:
    """
    Render a horizontal row of metric cards.

    Each item: ``{label, value, icon?, variant?, hint?}``.
    """
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            metric_card(
                item.get("label", ""),
                item.get("value", "—"),
                hint=item.get("hint"),
                icon=item.get("icon", "◆"),
                variant=item.get("variant", "default"),  # type: ignore[arg-type]
            )
