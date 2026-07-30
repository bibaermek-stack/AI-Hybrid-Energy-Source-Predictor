import asyncio
import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_forecast_view(page: ft.Page) -> ft.Control:
    """Build energy forecasting and prediction screen."""
    c = state.colors

    # Value Labels
    txt_irrad_lbl = ft.Text(f"{state.irradiation:.0f} W/m²", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_temp_lbl = ft.Text(f"{state.ambient_temp:.0f} °C", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_module_lbl = ft.Text(f"{state.module_temp:.0f} °C", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_wind_spd_lbl = ft.Text(f"{state.wind_speed:.1f} m/s", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_wind_dir_lbl = ft.Text(f"{state.wind_direction:.0f} °", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_theor_lbl = ft.Text(f"{state.theoretical_power:.0f} kWh", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])

    # Output text controls
    txt_solar_val = ft.Text("420.5 kW", size=18, weight=ft.FontWeight.BOLD, color=c["accent"])
    txt_wind_val = ft.Text("400.1 kW", size=18, weight=ft.FontWeight.BOLD, color=c["secondary"])
    txt_total_val = ft.Text("820.6 kW", size=24, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_source = ft.Text("💡 Ұсынылатын көз: Гибридті Күн + Жел", size=13, weight=ft.FontWeight.W_600, color=c["text_primary"])
    progress_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2, color="#FFFFFF")

    # Input controls with live on_change
    def on_irrad_change(e):
        txt_irrad_lbl.value = f"{sl_irrad.value:.0f} W/m²"
        page.update()

    def on_temp_change(e):
        txt_temp_lbl.value = f"{sl_temp.value:.0f} °C"
        page.update()

    def on_module_change(e):
        txt_module_lbl.value = f"{sl_module.value:.0f} °C"
        page.update()

    def on_wind_spd_change(e):
        txt_wind_spd_lbl.value = f"{sl_wind_spd.value:.1f} m/s"
        page.update()

    def on_wind_dir_change(e):
        txt_wind_dir_lbl.value = f"{sl_wind_dir.value:.0f} °"
        page.update()

    def on_theor_change(e):
        txt_theor_lbl.value = f"{sl_theor.value:.0f} kWh"
        page.update()

    sl_irrad = ft.Slider(min=0, max=1500, value=state.irradiation, divisions=30, label="{value} W/m²", on_change=on_irrad_change)
    sl_temp = ft.Slider(min=-10, max=60, value=state.ambient_temp, divisions=70, label="{value} °C", on_change=on_temp_change)
    sl_module = ft.Slider(min=-10, max=80, value=state.module_temp, divisions=90, label="{value} °C", on_change=on_module_change)
    sl_wind_spd = ft.Slider(min=0, max=25, value=state.wind_speed, divisions=50, label="{value} m/s", on_change=on_wind_spd_change)
    sl_wind_dir = ft.Slider(min=0, max=360, value=state.wind_direction, divisions=36, label="{value} °", on_change=on_wind_dir_change)
    sl_theor = ft.Slider(min=0, max=2000, value=state.theoretical_power, divisions=40, label="{value} kWh", on_change=on_theor_change)

    async def on_calculate(e=None):
        progress_ring.visible = True
        page.update()

        # Update state
        state.irradiation = sl_irrad.value or 900.0
        state.ambient_temp = sl_temp.value or 30.0
        state.module_temp = sl_module.value or 38.0
        state.wind_speed = sl_wind_spd.value or 6.5
        state.wind_direction = sl_wind_dir.value or 250.0
        state.theoretical_power = sl_theor.value or 750.0

        res = await api_client.predict(
            irradiation=state.irradiation,
            temperature=state.ambient_temp,
            module=state.module_temp,
            hour=state.hour,
            day=state.day,
            month=state.month,
            wind_speed=state.wind_speed,
            direction=state.wind_direction,
            theoretical=state.theoretical_power,
            load_kw=state.load_kw,
            battery_kw=state.battery_kw,
            solar_cost_per_kwh=state.solar_cost,
            wind_cost_per_kwh=state.wind_cost,
            strategy=state.strategy,
        )

        s_power = res.get('solar_power', 420.5)
        w_power = res.get('wind_power', 400.1)
        t_power = res.get('total_power', s_power + w_power)
        src = res.get('recommended_source', 'Hybrid Renewable')

        txt_solar_val.value = f"{s_power:.1f} kW"
        txt_wind_val.value = f"{w_power:.1f} kW"
        txt_total_val.value = f"{t_power:.1f} kW"
        txt_source.value = f"💡 Ұсынылатын көз: {src}"

        progress_ring.visible = False
        page.update()

    # Trigger initial prediction on view load safely
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(on_calculate(None))
    except RuntimeError:
        pass

    btn_calc = ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.CALCULATE, color="#FFFFFF"),
                ft.Text(state.text("fc_btn"), color="#FFFFFF", weight=ft.FontWeight.BOLD),
                progress_ring,
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_calculate,
    )

    # Solar Section
    solar_box = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color=c["accent"]), ft.Text(state.text("fc_solar_params"), weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                ft.Row([ft.Text(state.text("fc_irradiation"), size=11, color=c["text_secondary"]), txt_irrad_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_irrad,
                ft.Row([ft.Text(state.text("fc_temp"), size=11, color=c["text_secondary"]), txt_temp_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_temp,
                ft.Row([ft.Text(state.text("fc_module_temp"), size=11, color=c["text_secondary"]), txt_module_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_module,
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Wind Section
    wind_box = ft.Container(
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.AIR, color=c["secondary"]), ft.Text(state.text("fc_wind_params"), weight=ft.FontWeight.BOLD, color=c["text_primary"])]),
                ft.Row([ft.Text(state.text("fc_wind_speed"), size=11, color=c["text_secondary"]), txt_wind_spd_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_wind_spd,
                ft.Row([ft.Text(state.text("fc_wind_dir"), size=11, color=c["text_secondary"]), txt_wind_dir_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_wind_dir,
                ft.Row([ft.Text(state.text("fc_theoretical"), size=11, color=c["text_secondary"]), txt_theor_lbl], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                sl_theor,
            ],
            spacing=4,
        ),
        padding=12,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    # Result Section
    results_box = ft.Container(
        content=ft.Column(
            [
                ft.Text(state.text("fc_result_total"), size=12, color=c["text_secondary"]),
                txt_total_val,
                ft.Divider(height=1, color=c["card_border"]),
                ft.Row(
                    [
                        ft.Column([ft.Text(state.text("fc_result_solar"), size=11, color=c["text_secondary"]), txt_solar_val]),
                        ft.Column([ft.Text(state.text("fc_result_wind"), size=11, color=c["text_secondary"]), txt_wind_val]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND,
                ),
                ft.Container(height=4),
                txt_source,
            ],
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["primary"]),
    )

    return ft.ListView(
        controls=[
            ft.Text("📈 " + state.text("fc_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            solar_box,
            wind_box,
            btn_calc,
            results_box,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
    )
