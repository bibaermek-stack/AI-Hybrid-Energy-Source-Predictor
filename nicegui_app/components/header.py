"""
NiceGUI Mobile Header Component with language switcher and dark mode toggle.
"""

from typing import Callable
from nicegui import ui
from nicegui_app.state import state


def build_header(on_refresh: Callable[[], None]):
    """Build compact mobile header navigation bar."""
    dark = ui.dark_mode()

    with ui.row().classes("bg-blue-900 text-white flex items-center justify-between px-3 py-2.5 shadow-md w-full rounded-b-xl"):
        with ui.row().classes("items-center gap-2"):
            ui.icon("bolt", size="sm").classes("text-yellow-400")
            with ui.column().classes("gap-0"):
                ui.label(state.text("app_title")).classes("text-base font-extrabold leading-tight")
                ui.label("Mobile Web").classes("text-xs text-blue-200")

        with ui.row().classes("items-center gap-2"):
            # Health status badge
            status_color = "bg-green-500" if state.is_api_online else "bg-red-500"
            with ui.row().classes("items-center gap-1 px-2 py-0.5 rounded-full bg-blue-950 text-xs font-semibold"):
                ui.element("div").classes(f"w-2 h-2 rounded-full {status_color}")

            # Language switcher
            def on_lang_change(e):
                state.set_language(e.value)
                on_refresh()

            ui.select(
                options={"kk": "KK", "en": "EN"},
                value=state.lang,
                on_change=on_lang_change,
            ).props("dense options-dense borderless bg-blue-800 text-white").classes("text-xs font-bold px-1 rounded")

            # Dark mode button
            def toggle_theme():
                state.dark_mode = not state.dark_mode
                if state.dark_mode:
                    dark.enable()
                else:
                    dark.disable()
                on_refresh()

            ui.button(icon="dark_mode" if state.dark_mode else "light_mode", on_click=toggle_theme).props("flat color=white dense round")
