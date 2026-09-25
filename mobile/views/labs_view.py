"""
Microgrid lab view for EcoPredict AI Mobile.

Runs the dashboard's "microgrid dispatch" lab on the server: POST
/labs/microgrid-day drives src.simulation.microgrid.engine (PV array physics,
inverter curve, battery, grid) over a 24 h weather profile. The screen used to
compute `solar*0.85 + wind*0.70` and an "efficiency" of `92 + battery/1000*6`
on the phone — formulas with no physical meaning.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile import api_client as api_client_module
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]

# Weather profile id -> i18n key.
WEATHER_KEYS = {
    "sample": "lab_weather_sample",
    "synthetic": "lab_weather_synthetic",
    "open-meteo": "lab_weather_openmeteo",
}


def build_labs_view(page: ft.Page) -> ft.Control:
    """24 h PV + battery + grid simulation with the dashboard's lab parameters."""
    c = state.colors
    t = state.text

    def weather_label(source: str) -> str:
        return t(WEATHER_KEYS[source]) if source in WEATHER_KEYS else source

    def slider_row(label: str, unit: str, lo: float, hi: float, value: float, step: float) -> tuple:
        txt = ft.Text(f"{value:.0f} {unit}", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
        slider = ft.Slider(min=lo, max=hi, value=value, divisions=int((hi - lo) / step))

        def on_change(e):
            txt.value = f"{float(slider.value):.0f} {unit}"
            page.update()

        slider.on_change = on_change
        row = ft.Row([ft.Text(label, size=12), txt], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        return row, slider

    # Ranges and defaults match dashboard/views/labs.py (_lab_microgrid).
    row_panels, sl_panels = slider_row(t("lab_panels"), t("lab_unit_pcs"), 20, 400, 100, 10)
    row_batt, sl_batt = slider_row(t("lab_battery"), "kWh", 5, 300, 50, 5)
    row_load, sl_load = slider_row(t("lab_load"), "kW", 1, 50, 15, 1)
    row_inv, sl_inv = slider_row(t("lab_inverter"), "kW", 5, 100, 40, 5)

    dd_weather = ft.Dropdown(
        label=t("lab_weather"),
        value="sample",
        options=[ft.DropdownOption(key=k, text=weather_label(k)) for k in WEATHER_KEYS],
        dense=True,
    )

    txt_status = ft.Text("", size=12, color=c["error"], visible=False, selectable=True)
    txt_weather_used = ft.Text("", size=11, color=c["text_secondary"])
    progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    def kpi(title: str, color: str) -> tuple:
        value = ft.Text("—", size=17, weight=ft.FontWeight.BOLD, color=color)
        card = ft.Container(
            content=ft.Column([ft.Text(title, size=11, color=c["text_secondary"]), value], spacing=2),
            padding=10,
            border_radius=12,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
            expand=True,
        )
        return card, value

    card_pv, val_pv = kpi(t("lab_kpi_pv"), c["accent"])
    card_load, val_load = kpi(t("lab_kpi_load"), c["text_primary"])
    card_imp, val_imp = kpi(t("lab_kpi_import"), c["error"])
    card_exp, val_exp = kpi(t("lab_kpi_export"), c["secondary"])
    card_sc, val_sc = kpi(t("lab_kpi_self"), c["success"])
    card_soc, val_soc = kpi(t("lab_kpi_soc"), c["primary"])

    chart = ft.Row([], scroll=ft.ScrollMode.ALWAYS, spacing=6, vertical_alignment=ft.CrossAxisAlignment.END)

    def render_chart(hours: list) -> None:
        peak = max([h.get("pv_kw", 0.0) for h in hours] + [h.get("load_kw", 0.0) for h in hours] + [0.1])
        bars = []
        for h in hours:
            pv_h = int(max(2, h.get("pv_kw", 0.0) / peak * 110))
            load_h = int(max(2, h.get("load_kw", 0.0) / peak * 110))
            bars.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Container(width=6, height=pv_h, bgcolor=c["accent"], border_radius=3),
                                ft.Container(width=6, height=load_h, bgcolor=c["text_secondary"], border_radius=3),
                            ],
                            spacing=1,
                            vertical_alignment=ft.CrossAxisAlignment.END,
                        ),
                        ft.Text(f"{int(h.get('hour', 0)):02d}", size=9, color=c["text_secondary"]),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                )
            )
        chart.controls = bars

    async def run(e=None) -> None:
        progress.visible = True
        txt_status.visible = False
        page.update()
        res = await api_client.microgrid_day(
            num_panels=int(sl_panels.value or 100),
            battery_kwh=float(sl_batt.value or 50),
            load_kw=float(sl_load.value or 15),
            inverter_kw=float(sl_inv.value or 40),
            weather=dd_weather.value or "sample",
        )
        progress.visible = False

        if res is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            txt_status.value, txt_status.visible = t("lab_err_failed", reason=reason), True
            page.update()
            return

        s = res.get("summary") or {}
        val_pv.value = f"{float(s.get('pv_kwh') or 0):.1f} kWh"
        val_load.value = f"{float(s.get('load_kwh') or 0):.1f} kWh"
        val_imp.value = f"{float(s.get('import_kwh') or 0):.1f} kWh"
        val_exp.value = f"{float(s.get('export_kwh') or 0):.1f} kWh"
        val_sc.value = f"{float(s.get('self_consumption_pct') or 0):.1f} %"
        val_soc.value = f"{float(s.get('final_soc') or 0) * 100:.0f} %"

        requested = dd_weather.value or "sample"
        used = str(res.get("weather_source") or requested)
        note = t("lab_weather_used", source=weather_label(used))
        if used != requested:
            note += " " + t("lab_weather_fallback", source=weather_label(requested))
        txt_weather_used.value = note
        render_chart(res.get("hours") or [])
        page.update()

    btn_run = ft.Button(
        content=ft.Row([ft.Text(t("lab_btn_run")), progress], tight=True, spacing=8),
        icon=ft.Icons.PLAY_ARROW,
        style=ft.ButtonStyle(bgcolor=c["primary"], color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=run,
    )

    params = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.SCIENCE, color=c["primary"]), ft.Text(t("lab_params"), weight=ft.FontWeight.BOLD)]),
                row_panels, sl_panels,
                row_batt, sl_batt,
                row_load, sl_load,
                row_inv, sl_inv,
                dd_weather,
                btn_run,
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    chart_card = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(t("lab_chart_title"), size=13, weight=ft.FontWeight.BOLD),
                        ft.Row(
                            [
                                ft.Container(width=10, height=10, bgcolor=c["accent"], border_radius=5),
                                ft.Text("PV", size=10, color=c["text_secondary"]),
                                ft.Container(width=10, height=10, bgcolor=c["text_secondary"], border_radius=5),
                                ft.Text(t("lab_legend_load"), size=10, color=c["text_secondary"]),
                            ],
                            spacing=4,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    wrap=True,
                ),
                txt_weather_used,
                chart,
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    view = ft.ListView(
        controls=[
            ft.Text(t("lab_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("lab_subtitle"), size=11, color=c["text_secondary"]),
            params,
            txt_status,
            ft.Row([card_pv, card_load], spacing=8),
            ft.Row([card_imp, card_exp], spacing=8),
            ft.Row([card_sc, card_soc], spacing=8),
            chart_card,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
        expand=True,
    )
    view.data = run
    return view
