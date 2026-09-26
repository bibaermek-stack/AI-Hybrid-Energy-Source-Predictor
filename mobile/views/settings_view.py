"""
Settings & Diagnostics View for EcoPredict AI Mobile.

Language and theme changes go through state.set_language / state.set_theme;
main.py listens, saves them to SharedPreferences and rebuilds every screen.
"""

import flet as ft
from typing import Callable
try:
    from mobile.config import APP_VERSION
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from config import APP_VERSION  # type: ignore # pyright: ignore[reportMissingImports]
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_settings_view(page: ft.Page, on_status_change: Callable[[], None]) -> ft.Control:
    """Build application configuration and network diagnostics screen."""
    c = state.colors
    t = state.text

    txt_server_status = ft.Text("", size=11, weight=ft.FontWeight.W_500)
    txt_status_msg = ft.Text("", size=12, color=c["text_secondary"], selectable=True)
    progress = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2)

    def paint_server_status() -> None:
        online = state.is_api_online
        txt_server_status.value = t("st_server_online") if online else t("st_server_offline")
        txt_server_status.color = c["success"] if online else c["error"]

    paint_server_status()

    server_info_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CLOUD_DONE, color=c["primary"], size=22),
                        ft.Text(t("st_server_title"), size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                    ],
                    spacing=8,
                ),
                txt_server_status,
                ft.Text(state.api_base_url, size=10, color=c["text_secondary"], selectable=True),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=10,
        bgcolor=c["surface_variant"],
    )

    async def on_test_conn(e):
        progress.visible = True
        page.update()
        await api_client.check_health()
        progress.visible = False
        paint_server_status()
        if state.is_api_online:
            txt_status_msg.value = t("st_status_ok")
            txt_status_msg.color = c["success"]
        else:
            # Show what actually failed. A bare "no internet" sent us chasing
            # the network when the real cause was certificate verification.
            detail = state.api_status_detail
            txt_status_msg.value = f"{t('st_status_err')}\n\n{detail}" if detail else t("st_status_err")
            txt_status_msg.color = c["error"]
        on_status_change()
        page.update()

    btn_test = ft.Button(
        content=ft.Row([ft.Text(t("st_btn_test")), progress], tight=True, spacing=8),
        icon=ft.Icons.NETWORK_CHECK,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_test_conn,
    )

    rg_lang = ft.RadioGroup(
        content=ft.Row(
            [
                # Each language is named in itself, whichever is active.
                ft.Radio(value="kk", label=t("lang_name_kk")),
                ft.Radio(value="en", label=t("lang_name_en")),
            ]
        ),
        value=state.lang,
        on_change=lambda e: state.set_language(e.control.value),
    )

    rg_theme = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="dark", label=t("st_dark")),
                ft.Radio(value="light", label=t("st_light")),
            ]
        ),
        value=state.theme_mode,
        on_change=lambda e: state.set_theme(e.control.value),
    )

    def box(controls: list, bgcolor: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(controls, spacing=8),
            padding=14,
            border_radius=14,
            bgcolor=bgcolor,
            border=ft.Border.all(1, c["card_border"]),
        )

    box_config = box(
        [
            ft.Text(t("st_api_url"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            server_info_card,
            btn_test,
            txt_status_msg,
        ],
        c["surface"],
    )

    box_pref = box(
        [
            ft.Text(t("st_lang"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            rg_lang,
            ft.Divider(height=1, color=c["card_border"]),
            ft.Text(t("st_theme"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            rg_theme,
            ft.Text(t("st_saved_note"), size=11, color=c["text_secondary"]),
        ],
        c["surface"],
    )

    box_info = box(
        [
            ft.Text(f"EcoPredict AI Mobile v{APP_VERSION}", weight=ft.FontWeight.BOLD, color=c["primary"]),
            ft.Text(t("st_info_engine"), size=11, color=c["text_secondary"]),
            ft.Text(t("st_info_project"), size=11, color=c["text_secondary"]),
        ],
        c["surface_variant"],
    )

    return ft.ListView(
        controls=[
            ft.Text("⚙ " + t("st_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            box_config,
            box_pref,
            box_info,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
        expand=True,
    )
