"""
Settings & Diagnostics View for EcoPredict AI Mobile.
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_settings_view(page: ft.Page, on_refresh_all: Callable[[], None]) -> ft.Control:
    """Build application configuration and network diagnostics screen."""
    c = state.colors

    server_info_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.CLOUD_DONE, color=c["primary"], size=22),
                        ft.Text("Railway 24/7 Production Backend", size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                    ],
                    spacing=8,
                ),
                ft.Text(
                    "Статус: 🟢 24/7 Автоматты Бұлттық Сервер (Қосылған)" if state.is_api_online else "Статус: 🔴 Уақытша Офлайн",
                    size=11,
                    color=c["success"] if state.is_api_online else c["error"],
                    weight=ft.FontWeight.W_500,
                ),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=10,
        bgcolor=c["surface_variant"],
    )
    txt_status_msg = ft.Text("", size=12, color=c["text_secondary"])

    async def on_test_conn(e):
        res = await api_client.check_health()
        if res.get("status") == "healthy" or state.is_api_online:
            txt_status_msg.value = state.text("st_status_ok")
            txt_status_msg.color = c["success"]
        else:
            txt_status_msg.value = state.text("st_status_err")
            txt_status_msg.color = c["error"]
        on_refresh_all()
        page.update()

    btn_test = ft.ElevatedButton(
        content=ft.Text(state.text("st_btn_test")),
        icon=ft.Icons.NETWORK_CHECK,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_test_conn,
    )

    def on_lang_change(e):
        state.set_language(e.control.value)
        on_refresh_all()
        page.update()

    rg_lang = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="kk", label="Қазақша (KK)"),
                ft.Radio(value="en", label="English (EN)"),
            ]
        ),
        value=state.lang,
        on_change=on_lang_change,
    )

    def on_theme_change(e):
        if e.control.value != state.theme_mode:
            state.toggle_theme()
            on_refresh_all()
            page.update()

    rg_theme = ft.RadioGroup(
        content=ft.Row(
            [
                ft.Radio(value="dark", label=state.text("st_dark")),
                ft.Radio(value="light", label=state.text("st_light")),
            ]
        ),
        value=state.theme_mode,
        on_change=on_theme_change,
    )

    box_config = ft.Container(
        content=ft.Column(
            [
                ft.Text(state.text("st_api_url"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                server_info_card,
                btn_test,
                txt_status_msg,
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    box_pref = ft.Container(
        content=ft.Column(
            [
                ft.Text(state.text("st_lang"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                rg_lang,
                ft.Divider(height=1, color=c["card_border"]),
                ft.Text(state.text("st_theme"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                rg_theme,
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    box_info = ft.Container(
        content=ft.Column(
            [
                ft.Text("EcoPredict AI Mobile v1.0.0", weight=ft.FontWeight.BOLD, color=c["primary"]),
                ft.Text("Cross-Platform Flet Engine (Flutter Python)", size=11, color=c["text_secondary"]),
                ft.Text("Built for Turkistan Hybrid Renewable Microgrid Project", size=11, color=c["text_secondary"]),
            ],
            spacing=4,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
    )

    return ft.ListView(
        controls=[
            ft.Text("⚙ " + state.text("st_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            box_config,
            box_pref,
            box_info,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
    )
