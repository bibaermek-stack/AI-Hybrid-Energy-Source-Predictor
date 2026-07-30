"""
Energy Forecasting Page for NiceGUI.
"""

from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client


def render_forecast_page():
    """Render energy generation forecast page."""
    with ui.column().classes("w-full gap-6 p-4"):
        ui.label("📈 " + state.text("fc_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.grid().classes("w-full grid-cols-1 md:grid-cols-2 gap-6"):
            # Solar parameters card
            with ui.card().classes("p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
                with ui.row().classes("items-center gap-2 mb-2"):
                    ui.icon("wb_sunny", size="sm").classes("text-amber-500")
                    ui.label(state.text("fc_solar_params")).classes("font-bold text-gray-800 dark:text-white")

                ui.label("Solar Irradiance (W/m²)").classes("text-xs text-gray-500")
                ui.slider(min=0, max=1500, step=10).bind_value(state, "irradiation").props("label-always color=amber")

                ui.label("Ambient Temperature (°C)").classes("text-xs text-gray-500 mt-2")
                ui.slider(min=-10, max=60, step=1).bind_value(state, "ambient_temp").props("label-always color=amber")

                ui.label("Module Temperature (°C)").classes("text-xs text-gray-500 mt-2")
                ui.slider(min=-10, max=80, step=1).bind_value(state, "module_temp").props("label-always color=amber")

            # Wind parameters card
            with ui.card().classes("p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
                with ui.row().classes("items-center gap-2 mb-2"):
                    ui.icon("air", size="sm").classes("text-teal-500")
                    ui.label(state.text("fc_wind_params")).classes("font-bold text-gray-800 dark:text-white")

                ui.label("Wind Speed (m/s)").classes("text-xs text-gray-500")
                ui.slider(min=0, max=25, step=0.5).bind_value(state, "wind_speed").props("label-always color=teal")

                ui.label("Wind Direction (°)").classes("text-xs text-gray-500 mt-2")
                ui.slider(min=0, max=360, step=5).bind_value(state, "wind_direction").props("label-always color=teal")

                ui.label("Theoretical Power (kWh)").classes("text-xs text-gray-500 mt-2")
                ui.slider(min=0, max=2000, step=50).bind_value(state, "theoretical_power").props("label-always color=teal")

        # Results Container
        lbl_solar = ui.label("0.0 kW").classes("text-2xl font-bold text-amber-500")
        lbl_wind = ui.label("0.0 kW").classes("text-2xl font-bold text-teal-500")
        lbl_total = ui.label("0.0 kW").classes("text-3xl font-extrabold text-blue-500")
        lbl_source = ui.label("---").classes("text-sm font-semibold text-gray-700 dark:text-gray-300")
        spinner = ui.spinner(size="sm").classes("hidden")

        async def on_calculate():
            spinner.classes(remove="hidden")
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
            spinner.classes(add="hidden")
            lbl_solar.set_text(f"{res.get('solar_power', 0.0):.1f} kW")
            lbl_wind.set_text(f"{res.get('wind_power', 0.0):.1f} kW")
            lbl_total.set_text(f"{res.get('total_power', 0.0):.1f} kW")
            lbl_source.set_text(f"Recommended Source: {res.get('recommended_source', 'N/A')}")
            ui.notify("Forecast calculated successfully!", type="positive", icon="check_circle")

        ui.button(state.text("fc_btn"), icon="calculate", on_click=on_calculate).classes("w-full py-3 bg-blue-600 text-white font-bold rounded-xl shadow-md")

        with ui.card().classes("w-full p-6 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50/50 dark:bg-slate-900 shadow-sm text-center"):
            with ui.row().classes("justify-center items-center gap-2"):
                ui.label(state.text("fc_total")).classes("text-sm text-gray-500 dark:text-gray-400")
                spinner

            lbl_total
            ui.separator().classes("my-2")
            with ui.row().classes("w-full justify-around mt-2"):
                with ui.column().classes("items-center"):
                    ui.label(state.text("fc_solar")).classes("text-xs text-gray-400")
                    lbl_solar
                with ui.column().classes("items-center"):
                    ui.label(state.text("fc_wind")).classes("text-xs text-gray-400")
                    lbl_wind
            lbl_source.classes("mt-3")
