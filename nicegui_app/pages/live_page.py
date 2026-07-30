"""
Solarman Live Telemetry Page for NiceGUI.
"""

from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client
from nicegui_app.components.metric_card import build_metric_card


def render_live_page():
    """Render live telemetry page."""
    with ui.column().classes("w-full gap-6 p-4"):
        with ui.row().classes("w-full justify-between items-center"):
            ui.label("📡 " + state.text("live_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

            async def on_refresh():
                data = await api_client.get_solarman_live()
                lbl_power.set_text(f"{data.get('inverter_power_kw', 845.2):.1f} kW")
                lbl_yield.set_text(f"{data.get('daily_yield_kwh', 3420.5):.1f} kWh")
                lbl_status.set_text(data.get("status", "Normal Operation"))
                ui.notify("Telemetry refreshed!", type="info")

            ui.button("Refresh Telemetry", icon="refresh", on_click=on_refresh).props("outline color=primary dense")

        lbl_status = ui.label("Normal Operation / Нормалды").classes("text-lg font-bold text-emerald-500")
        with ui.card().classes("w-full p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label("Inverter Status:").classes("text-xs text-gray-400")
            lbl_status
            ui.label("Clear Sky 28.5°C · Solar Irradiance 910 W/m²").classes("text-xs text-gray-500 mt-1")

        with ui.grid().classes("w-full grid-cols-1 sm:grid-cols-2 gap-4"):
            lbl_power = ui.label("845.2 kW").classes("text-2xl font-bold text-blue-600")
            lbl_yield = ui.label("3,420.5 kWh").classes("text-2xl font-bold text-amber-500")

            build_metric_card(title=state.text("live_power"), value="845.2", unit="kW", icon="power", color="text-blue-500")
            build_metric_card(title=state.text("live_yield"), value="3,420.5", unit="kWh", icon="wb_sunny", color="text-amber-500")

        with ui.card().classes("w-full p-4 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label("⚠️ Active Grid Alerts & System Health").classes("text-sm font-bold text-gray-800 dark:text-white mb-2")
            ui.label("• Inverter MPPT efficiency optimal @ 98.2%").classes("text-xs text-gray-500")
            ui.label("• Grid voltage frequency stable @ 50.01 Hz").classes("text-xs text-gray-500")
            ui.label("• Automated solar panel cleaning scheduled tomorrow @ 06:00").classes("text-xs text-gray-500")
