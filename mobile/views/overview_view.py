"""
Overview / Home View for EcoPredict AI Mobile.
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
    from mobile.components.metric_card import build_metric_card
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from components.metric_card import build_metric_card  # type: ignore # pyright: ignore[reportMissingImports]


def build_overview_view(page: ft.Page, on_navigate: Callable[[int], None]) -> ft.Control:
    """Build home overview screen."""
    c = state.colors

    # Hero card
    hero_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text("AI · Energy · Education", size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                            border_radius=10,
                            bgcolor="rgba(255,255,255,0.2)",
                        ),
                    ]
                ),
                ft.Text(
                    state.text("ov_hero_title"),
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color="#FFFFFF",
                ),
                ft.Text(
                    state.text("ov_hero_sub"),
                    size=12,
                    color="rgba(255,255,255,0.85)",
                ),
            ],
            spacing=8,
        ),
        padding=16,
        border_radius=16,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
            colors=["#1E3A8A", "#3B82F6", "#0D9488"],
        ),
    )

    # Key Performance Indicators
    kpi_title = ft.Text(
        "📊 " + state.text("ov_quick_actions"),
        size=15,
        weight=ft.FontWeight.BOLD,
        color=c["text_primary"],
    )

    card_solar = build_metric_card(
        title=state.text("ov_kpi_solar"),
        value="620.4",
        unit="kW",
        icon=ft.Icons.WB_SUNNY,
        accent_color="#F59E0B",
        subtitle="Forecast peak @ 13:00",
    )

    card_wind = build_metric_card(
        title=state.text("ov_kpi_wind"),
        value="310.8",
        unit="kW",
        icon=ft.Icons.AIR,
        accent_color="#14B8A6",
        subtitle="Average speed 6.5 m/s",
    )

    card_load = build_metric_card(
        title=state.text("ov_kpi_load"),
        value="450.0",
        unit="kW",
        icon=ft.Icons.POWER,
        accent_color="#EC4899",
        subtitle="Microgrid demand",
    )

    card_battery = build_metric_card(
        title=state.text("ov_kpi_battery"),
        value="82.5",
        unit="%",
        icon=ft.Icons.BATTERY_CHARGING_FULL,
        accent_color="#10B981",
        subtitle="200 kWh capacity",
    )

    # Grid layout of KPI cards
    kpi_grid = ft.Column(
        [
            ft.Row([ft.Container(card_solar, expand=True), ft.Container(card_wind, expand=True)], spacing=10),
            ft.Row([ft.Container(card_load, expand=True), ft.Container(card_battery, expand=True)], spacing=10),
        ],
        spacing=10,
    )

    # Quick action shortcuts
    action_btn_predict = ft.ElevatedButton(
        content=ft.Text(state.text("ov_btn_predict")),
        icon=ft.Icons.SHOW_CHART,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=lambda e: on_navigate(1), # Forecast tab
        expand=True,
    )

    action_btn_fault = ft.OutlinedButton(
        content=ft.Text(state.text("ov_btn_fault")),
        icon=ft.Icons.CAMERA_ALT,
        style=ft.ButtonStyle(
            color=c["text_primary"],
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=lambda e: on_navigate(2), # Faults tab
        expand=True,
    )

    action_btn_chat = ft.OutlinedButton(
        content=ft.Text(state.text("ov_btn_chat")),
        icon=ft.Icons.CHAT,
        style=ft.ButtonStyle(
            color=c["text_primary"],
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=lambda e: on_navigate(4), # Chat tab
        expand=True,
    )

    quick_actions = ft.Column(
        [
            action_btn_predict,
            ft.Row([action_btn_fault, action_btn_chat], spacing=10),
        ],
        spacing=10,
    )

    offline_banner = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.WIFI_OFF, color="#FFFFFF", size=22),
                ft.Column(
                    [
                        ft.Text(
                            "⚠️ Интернет байланысы жоқ!",
                            size=13,
                            weight=ft.FontWeight.BOLD,
                            color="#FFFFFF",
                        ),
                        ft.Text(
                            "Ұялы деректерді (4G/5G) немесе Wi-Fi-ды тексеріңіз. Railway 24/7 Сервер оффлайн.",
                            size=11,
                            color="#FEE2E2",
                        ),
                    ],
                    spacing=2,
                    expand=True,
                ),
            ],
            spacing=10,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["error"],
        visible=not state.is_api_online,
    )

    return ft.ListView(
        controls=[
            offline_banner,
            hero_card,
            ft.Container(height=10),
            kpi_grid,
            ft.Container(height=14),
            kpi_title,
            ft.Container(height=6),
            quick_actions,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
    )
