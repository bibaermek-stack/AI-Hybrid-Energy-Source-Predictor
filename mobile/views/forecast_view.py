"""
24-Hour Time-Series Energy Generation Forecast View for EcoPredict AI Mobile.

Figures come from GET /solarman/forecast, which runs the RandomForest model
over the Turkistan weather forecast. This screen used to draw a math.sin bell
curve and a fixed "620.4 kW peak at 13:00" — numbers that looked like a
forecast but were generated on the phone.

The endpoint forecasts solar only, so there is no wind series here; adding one
would mean going back to making it up.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_forecast_view(page: ft.Page) -> ft.Control:
    """24-hour solar generation forecast: peak summary, hourly bars, hourly table."""
    c = state.colors

    ref_peak = ft.Ref[ft.Text]()
    ref_peak_at = ft.Ref[ft.Text]()
    ref_total = ft.Ref[ft.Text]()
    ref_total_sub = ft.Ref[ft.Text]()
    ref_chart = ft.Ref[ft.Row]()
    ref_table = ft.Ref[ft.DataTable]()
    ref_status = ft.Ref[ft.Text]()

    def summary_card(title: str, icon, accent: str, value_ref, sub_ref) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row([
                        ft.Icon(icon, color=accent, size=20),
                        ft.Text(title, size=12, color=c["text_secondary"]),
                    ]),
                    ft.Text("—", size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"], ref=value_ref),
                    ft.Text("Жүктелуде…", size=11, color=accent, ref=sub_ref),
                ],
                spacing=4,
            ),
            padding=12,
            border_radius=12,
            bgcolor=c["surface_variant"],
            border=ft.Border.all(1, c["card_border"]),
            expand=True,
        )

    card_peak = summary_card("Күн Пик Қуаты", ft.Icons.WB_SUNNY, "#F59E0B", ref_peak, ref_peak_at)
    card_total = summary_card("Тәуліктік Өндіріс", ft.Icons.BATTERY_CHARGING_FULL, "#10B981", ref_total, ref_total_sub)

    chart_container = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("📈 24 Сағаттық Болжам Графигі (kW)", size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                        ft.Row(
                            [
                                ft.Container(width=10, height=10, bgcolor="#F59E0B", border_radius=5),
                                ft.Text("Күн", size=10, color=c["text_secondary"]),
                            ],
                            spacing=6,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.Text("Жүктелуде…", size=12, color=c["text_secondary"], ref=ref_status),
                ft.Row([], scroll=ft.ScrollMode.ALWAYS, spacing=8, ref=ref_chart),
            ]
        ),
        padding=14,
        border_radius=16,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Уақыт", size=11, weight=ft.FontWeight.BOLD, color=c["text_secondary"])),
            ft.DataColumn(ft.Text("Қуат kW", size=11, weight=ft.FontWeight.BOLD, color="#F59E0B")),
            ft.DataColumn(ft.Text("Радиация", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])),
            ft.DataColumn(ft.Text("Бұлт %", size=11, weight=ft.FontWeight.BOLD, color=c["text_secondary"])),
            ft.DataColumn(ft.Text("t°C", size=11, weight=ft.FontWeight.BOLD, color="#14B8A6")),
        ],
        rows=[],
        heading_row_height=36,
        data_row_min_height=36,
        column_spacing=16,
        ref=ref_table,
    )

    table_container = ft.Container(
        content=ft.Column(
            [
                ft.Text("📋 24h Сағаттық Болжам Кестесі", size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ft.Container(height=6),
                ft.Row([data_table], scroll=ft.ScrollMode.ALWAYS),
            ]
        ),
        padding=14,
        border_radius=16,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    def _set(ref, value: str) -> None:
        if ref.current is not None:
            ref.current.value = value

    async def load_forecast() -> None:
        rows = await api_client.get_forecast()

        if not rows:
            _set(ref_peak, "—")
            _set(ref_peak_at, "Қолжетімсіз")
            _set(ref_total, "—")
            _set(ref_total_sub, "Қолжетімсіз")
            _set(
                ref_status,
                "Болжам алынбады. Серверде WEATHERAPI_KEY бапталмаған болуы мүмкін.",
            )
            if ref_chart.current is not None:
                ref_chart.current.controls = []
            if ref_table.current is not None:
                ref_table.current.rows = []
            page.update()
            return

        powers = [float(r.get("predicted_power_kw") or 0.0) for r in rows]
        peak = max(powers)
        peak_row = rows[powers.index(peak)]
        # Hourly samples, so kW per hour sums directly to kWh.
        total_kwh = sum(powers)

        _set(ref_peak, f"{peak:.1f} kW")
        _set(ref_peak_at, f"Сағат {int(peak_row.get('hour', 0)):02d}:00-де")
        _set(ref_total, f"{total_kwh:.0f} kWh")
        _set(ref_total_sub, f"{len(rows)} сағаттық болжам")
        _set(ref_status, "")
        if ref_status.current is not None:
            ref_status.current.visible = False

        scale = max(peak, 0.1)
        bars = []
        for row, power in zip(rows, powers):
            bar_h = int(max(0.04, power / scale) * 110)
            bars.append(
                ft.Column(
                    [
                        ft.Text(f"{power:.0f}", size=8, color=c["text_secondary"]),
                        ft.Container(bgcolor="#F59E0B", width=12, height=bar_h, border_radius=4),
                        ft.Text(f"{int(row.get('hour', 0)):02d}", size=9, weight=ft.FontWeight.W_500, color=c["text_secondary"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                )
            )
        if ref_chart.current is not None:
            ref_chart.current.controls = bars

        table_rows = []
        for row in rows[::2]:  # every second hour keeps the mobile table readable
            table_rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(f"{int(row.get('hour', 0)):02d}:00", size=12, weight=ft.FontWeight.BOLD, color=c["text_primary"])),
                        ft.DataCell(ft.Text(f"{float(row.get('predicted_power_kw') or 0):.1f}", size=12, color="#F59E0B")),
                        ft.DataCell(ft.Text(f"{float(row.get('irradiance') or 0):.0f}", size=12, color=c["primary"])),
                        ft.DataCell(ft.Text(f"{float(row.get('cloud_cover') or 0):.0f}", size=12, color=c["text_secondary"])),
                        ft.DataCell(ft.Text(f"{float(row.get('temperature') or 0):.1f}", size=12, color="#14B8A6")),
                    ]
                )
            )
        if ref_table.current is not None:
            ref_table.current.rows = table_rows

        page.update()

    view = ft.ListView(
        controls=[
            ft.Text("📊 24 Сағаттық Болжам жүйесі", size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text("Түркістан ауа райы болжамы бойынша RandomForest моделі", size=12, color=c["text_secondary"]),
            ft.Container(height=10),
            ft.Row([card_peak, card_total], spacing=10),
            ft.Container(height=12),
            chart_container,
            ft.Container(height=12),
            table_container,
            ft.Container(height=20),
        ],
        spacing=8,
        padding=12,
        expand=True,
    )
    # Picked up by on_nav_change so the forecast refreshes on each visit.
    view.data = load_forecast
    return view
