"""
"More" tab for EcoPredict AI Mobile: the screens that no longer fit in the
five-slot navigation bar. Opening one keeps "More" highlighted and shows a
back arrow in the app bar (see main.py).
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

# (screen key, icon, title i18n key, subtitle i18n key)
MORE_ITEMS = [
    ("faults", ft.Icons.SOLAR_POWER, "nav_faults", "more_faults_sub"),
    ("opt", ft.Icons.TUNE, "nav_opt", "more_opt_sub"),
    ("sustainability", ft.Icons.CO2, "nav_sustainability", "more_sust_sub"),
    ("labs", ft.Icons.SCIENCE, "nav_labs", "more_labs_sub"),
    ("training", ft.Icons.INSIGHTS, "nav_training", "more_training_sub"),
    ("learn", ft.Icons.SCHOOL, "nav_learn", "more_learn_sub"),
    ("settings", ft.Icons.SETTINGS, "nav_settings", "more_settings_sub"),
]

TITLE_KEYS = {key: title for key, _, title, _ in MORE_ITEMS}


def build_more_view(page: ft.Page, on_open: Callable[[str], None]) -> ft.Control:
    """List of secondary screens."""
    c = state.colors
    t = state.text

    def tile(key: str, icon, title_key: str, sub_key: str) -> ft.Control:
        return ft.Container(
            content=ft.ListTile(
                leading=ft.Icon(icon, color=c["primary"]),
                title=ft.Text(t(title_key), weight=ft.FontWeight.W_600, color=c["text_primary"]),
                subtitle=ft.Text(t(sub_key), size=11, color=c["text_secondary"]),
                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=c["text_secondary"]),
                on_click=lambda e, k=key: on_open(k),
            ),
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
        )

    return ft.ListView(
        controls=[ft.Text(t("more_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"])]
        + [tile(*item) for item in MORE_ITEMS]
        + [ft.Container(height=20)],
        spacing=10,
        padding=12,
        expand=True,
    )
