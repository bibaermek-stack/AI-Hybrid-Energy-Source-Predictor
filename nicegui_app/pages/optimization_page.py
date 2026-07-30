"""
Microgrid Dispatch Optimization Page for NiceGUI.
"""

from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client


def render_optimization_page():
    """Render microgrid dispatch optimization page."""
    with ui.column().classes("w-full gap-6 p-4"):
        ui.label("⚙ " + state.text("opt_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.card().classes("w-full p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            with ui.grid().classes("w-full grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4"):
                ui.number(state.text("opt_load"), value=state.load_kw, step=50).bind_value(state, "load_kw").classes("w-full")
                ui.number(state.text("opt_battery"), value=state.battery_kw, step=20).bind_value(state, "battery_kw").classes("w-full")
                ui.number(state.text("opt_solar_cost"), value=state.solar_cost, step=0.01).bind_value(state, "solar_cost").classes("w-full")
                ui.number(state.text("opt_wind_cost"), value=state.wind_cost, step=0.01).bind_value(state, "wind_cost").classes("w-full")

            ui.select(
                options={
                    "hybrid": "Hybrid Smart Dispatch",
                    "min_cost": "Minimize Operational Cost",
                    "max_power": "Maximize Renewable Output",
                    "balanced": "Balanced Battery/Grid",
                },
                value=state.strategy,
            ).bind_value(state, "strategy").classes("w-full mt-3")

            lbl_rec = ui.label("Optimal Source: ---").classes("text-lg font-bold text-blue-600 mt-4")
            lbl_solar = ui.label("0.0 kW").classes("text-base font-bold text-amber-500")
            lbl_wind = ui.label("0.0 kW").classes("text-base font-bold text-teal-500")
            lbl_bat = ui.label("0.0 kW").classes("text-base font-bold text-emerald-500")
            lbl_grid = ui.label("0.0 kW").classes("text-base font-bold text-pink-500")

            async def on_run_opt():
                res = await api_client.predict(
                    irradiation=state.irradiation,
                    temperature=state.ambient_temp,
                    module=state.module_temp,
                    hour=state.hour,
                    day=state.day,
                    month=state.month,
                    wind_speed=state.wind_speed,
                    direction=state.wind_direction,
                    theoretical=state.theoretical_power,
                    load_kw=state.load_kw,
                    battery_kw=state.battery_kw,
                    solar_cost_per_kwh=state.solar_cost,
                    wind_cost_per_kwh=state.wind_cost,
                    strategy=state.strategy,
                )
                lbl_rec.set_text(f"Optimal Source: {res.get('recommended_source', 'Hybrid')}")
                dispatch = res.get("optimal_dispatch") or {}
                lbl_solar.set_text(f"{dispatch.get('solar_kw', res.get('solar_power', 0.0)):.1f} kW")
                lbl_wind.set_text(f"{dispatch.get('wind_kw', res.get('wind_power', 0.0)):.1f} kW")
                lbl_bat.set_text(f"{dispatch.get('battery_kw', min(state.battery_kw, 50.0)):.1f} kW")
                lbl_grid.set_text(f"{dispatch.get('grid_kw', 0.0):.1f} kW")
                ui.notify("Microgrid dispatch optimization complete!", type="positive")

            ui.button(state.text("opt_btn"), icon="tune", on_click=on_run_opt).classes("w-full mt-4 py-3 bg-blue-600 text-white font-bold rounded-xl")

            with ui.card().classes("w-full p-4 mt-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-gray-700"):
                lbl_rec
                ui.separator().classes("my-2")
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("☀️ Solar Supply:")
                    lbl_solar
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("💨 Wind Supply:")
                    lbl_wind
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("🔋 Battery Discharge:")
                    lbl_bat
                with ui.row().classes("w-full justify-between items-center"):
                    ui.label("⚡ Grid Import:")
                    lbl_grid
