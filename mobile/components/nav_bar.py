"""
Responsive Navigation Bar & Rail component for EcoPredict AI Mobile.
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_bottom_nav(selected_index: int, on_change: Callable) -> ft.NavigationBar:
    """Build mobile bottom navigation bar with expanded view destinations."""
    c = state.colors

    destinations = [
        ft.NavigationBarDestination(
            icon=ft.Icons.HOME_OUTLINED,
            selected_icon=ft.Icons.HOME,
            label="Басты",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.AUTO_AWESOME_OUTLINED,
            selected_icon=ft.Icons.AUTO_AWESOME,
            label="ML Болжам",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SHOW_CHART_OUTLINED,
            selected_icon=ft.Icons.SHOW_CHART,
            label="24h График",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SOLAR_POWER_OUTLINED,
            selected_icon=ft.Icons.SOLAR_POWER,
            label="YOLO Ақау",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SCHOOL_OUTLINED,
            selected_icon=ft.Icons.SCHOOL,
            label="Оқыту ML",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.TUNE_OUTLINED,
            selected_icon=ft.Icons.TUNE,
            label="Оңтайландыру",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.CO2_OUTLINED,
            selected_icon=ft.Icons.CO2,
            label="Экология",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SCIENCE_OUTLINED,
            selected_icon=ft.Icons.SCIENCE,
            label="Лаборатория",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.CHAT_BUBBLE_OUTLINE,
            selected_icon=ft.Icons.CHAT_BUBBLE,
            label="AI Кеңесші",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SENSORS_OUTLINED,
            selected_icon=ft.Icons.SENSORS,
            label="Solarman",
        ),
        ft.NavigationBarDestination(
            icon=ft.Icons.SETTINGS_OUTLINED,
            selected_icon=ft.Icons.SETTINGS,
            label="Баптаулар",
        ),
    ]

    return ft.NavigationBar(
        selected_index=min(selected_index, len(destinations) - 1),
        destinations=destinations,
        on_change=on_change,
        bgcolor=c["surface"],
        indicator_color=c["primary_container"],
        elevation=8,
    )
