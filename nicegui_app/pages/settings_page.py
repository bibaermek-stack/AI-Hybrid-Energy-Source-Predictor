"""
Settings & Diagnostics Page for NiceGUI.
"""

from typing import Callable
from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client


def render_settings_page(on_refresh: Callable[[], None]):
    """Render settings & diagnostics page."""
    with ui.column().classes("w-full gap-6 p-4"):
        ui.label("⚙ " + state.text("st_title")).classes("text-xl font-bold text-gray-800 dark:text-white")

        with ui.card().classes("w-full p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label(state.text("st_api_url")).classes("text-sm font-bold text-gray-800 dark:text-white")
            inp_url = ui.input(value=state.api_base_url).classes("w-full")

            async def test_conn():
                state.api_base_url = (inp_url.value or "").rstrip("/")
                res = await api_client.check_health()
                if res.get("status") == "healthy" or state.is_api_online:
                    ui.notify("Connection established successfully!", type="positive")
                else:
                    ui.notify("Error: Unable to connect to backend server.", type="negative")
                on_refresh()

            ui.button(state.text("st_btn_test"), icon="network_check", on_click=test_conn).classes("mt-3 bg-blue-600 text-white font-bold rounded-lg")

        with ui.card().classes("w-full p-5 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-slate-900 shadow-sm"):
            ui.label(state.text("st_lang")).classes("text-sm font-bold text-gray-800 dark:text-white mb-2")

            def on_lang_change(e):
                state.set_language(e.value)
                on_refresh()

            ui.radio(options={"kk": "Қазақша (KK)", "en": "English (EN)"}, value=state.lang, on_change=on_lang_change).props("inline")

        with ui.card().classes("w-full p-5 rounded-xl bg-blue-50 dark:bg-slate-800 border border-blue-200 dark:border-blue-900"):
            ui.label("EcoPredict AI NiceGUI Web v1.0.0").classes("text-sm font-bold text-blue-600 dark:text-blue-400")
            ui.label("Built with NiceGUI (Vue 3 / Quasar + TailwindCSS) & FastAPI").classes("text-xs text-gray-500 mt-1")
