"""Apply design-token-aligned Plotly theming to figures."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from dashboard.styles.tokens import plotly_layout_defaults


def apply_theme(fig: go.Figure, theme: str = "Dark", **layout_overrides: Any) -> go.Figure:
    """
    Mutate and return ``fig`` with EcoPredict layout defaults.

    Parameters
    ----------
    fig :
        Plotly figure.
    theme :
        ``Dark`` or ``Light`` (or session theme string).
    layout_overrides :
        Passed to ``fig.update_layout``.
    """
    base = plotly_layout_defaults(theme)
    base.update(layout_overrides)
    fig.update_layout(**base)
    return fig


def themed_line(
    x: list | tuple,
    series: dict[str, list | tuple],
    *,
    title: str = "",
    y_title: str = "",
    theme: str = "Dark",
) -> go.Figure:
    """Multi-series line chart with design tokens."""
    fig = go.Figure()
    for name, y in series.items():
        fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", name=name))
    return apply_theme(
        fig,
        theme,
        title=title or None,
        yaxis_title=y_title or None,
        height=400,
    )
