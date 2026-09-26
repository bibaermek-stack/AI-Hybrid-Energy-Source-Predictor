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
    from mobile.views.more_view import MORE_ITEMS
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from views.more_view import MORE_ITEMS  # type: ignore # pyright: ignore[reportMissingImports]

# (screen key, icon, selected icon, label i18n key)
TABS = [
    ("overview", ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "nav_overview"),
    ("forecast", ft.Icons.SHOW_CHART_OUTLINED, ft.Icons.SHOW_CHART, "nav_forecast"),
    ("live", ft.Icons.SENSORS_OUTLINED, ft.Icons.SENSORS, "nav_live"),
    ("chat", ft.Icons.CHAT_BUBBLE_OUTLINE, ft.Icons.CHAT_BUBBLE, "nav_chat"),
    ("more", ft.Icons.APPS_OUTLINED, ft.Icons.APPS, "nav_more"),
]

TAB_KEYS = [key for key, *_ in TABS]
MORE_KEYS = {key for key, *_ in MORE_ITEMS}

# Width from which the rail replaces the bottom bar (Material "medium" window).
RAIL_BREAKPOINT = 600


def tab_index(screen: str) -> int:
    """Bottom-bar slot a screen belongs to; secondary screens sit under More."""
    if screen in TAB_KEYS:
        return TAB_KEYS.index(screen)
    return TAB_KEYS.index("more")


def back_target(screen: str):
    """
    Where the system Back button goes from `screen`, or None to leave the app.

    A screen opened from More returns to More; any other tab returns Home;
    Back on Home exits, as Android users expect.
    """
    if screen in MORE_KEYS:
        return "more"
    if screen != "overview":
        return "overview"
    return None


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
