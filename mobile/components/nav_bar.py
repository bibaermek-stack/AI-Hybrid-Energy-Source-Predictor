"""
Primary navigation for EcoPredict AI Mobile: five destinations, shown as a
bottom NavigationBar on phones and a NavigationRail on wide screens.

There used to be eleven bottom-bar destinations — about 35 px each on a
393 px phone, with labels wrapping mid-word ("YOL O", "Solar man"). Material
recommends three to five; everything else lives under "More" (more_view.py).
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

# (screen key, icon, selected icon, label i18n key)
TABS = [
    ("overview", ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "nav_overview"),
    ("forecast", ft.Icons.SHOW_CHART_OUTLINED, ft.Icons.SHOW_CHART, "nav_forecast"),
    ("live", ft.Icons.SENSORS_OUTLINED, ft.Icons.SENSORS, "nav_live"),
    ("chat", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE, "nav_chat"),
    ("more", ft.Icons.APPS_OUTLINED, ft.Icons.APPS, "nav_more"),
]

# Width from which the rail replaces the bottom bar (Material "medium" window).
RAIL_BREAKPOINT = 600


def build_bottom_nav(selected_index: int, on_change: Callable) -> ft.NavigationBar:
    """Phone bottom navigation bar."""
    c = state.colors
    return ft.NavigationBar(
        selected_index=min(max(selected_index, 0), len(TABS) - 1),
        destinations=[
            ft.NavigationBarDestination(icon=icon, selected_icon=selected, label=state.text(label))
            for _, icon, selected, label in TABS
        ],
        on_change=on_change,
        bgcolor=c["surface"],
        indicator_color=c["primary_container"],
        elevation=8,
    )


def build_nav_rail(selected_index: int, on_change: Callable) -> ft.NavigationRail:
    """Tablet / desktop side rail with the same destinations."""
    c = state.colors
    return ft.NavigationRail(
        selected_index=min(max(selected_index, 0), len(TABS) - 1),
        label_type=ft.NavigationRailLabelType.ALL,
        destinations=[
            ft.NavigationRailDestination(icon=icon, selected_icon=selected, label=state.text(label))
            for _, icon, selected, label in TABS
        ],
        on_change=on_change,
        bgcolor=c["surface"],
        indicator_color=c["primary_container"],
        min_width=88,
    )
