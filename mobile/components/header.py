"""
Top AppBar header component with status pill, language toggle, and theme switch.
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_app_header(page: ft.Page, on_refresh: Callable[[], None]) -> ft.AppBar:
    """Build responsive top app bar."""
    c = state.colors
    is_online = state.is_api_online
    
    # Status pill color & text
    status_color = c["success"] if is_online else c["error"]
    status_text = state.text("ov_status_online" if is_online else "ov_status_offline")
    
    def on_lang_toggle(e):
        next_lang = "en" if state.lang == "kk" else "kk"
        state.set_language(next_lang)
        on_refresh()
        page.update()

    def on_theme_toggle(e):
        state.toggle_theme()
        on_refresh()
        page.update()

    return ft.AppBar(
        leading=ft.Container(
            content=ft.Icon(ft.Icons.ENERGY_SAVINGS_LEAF, color=c["primary"], size=28),
            padding=ft.Padding.only(left=12),
        ),
        leading_width=44,
        title=ft.Column(
            [
                ft.Text(
                    state.text("app_title"),
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=c["text_primary"],
                ),
                ft.Text(
                    state.text("app_subtitle"),
                    size=10,
                    color=c["text_secondary"],
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=1,
        ),
        bgcolor=c["surface"],
        elevation=2,
        actions=[
            # API Health Pill
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            width=8,
                            height=8,
                            border_radius=4,
                            bgcolor=status_color,
                        ),
                        ft.Text(
                            status_text,
                            size=10,
                            weight=ft.FontWeight.W_600,
                            color=c["text_primary"],
                        ),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
                bgcolor=c["surface_variant"],
            ),
            # Language toggle button
            ft.IconButton(
                icon=ft.Icons.TRANSLATE,
                icon_color=c["primary"],
                tooltip="Switch Language (KK/EN)",
                on_click=on_lang_toggle,
            ),
            # Theme toggle button
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE if state.theme_mode == "dark" else ft.Icons.DARK_MODE,
                icon_color=c["accent"],
                tooltip="Toggle Theme Mode",
                on_click=on_theme_toggle,
            ),
            ft.Container(width=4),
        ],
    )
