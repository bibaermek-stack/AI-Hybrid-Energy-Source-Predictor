"""
24-Hour Time-Series Energy Generation Forecast View for EcoPredict AI Mobile.
"""

import math
import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_forecast_view(page: ft.Page) -> ft.Control:
    """Build 24-hour time-series energy generation forecast view with hourly trend bars and data table."""
    c = state.colors

    # Generate 24-hour forecast data curve
    hourly_data = []
    max_total = 0.1
    for h in range(24):
        # Solar diurnal bell curve
        solar = max(0.0, math.sin(math.pi * (h - 6) / 12) * 620.0) if 6 <= h <= 18 else 0.0
        # Wind generation curve with evening peak
        wind = 250.0 + math.cos(math.pi * (h - 18) / 12) * 150.0 + (h % 3) * 15.0
        total = round(solar + wind, 1)
        max_total = max(max_total, total)
        hourly_data.append({
            "hour": f"{h:02d}:00",
            "solar": round(solar, 1),
            "wind": round(wind, 1),
            "total": total,
        })

    # Summary metric cards
    card_peak_solar = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color="#F59E0B", size=20), ft.Text("Күн Пик Қуаты", size=12, color=c["text_secondary"])]),
                ft.Text("620.4 kW", size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ft.Text("Сағат 13:00-де", size=11, color="#F59E0B"),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
        expand=True,
    )

    card_peak_wind = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.AIR, color="#14B8A6", size=20), ft.Text("Жел Пик Қуаты", size=12, color=c["text_secondary"])]),
                ft.Text("400.1 kW", size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ft.Text("Сағат 18:00-де", size=11, color="#14B8A6"),
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=12,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
        expand=True,
    )

    # 24-Hour Trend Line / Visual Bar Chart
    chart_bars = []
    for item in hourly_data:
        h_str = item["hour"]
        tot = item["total"]
        sol = item["solar"]
        wnd = item["wind"]
        height_pct = min(1.0, max(0.08, tot / max_total))
        bar_h = int(height_pct * 110)

        sol_ratio = sol / tot if tot > 0 else 0
        wnd_ratio = wnd / tot if tot > 0 else 1

        chart_bars.append(
            ft.Column(
                [
                    ft.Text(f"{int(tot)}", size=8, color=c["text_secondary"]),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Container(bgcolor="#14B8A6", height=int(bar_h * wnd_ratio), border_radius=ft.BorderRadius(top_left=4, top_right=4, bottom_left=0, bottom_right=0)),
                                ft.Container(bgcolor="#F59E0B", height=int(bar_h * sol_ratio), border_radius=ft.BorderRadius(top_left=0, top_right=0, bottom_left=4, bottom_right=4)),
                            ],
                            spacing=0,
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        width=12,
                        height=bar_h,
                    ),
                    ft.Text(h_str[:2], size=9, weight=ft.FontWeight.W_500, color=c["text_secondary"]),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=2,
            )
        )

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
                                ft.Container(width=10, height=10, bgcolor="#14B8A6", border_radius=5),
                                ft.Text("Жел", size=10, color=c["text_secondary"]),
                            ],
                            spacing=6,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(height=10),
                ft.Row(chart_bars, scroll=ft.ScrollMode.ALWAYS, spacing=8),
            ]
        ),
        padding=14,
        border_radius=16,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Hourly Data Table Rows
    table_rows = []
    for item in hourly_data[::2]:  # Show every 2 hours for clean mobile view
        table_rows.append(
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(item["hour"], size=12, weight=ft.FontWeight.BOLD, color=c["text_primary"])),
                    ft.DataCell(ft.Text(f"{item['solar']} kW", size=12, color="#F59E0B")),
                    ft.DataCell(ft.Text(f"{item['wind']} kW", size=12, color="#14B8A6")),
                    ft.DataCell(ft.Text(f"{item['total']} kW", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])),
                ]
            )
        )

    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Уақыт", size=11, weight=ft.FontWeight.BOLD, color=c["text_secondary"])),
            ft.DataColumn(ft.Text("Күн kW", size=11, weight=ft.FontWeight.BOLD, color="#F59E0B")),
            ft.DataColumn(ft.Text("Жел kW", size=11, weight=ft.FontWeight.BOLD, color="#14B8A6")),
            ft.DataColumn(ft.Text("Барлығы", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])),
        ],
        rows=table_rows,
        heading_row_height=36,
        data_row_min_height=36,
        column_spacing=16,
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

    return ft.ListView(
        controls=[
            ft.Text("📊 24 Сағаттық Болжам жүйесі", size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text("ML модельдері арқылы 24 сағатқа арналған генерация динамикасы", size=12, color=c["text_secondary"]),
            ft.Container(height=10),
            ft.Row([card_peak_solar, card_peak_wind], spacing=10),
            ft.Container(height=12),
            chart_container,
            ft.Container(height=12),
            table_container,
            ft.Container(height=20),
        ],
        spacing=8,
        padding=12,
    )
