"""
EcoPredict AI - NiceGUI Mobile-First Application Shell.
"""

import sys
from pathlib import Path

# Project root on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nicegui import ui
from nicegui_app.state import state
from nicegui_app.api_client import api_client
from nicegui_app.components.header import build_header

from nicegui_app.pages.overview_page import render_overview_page
from nicegui_app.pages.forecast_page import render_forecast_page
from nicegui_app.pages.faults_page import render_faults_page
from nicegui_app.pages.optimization_page import render_optimization_page
from nicegui_app.pages.chat_page import render_chat_page
from nicegui_app.pages.live_page import render_live_page
from nicegui_app.pages.settings_page import render_settings_page


@ui.page("/")
async def index_page():
    """Main mobile-first dashboard routing."""
    # Custom viewport meta tag for mobile devices
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">')
    ui.add_head_html('<meta name="apple-mobile-web-app-capable" content="yes">')
    ui.add_head_html('<meta name="mobile-web-app-capable" content="yes">')

    # Startup API health check
    await api_client.check_health()

    def refresh_shell():
        ui.navigate.to("/")

    # Centered Mobile Frame Shell Container
    with ui.column().classes("w-full max-w-md mx-auto min-h-screen bg-gray-50 dark:bg-slate-950 shadow-2xl border-x border-gray-200 dark:border-gray-800 pb-20 relative p-0"):
        # Mobile Header
        build_header(refresh_shell)

        # Tab panels & Bottom Navigation Tabs
        with ui.tabs().classes("w-full bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-gray-800 text-xs overflow-x-auto") as tabs:
            t_overview = ui.tab("overview", label=state.text("nav_overview"), icon="home")
            t_forecast = ui.tab("forecast", label=state.text("nav_forecast"), icon="trending_up")
            t_faults = ui.tab("faults", label=state.text("nav_faults"), icon="search")
            t_opt = ui.tab("opt", label=state.text("nav_opt"), icon="tune")
            t_chat = ui.tab("chat", label=state.text("nav_chat"), icon="chat")
            t_live = ui.tab("live", label=state.text("nav_live"), icon="sensors")
            t_settings = ui.tab("settings", label=state.text("nav_settings"), icon="settings")

        with ui.tab_panels(tabs, value=t_overview).classes("w-full bg-transparent p-0"):
            with ui.tab_panel(t_overview).classes("p-2"):
                render_overview_page()
            with ui.tab_panel(t_forecast).classes("p-2"):
                render_forecast_page()
            with ui.tab_panel(t_faults).classes("p-2"):
                render_faults_page()
            with ui.tab_panel(t_opt).classes("p-2"):
                render_optimization_page()
            with ui.tab_panel(t_chat).classes("p-2"):
                render_chat_page()
            with ui.tab_panel(t_live).classes("p-2"):
                render_live_page()
            with ui.tab_panel(t_settings).classes("p-2"):
                render_settings_page(refresh_shell)

        # Mobile Bottom Navigation Bar Container
        with ui.row().classes("w-full max-w-md mx-auto bg-blue-950 text-white flex justify-around items-center py-2 fixed bottom-0 z-50 border-t border-blue-900"):
            ui.button(icon="home", on_click=lambda: tabs.set_value("overview")).props("flat color=white dense round")
            ui.button(icon="trending_up", on_click=lambda: tabs.set_value("forecast")).props("flat color=white dense round")
            ui.button(icon="search", on_click=lambda: tabs.set_value("faults")).props("flat color=white dense round")
            ui.button(icon="tune", on_click=lambda: tabs.set_value("opt")).props("flat color=white dense round")
            ui.button(icon="chat", on_click=lambda: tabs.set_value("chat")).props("flat color=white dense round")
            ui.button(icon="settings", on_click=lambda: tabs.set_value("settings")).props("flat color=white dense round")


def run():
    """Run NiceGUI mobile-first web app."""
    ui.run(
        title="EcoPredict AI Mobile Web",
        port=8560,
        reload=False,
        show=True,
        favicon="⚡",
    )


if __name__ in {"__main__", "__mp_main__"}:
    run()
