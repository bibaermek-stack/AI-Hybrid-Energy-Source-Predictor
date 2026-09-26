"""
Top AppBar header component with status pill, language toggle, and theme switch.
"""

import flet as ft
from typing import Callable, Optional
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_app_header(
    page: ft.Page,
    on_recheck: Callable[[], None],
    on_back: Optional[Callable[[], None]] = None,
    title: Optional[str] = None,
) -> ft.AppBar:
    """
    Build the top app bar.

    Language and theme buttons only change state; main.py listens and rebuilds
    the screens. Tapping the status pill re-runs the health check (on_recheck).
    With on_back set (a screen opened from the "More" tab) the logo becomes a
    back arrow and `title` replaces the app name.
    """
    c = state.colors
    t = state.text
    is_online = state.is_api_online

    status_color = c["success"] if is_online else c["error"]
    status_text = t("ov_status_online") if is_online else t("ov_status_offline")

    if on_back is not None:
        leading = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            icon_color=c["text_primary"],
            tooltip=t("back"),
            on_click=lambda e: on_back(),
        )
    else:
        leading = ft.Container(
            content=ft.Icon(ft.Icons.ENERGY_SAVINGS_LEAF, color=c["primary"], size=28),
            padding=ft.Padding.only(left=12),
        )

    title_column = ft.Column(
        [
            ft.Text(
                title or t("app_title"),
                size=16,
                weight=ft.FontWeight.BOLD,
                color=c["text_primary"],
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]
        + (
            []
            if title
            else [
                ft.Text(
                    t("app_subtitle"),
                    size=10,
                    color=c["text_secondary"],
                    overflow=ft.TextOverflow.ELLIPSIS,
                )
            ]
        ),
        spacing=1,
    )

    return ft.AppBar(
        leading=leading,
        leading_width=48 if on_back else 44,
        title=title_column,
        bgcolor=c["surface"],
        elevation=2,
        actions=[
            # API health pill — tap to check again.
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(width=8, height=8, border_radius=4, bgcolor=status_color),
                        ft.Text(status_text, size=10, weight=ft.FontWeight.W_600, color=c["text_primary"]),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
                bgcolor=c["surface_variant"],
                tooltip=t("status_recheck"),
                on_click=lambda e: on_recheck(),
                ink=True,
            ),
            ft.IconButton(
                icon=ft.Icons.TRANSLATE,
                icon_color=c["primary"],
                tooltip=t("toggle_language"),
                on_click=lambda e: state.set_language("en" if state.lang == "kk" else "kk"),
            ),
            ft.IconButton(
                icon=ft.Icons.LIGHT_MODE if state.theme_mode == "dark" else ft.Icons.DARK_MODE,
                icon_color=c["accent"],
                tooltip=t("toggle_theme"),
                on_click=lambda e: state.toggle_theme(),
            ),
            ft.Container(width=4),
        ],
    )
