"""
Overview / Home Dashboard Page for NiceGUI.
"""

from nicegui import ui
import plotly.graph_objects as go
from nicegui_app.state import state
from nicegui_app.components.metric_card import build_metric_card


def render_overview_page():
    """Render home overview page."""
    with ui.column().classes("w-full gap-6 p-4"):
        # Hero banner
        with ui.card().classes("w-full p-6 rounded-2xl bg-gradient-to-r from-blue-900 via-indigo-900 to-teal-800 text-white shadow-lg"):
            ui.label(state.text("ov_title")).classes("text-2xl font-extrabold")
            ui.label(state.text("ov_subtitle")).classes("text-sm text-blue-200 mt-1")

        # KPI Metric Grid
        with ui.grid().classes("w-full grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4"):
            build_metric_card(
                title=state.text("ov_kpi_solar"),
                value="620.4",
                unit="kW",
                icon="wb_sunny",
                color="text-amber-500",
                subtitle="Peak irradiance @ 13:00",
            )
            build_metric_card(
                title=state.text("ov_kpi_wind"),
                value="310.8",
                unit="kW",
                icon="air",
                color="text-teal-500",
                subtitle="Avg speed 6.5 m/s",
            )
            build_metric_card(
                title=state.text("ov_kpi_load"),
                value="450.0",
                unit="kW",
                icon="power",
                color="text-pink-500",
                subtitle="System demand",
            )
            build_metric_card(
                title=state.text("ov_kpi_battery"),
                value="82.5",
                unit="%",
                icon="battery_charging_full",
                color="text-emerald-500",
                subtitle="200 kWh capacity",
            )

        # Plotly Generation Curve Chart
        with ui.card().classes("w-full p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label("📊 24-Hour Hybrid Power Generation & Load Profile").classes("text-base font-bold text-gray-800 dark:text-white mb-2")

            hours = list(range(24))
            solar_curve = [0, 0, 0, 0, 0, 20, 120, 320, 580, 750, 850, 890, 920, 880, 780, 610, 390, 180, 40, 0, 0, 0, 0, 0]
            wind_curve = [210, 240, 280, 310, 290, 260, 220, 190, 180, 200, 230, 250, 270, 290, 310, 340, 380, 410, 390, 320, 280, 250, 230, 220]
            load_curve = [350, 320, 300, 290, 310, 380, 480, 550, 620, 600, 580, 590, 610, 630, 640, 620, 590, 560, 520, 480, 440, 410, 380, 360]

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hours, y=solar_curve, mode="lines", name="Solar Power (kW)", line=dict(color="#F59E0B", width=3)))
            fig.add_trace(go.Scatter(x=hours, y=wind_curve, mode="lines", name="Wind Power (kW)", line=dict(color="#14B8A6", width=3)))
            fig.add_trace(go.Scatter(x=hours, y=load_curve, mode="lines", name="Load Demand (kW)", line=dict(color="#EC4899", width=2, dash="dash")))

            fig.update_layout(
                margin=dict(l=40, r=20, t=20, b=40),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94A3B8"),
                xaxis=dict(title="Hour of Day", gridcolor="#334155"),
                yaxis=dict(title="Power (kW)", gridcolor="#334155"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            ui.plotly(fig).classes("w-full h-80")
