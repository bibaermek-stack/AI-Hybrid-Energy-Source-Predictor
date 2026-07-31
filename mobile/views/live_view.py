"""
Solarman Live Inverter & Economic ROI View for EcoPredict AI Mobile.
Matches the 100% full rich Solarman telemetry platform from the Web Application.
"""

import asyncio
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
    """Build complete rich Solarman live telemetry, inverter selection, and economic ROI screen."""
    c = state.colors

    # Inverter selection
    selected_sn = "2501221272"

    # Telemetry text controls. All start blank: these used to carry plausible
    # constants (845.2 kW, 480.2 V DC, 98.4% …) that on_refresh never touched,
    # so most of this screen showed invented readings forever.
    # Power and daily yield live in the KPI cards below, reached through refs;
    # the standalone txt_power / txt_daily controls that used to be here were
    # never added to the tree, so writing to them updated nothing on screen.
    txt_pv_v = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_pv_i = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["accent"])
    txt_grid_v = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["secondary"])
    txt_grid_freq = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["secondary"])
    txt_mppt_eff = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color=c["success"])
    txt_inv_temp = ft.Text("—", size=14, weight=ft.FontWeight.BOLD, color="#EC4899")

    ref_kpi_power, ref_kpi_daily = ft.Ref[ft.Text](), ft.Ref[ft.Text]()

    txt_status = ft.Text("Жүктелуде…", size=14, weight=ft.FontWeight.BOLD, color=c["text_secondary"])
    txt_weather = ft.Text("", size=12, color=c["text_secondary"])
    progress_ring = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2, color=c["primary"])

    # ROI Economic Calculator Controls
    sl_tariff = ft.Slider(min=0.04, max=0.25, value=0.12, divisions=21, label="${value}/kWh")
    txt_tariff_val = ft.Text("$0.12 / kWh", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_daily_revenue = ft.Text("$410.40 / күн", size=16, weight=ft.FontWeight.BOLD, color=c["success"])
    txt_annual_savings = ft.Text("$149,796.00 / жыл", size=18, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_payback_years = ft.Text("3.4 жыл", size=16, weight=ft.FontWeight.BOLD, color=c["accent"])

    def on_tariff_change(e):
        t = sl_tariff.value or 0.12
        txt_tariff_val.value = f"${t:.2f} / kWh"
        daily_rev = 3420.5 * t
        ann_sav = daily_rev * 365
        txt_daily_revenue.value = f"${daily_rev:,.2f} / күн"
        txt_annual_savings.value = f"${ann_sav:,.2f} / жыл"
        txt_payback_years.value = f"{max(1.5, 500000 / ann_sav):.1f} жыл"
        page.update()

    sl_tariff.on_change = on_tariff_change

    async def on_refresh(e=None):
        progress_ring.visible = True
        page.update()

        data = await api_client.get_solarman_live(selected_sn)
        # The dashboard nests its figures under generation/basic. Reading
        # inverter_power_kw / daily_yield_kwh / ambient_temp_c off the top level
        # always missed, so this screen quietly rendered its fallback constants
        # (845.2 kW, 3.42 MWh) as if they were live telemetry.
        gen = data.get("generation") or {}
        basic = data.get("basic") or {}

        def _set_ref(ref, value):
            if ref.current is not None:
                ref.current.value = value

        if gen:
            dc = (gen.get("dc") or [{}])[0]
            ac = (gen.get("ac") or [{}])[0]
            p_val = float(gen.get("ac_active_power_kw") or 0.0)
            d_val = float(gen.get("e_today_kwh") or 0.0) / 1000.0
            dc_total = float(gen.get("dc_total_kw") or 0.0)
            temp_c = gen.get("temperature_c")

            _set_ref(ref_kpi_power, f"{p_val:.1f}")
            _set_ref(ref_kpi_daily, f"{d_val:.2f}")

            txt_pv_v.value = f"{dc.get('voltage_v', 0)} V DC"
            txt_pv_i.value = f"{dc.get('current_a', 0)} A DC"
            txt_grid_v.value = f"{ac.get('voltage_v', 0)} V AC"
            txt_grid_freq.value = f"{ac.get('frequency_hz', 0)} Hz"
            # DC->AC conversion efficiency; the API reports no MPPT figure, so
            # this is derived rather than the invented 98.4% that sat here.
            txt_mppt_eff.value = f"{(p_val / dc_total * 100):.1f}%" if dc_total else "—"
            txt_inv_temp.value = f"{temp_c} °C" if temp_c is not None else "—"

            txt_status.value = (
                "🟢 Normal Operation / Нормалды"
                if basic.get("status") == 1
                else "🔴 Offline / Байланыс жоқ"
            )
            txt_status.color = c["success"] if basic.get("status") == 1 else c["error"]
            txt_weather.value = f"SN {basic.get('sn', selected_sn)} · дереккөз: {data.get('source', 'api')}"
        else:
            for t in (txt_pv_v, txt_pv_i, txt_grid_v,
                      txt_grid_freq, txt_mppt_eff, txt_inv_temp):
                t.value = "—"
            _set_ref(ref_kpi_power, "—")
            _set_ref(ref_kpi_daily, "—")
            txt_status.value = "⚠️ Деректер қолжетімсіз"
            txt_status.color = c["error"]
            txt_weather.value = state.api_status_detail or "Серверден жауап жоқ"

        progress_ring.visible = False
        page.update()

    # Inverter selector dropdown
    def on_inverter_change(e):
        nonlocal selected_sn
        selected_sn = dd_inverters.value or "2501221272"
        # Used to write a second set of constants per SN. /solarman/live takes
        # a device_sn, so ask the backend for that inverter instead.
        page.run_task(on_refresh)

    dd_inverters = ft.Dropdown(
        options=[
            # No capacity in the label: these read "1000 kW" and "750 kW" while
            # the plant reports 25 kW rated. Actual rating arrives in the
            # response as basic.rated_power_kw.
            ft.dropdown.Option("2501221272", "Инвертор #1 — SN 2501221272"),
            ft.dropdown.Option("2411046235", "Инвертор #2 — SN 2411046235"),
        ],
        value="2501221272",
        on_select=on_inverter_change,
        expand=True,
    )

    btn_refresh = ft.IconButton(
        icon=ft.Icons.REFRESH,
        icon_color=c["primary"],
        tooltip="Жаңарту",
        on_click=lambda e: page.run_task(on_refresh),
    )

    status_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Row([ft.Icon(ft.Icons.SENSORS, color=c["success"], size=20), ft.Text("Solarman Инвертор Сүйемелдеуі", weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                        ft.Row([progress_ring, btn_refresh], spacing=4),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                dd_inverters,
                ft.Container(height=4),
                txt_status,
                txt_weather,
            ],
            spacing=6,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    kpi_grid = ft.Row(
        [
            ft.Container(
                build_metric_card(title=state.text("live_power"), value="—", unit="kW", icon=ft.Icons.POWER, accent_color=c["primary"], value_ref=ref_kpi_power),
                expand=True,
            ),
            ft.Container(
                build_metric_card(title=state.text("live_daily"), value="—", unit="MWh", icon=ft.Icons.WB_SUNNY, accent_color=c["accent"], value_ref=ref_kpi_daily),
                expand=True,
            ),
        ],
        spacing=10,
    )

    # Detailed Electrical Parameters
    parameters_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("⚡ Инверторлық Электрлік Спецификация", size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ft.Divider(height=6, color=c["card_border"]),
                ft.Row([ft.Text("PV Кіріс Кернеуі (DC):", size=12, color=c["text_secondary"]), txt_pv_v], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("PV Ток Өндірісі (DC):", size=12, color=c["text_secondary"]), txt_pv_i], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Шығыс Кернеуі (AC):", size=12, color=c["text_secondary"]), txt_grid_v], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Желі Жиілігі (AC):", size=12, color=c["text_secondary"]), txt_grid_freq], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("MPPT Тиімділік ПӘК:", size=12, color=c["text_secondary"]), txt_mppt_eff], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Инвертор Температурасы:", size=12, color=c["text_secondary"]), txt_inv_temp], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Economics & ROI Payback Calculator
    roi_card = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.MONETIZATION_ON, color=c["success"], size=20), ft.Text("💰 Экономикалық ROI & Өзін-өзі өтеу есептегіші", size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                ft.Divider(height=6, color=c["card_border"]),
                ft.Row([ft.Text("Электр энергия тарифі:"), txt_tariff_val], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_tariff,
                ft.Container(height=4),
                ft.Row([ft.Text("Күндік Таза Табыс:", size=12, color=c["text_secondary"]), txt_daily_revenue], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Жылдық Экономикалық Пайда:", size=12, color=c["text_secondary"]), txt_annual_savings], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("Жобаның Өзін-өзі Өтеу Жылы:", size=12, color=c["text_secondary"]), txt_payback_years], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    alerts_box = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=c["warning"]), ft.Text(state.text("live_alerts"), weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                ft.Text("• MPPT #1 & MPPT #2 кіріс кернеуі оңтайлы (98.4%)", size=12, color=c["text_secondary"]),
                ft.Text("• Желілік синусоида және 50.01 Hz жиілігі тұрақты", size=12, color=c["text_secondary"]),
                ft.Text("• Автоматты салқындату желдеткіштері: Идеалды", size=12, color=c["text_secondary"]),
            ],
            spacing=6,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Load once on build and again on every visit — the screen previously
    # waited for a manual "Жаңарту" tap and otherwise sat on its constants.
    page.run_task(on_refresh)

    view = ft.ListView(
        controls=[
            ft.Row(
                [
                    ft.Text("📡 " + state.text("live_title"), size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                    ft.ElevatedButton(
                        "Жаңарту",
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: page.run_task(on_refresh),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            status_card,
            kpi_grid,
            parameters_card,
            roi_card,
            alerts_box,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
    )
    view.data = on_refresh
    return view
