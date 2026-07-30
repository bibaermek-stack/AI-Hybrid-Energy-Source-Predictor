"""Shared Plotly chart helpers."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def style_fig(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        legend=dict(orientation="h"),
    )
    return fig


def bar_solar_wind(solar: float, wind: float, labels: dict) -> None:
    fig = px.bar(
        {labels.get("x", "Source"): [labels.get("solar", "Solar"), labels.get("wind", "Wind")],
         labels.get("y", "Power (kW)"): [solar, wind]},
        x=labels.get("x", "Source"),
        y=labels.get("y", "Power (kW)"),
        color=labels.get("x", "Source"),
        color_discrete_map={
            labels.get("solar", "Solar"): "#FDB462",
            labels.get("wind", "Wind"): "#80B1D3",
        },
        title=labels.get("title", "Energy comparison"),
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)
