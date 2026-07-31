"""
Overview / Home View for EcoPredict AI Mobile.
"""

import flet as ft
from typing import Callable
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile.components.metric_card import build_metric_card
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
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

    # These four cards used to show fixed numbers (620.4 / 310.8 / 450.0 /
    # 82.5) that never changed, which is what made the home screen look broken.
    # They are filled from /predict and /solarman/live once the view loads.
    ref_solar, ref_solar_sub = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    ref_wind, ref_wind_sub = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    ref_load, ref_load_sub = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    ref_batt, ref_batt_sub = ft.Ref[ft.Text](), ft.Ref[ft.Text]()

    card_solar = build_metric_card(
        title=state.text("ov_kpi_solar"),
        value="—",
        unit="kW",
        icon=ft.Icons.WB_SUNNY,
        accent_color="#F59E0B",
        subtitle="Жүктелуде…",
        value_ref=ref_solar,
        subtitle_ref=ref_solar_sub,
    )

    card_wind = build_metric_card(
        title=state.text("ov_kpi_wind"),
        value="—",
        unit="kW",
        icon=ft.Icons.AIR,
        accent_color="#14B8A6",
        subtitle="Жүктелуде…",
        value_ref=ref_wind,
        subtitle_ref=ref_wind_sub,
    )

    card_load = build_metric_card(
        title=state.text("ov_kpi_load"),
        value="—",
        unit="kW",
        icon=ft.Icons.POWER,
        accent_color="#EC4899",
        subtitle="Жүктелуде…",
        value_ref=ref_load,
        subtitle_ref=ref_load_sub,
    )

    # Shows dispatched battery power, not state of charge — the API exposes no
    # SoC, and deriving a percentage from dispatch would be a made-up number.
    card_battery = build_metric_card(
        title=state.text("ov_kpi_battery"),
        value="—",
        unit="kW",
        icon=ft.Icons.BATTERY_CHARGING_FULL,
        accent_color="#10B981",
        subtitle="Жүктелуде…",
        value_ref=ref_batt,
        subtitle_ref=ref_batt_sub,
    )

    kpi_grid = ft.Column(
        [
            ft.Row([ft.Container(card_solar, expand=True), ft.Container(card_wind, expand=True)], spacing=10),
            ft.Row([ft.Container(card_load, expand=True), ft.Container(card_battery, expand=True)], spacing=10),
        ],
        spacing=10,
    )

    # Interactive Solarman Telemetry Section — the header claims "Real-time",
    # so these three readings are pulled from /solarman/live rather than the
    # fixed 480.2 V / 14.5 A / 50.0 Hz that used to sit here.
    ref_pv_v, ref_pv_a, ref_hz = ft.Ref[ft.Text](), ft.Ref[ft.Text](), ft.Ref[ft.Text]()

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
                                ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["primary"], ref=ref_pv_v),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text("PV Ток:", size=11, color=c["text_secondary"]),
                                ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["accent"], ref=ref_pv_a),
                            ],
                            expand=True,
                        ),
                        ft.Column(
                            [
                                ft.Text("Желі жиілігі:", size=11, color=c["text_secondary"]),
                                ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["secondary"], ref=ref_hz),
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

    def _set(ref, value: str) -> None:
        if ref.current is not None:
            ref.current.value = value

    async def load_live_data() -> None:
        """Replace the placeholders with real figures from the backend."""
        # Solar / wind come from the same ML endpoint the Predictions screen
        # uses, seeded with the telemetry sliders the user has set.
        pred = await api_client.predict(
            state.irradiation,
            state.ambient_temp,
            state.module_temp,
            state.hour,
            state.day,
            state.month,
            state.wind_speed,
            state.wind_direction,
            state.theoretical_power,
            state.load_kw,
            state.battery_kw,
        )
        if pred:
            _set(ref_solar, f"{float(pred.get('solar_power', 0.0)):.1f}")
            _set(ref_wind, f"{float(pred.get('wind_power', 0.0)):.1f}")
            _set(ref_load, f"{float(pred.get('load_kw', state.load_kw)):.1f}")
            _set(ref_solar_sub, f"Ұсыныс: {pred.get('recommended_source', '—')}")
            _set(ref_wind_sub, f"Жел үлесі: {float(pred.get('wind_share', 0.0)) * 100:.0f}%")
            _set(ref_load_sub, f"Сенімділік: {float(pred.get('reliability_index', 0.0)) * 100:.0f}%")
            _set(ref_batt, f"{float(pred.get('battery_used', 0.0)):.1f}")
            _set(ref_batt_sub, f"Диспетчер · {state.battery_kw:.0f} kWh сыйымдылық")
        else:
            for r in (ref_solar, ref_wind, ref_load, ref_batt):
                _set(r, "—")
            for r in (ref_solar_sub, ref_wind_sub, ref_load_sub, ref_batt_sub):
                _set(r, "Деректер қолжетімсіз")

        live = await api_client.get_solarman_live()
        gen = (live or {}).get("generation") or {}
        dc = (gen.get("dc") or [{}])[0]
        ac = (gen.get("ac") or [{}])[0]
        if gen:
            _set(ref_pv_v, f"{dc.get('voltage_v', 0)} V")
            _set(ref_pv_a, f"{dc.get('current_a', 0)} A")
            _set(ref_hz, f"{ac.get('frequency_hz', 0)} Hz")
        else:
            for r in (ref_pv_v, ref_pv_a, ref_hz):
                _set(r, "—")

        page.update()

    # Deliberately not started here: build_overview_view runs while main() is
    # still swapping the splash screen for the dashboard, and a concurrent
    # page.update() from this task raced that transition. main() kicks off the
    # first load once the dashboard is actually mounted.
    view = ft.ListView(
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
    # main.py caches views in a dict and never rebuilds them, so without this
    # the "Real-time" panel would keep showing whatever it read at app launch.
    # on_nav_change re-runs whatever callable a view leaves here.
    view.data = load_live_data
    return view
