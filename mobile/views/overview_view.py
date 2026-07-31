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


def build_overview_view(page: ft.Page, on_navigate_key: Callable[[str], None]) -> ft.Control:
    """Build home overview screen with string navigation callbacks and Solarman telemetry."""
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

    kpi_grid = ft.Column(
        [
            ft.Row([ft.Container(card_solar, expand=True), ft.Container(card_wind, expand=True)], spacing=10),
            ft.Row([ft.Container(card_load, expand=True), ft.Container(card_battery, expand=True)], spacing=10),
        ],
        spacing=10,
    )

    # Interactive Solarman Telemetry Section
    solarman_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.SENSORS, color=c["primary"], size=20),
                                ft.Text("Solarman Инвертор Телеметриясы (Real-time)", size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                            ]
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ARROW_FORWARD_IOS,
                            icon_size=14,
                            icon_color=c["primary"],
                            on_click=lambda e: on_navigate_key("live"),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Text("PV Кернеу:", size=11, color=c["text_secondary"]),
                                ft.Text("480.2 V", size=14, weight=ft.FontWeight.BOLD, color=c["primary"]),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text("PV Ток:", size=11, color=c["text_secondary"]),
                                ft.Text("14.5 A", size=14, weight=ft.FontWeight.BOLD, color=c["accent"]),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text("Желі жиілігі:", size=11, color=c["text_secondary"]),
                                ft.Text("50.0 Hz", size=14, weight=ft.FontWeight.BOLD, color=c["secondary"]),
                            ],
                            expand=True,
                        ),
                    ],
                ),
                ft.OutlinedButton(
                    content=ft.Row([ft.Icon(ft.Icons.ANALYTICS, size=16), ft.Text("Толық Solarman Телеметриясын Ашу", size=12)], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: on_navigate_key("live"),
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ],
            spacing=10,
        ),
        padding=14,
        border_radius=16,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Quick action shortcuts using string keys
    action_btn_predict = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.LIGHTBULB, size=16), ft.Text("⚡ ML Лезде Болжау Жобалау")], alignment=ft.MainAxisAlignment.CENTER),
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=lambda e: on_navigate_key("predictions"),
    )

    action_btn_forecast = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.SHOW_CHART, size=16), ft.Text("📈 24h Болжам")]),
        style=ft.ButtonStyle(color=c["text_primary"], shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=lambda e: on_navigate_key("forecast"),
        expand=True,
    )

    action_btn_fault = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.CAMERA_ALT, size=16), ft.Text("📷 YOLO Ақау")]),
        style=ft.ButtonStyle(color=c["text_primary"], shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=lambda e: on_navigate_key("faults"),
        expand=True,
    )

    action_btn_chat = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.CHAT, size=16), ft.Text("💬 AI Кеңесші")]),
        style=ft.ButtonStyle(color=c["text_primary"], shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=lambda e: on_navigate_key("chat"),
        expand=True,
    )

    quick_actions = ft.Column(
        [
            action_btn_predict,
            ft.Row([action_btn_forecast, action_btn_fault], spacing=10),
            action_btn_chat,
        ],
        spacing=10,
    )

    return ft.ListView(
        controls=[
            hero_card,
            ft.Container(height=10),
            kpi_grid,
            ft.Container(height=10),
            solarman_section,
            ft.Container(height=14),
            kpi_title,
            ft.Container(height=6),
            quick_actions,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
    )
