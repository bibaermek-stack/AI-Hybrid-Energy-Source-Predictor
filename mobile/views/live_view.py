"""
Solarman Live Monitoring View for EcoPredict AI Mobile.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile.components.metric_card import build_metric_card
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    from components.metric_card import build_metric_card  # type: ignore # pyright: ignore[reportMissingImports]


def build_live_view(page: ft.Page) -> ft.Control:
    """Build live plant telemetry and inverter status view."""
    c = state.colors

    txt_power = ft.Text("845.2 kW", size=22, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_daily = ft.Text("3,420.5 kWh", size=22, weight=ft.FontWeight.BOLD, color=c["accent"])
    txt_status = ft.Text("Normal Operation / Нормалды", size=14, weight=ft.FontWeight.BOLD, color=c["success"])
    txt_weather = ft.Text("Clear Sky 28.5°C · Irradiance 910 W/m²", size=12, color=c["text_secondary"])

    async def on_refresh(e):
        data = await api_client.get_solarman_live()
        txt_power.value = f"{data.get('inverter_power_kw', 845.2):.1f} kW"
        txt_daily.value = f"{data.get('daily_yield_kwh', 3420.5):.1f} kWh"
        txt_status.value = data.get("status", "Normal Operation")
        txt_weather.value = f"Ambient {data.get('ambient_temp_c', 28.5)}°C"
        page.update()

    btn_refresh = ft.IconButton(icon=ft.Icons.REFRESH, icon_color=c["primary"], on_click=on_refresh)

    status_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row([ft.Icon(ft.Icons.SENSORS, color=c["success"]), ft.Text("Inverter Telemetry", weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                        btn_refresh,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                txt_status,
                txt_weather,
            ],
            spacing=4,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    kpi_grid = ft.Row(
        [
            ft.Container(
                build_metric_card(title=state.text("live_power"), value="845.2", unit="kW", icon=ft.Icons.POWER, accent_color=c["primary"]),
                expand=True,
            ),
            ft.Container(
                build_metric_card(title=state.text("live_daily"), value="3.42", unit="MWh", icon=ft.Icons.WB_SUNNY, accent_color=c["accent"]),
                expand=True,
            ),
        ],
        spacing=10,
    )

    alerts_box = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=c["warning"]), ft.Text(state.text("live_alerts"), weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                ft.Text("• Inverter MPPT efficiency optimal (98.2%)", size=12, color=c["text_secondary"]),
                ft.Text("• Grid voltage frequency stable @ 50.01 Hz", size=12, color=c["text_secondary"]),
                ft.Text("• Next automated cleaning cycle: Tomorrow 06:00", size=12, color=c["text_secondary"]),
            ],
            spacing=6,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    return ft.ListView(
        controls=[
            ft.Text("📡 " + state.text("live_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            status_card,
            kpi_grid,
            alerts_box,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
    )
