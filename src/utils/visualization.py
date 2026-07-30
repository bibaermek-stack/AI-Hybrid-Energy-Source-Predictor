"""
Shared Plotly helpers for forecasting, optimization, and sustainability charts.
"""

from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go


def line_series(
    x: Sequence,
    y: Sequence,
    name: str = "series",
    title: str = "",
    y_title: str = "",
    x_title: str = "",
) -> go.Figure:
    fig = go.Figure(go.Scatter(x=list(x), y=list(y), mode="lines+markers", name=name))
    fig.update_layout(
        title=title or None,
        xaxis_title=x_title or None,
        yaxis_title=y_title or None,
        template="plotly_white",
        margin=dict(l=40, r=20, t=50, b=40),
        height=360,
    )
    return fig


def multi_line(
    x: Sequence,
    series: dict[str, Sequence],
    title: str = "",
    y_title: str = "",
) -> go.Figure:
    fig = go.Figure()
    for name, y in series.items():
        fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", name=name))
    fig.update_layout(
        title=title or None,
        yaxis_title=y_title or None,
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=20, t=50, b=40),
        height=400,
    )
    return fig


def stacked_bars(
    categories: Sequence[str],
    series: dict[str, Sequence[float]],
    title: str = "",
    y_title: str = "kWh",
) -> go.Figure:
    fig = go.Figure()
    for name, values in series.items():
        fig.add_trace(go.Bar(name=name, x=list(categories), y=list(values)))
    fig.update_layout(
        barmode="stack",
        title=title or None,
        yaxis_title=y_title,
        template="plotly_white",
        height=400,
    )
    return fig


def gauge_metric(
    value: float,
    title: str,
    max_value: float = 100.0,
    suffix: str = "",
) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(value),
            number={"suffix": suffix},
            title={"text": title},
            gauge={
                "axis": {"range": [0, max_value]},
                "bar": {"color": "#2ecc71"},
                "steps": [
                    {"range": [0, max_value * 0.5], "color": "#ecf0f1"},
                    {"range": [max_value * 0.5, max_value * 0.8], "color": "#d5f5e3"},
                ],
            },
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
    return fig
