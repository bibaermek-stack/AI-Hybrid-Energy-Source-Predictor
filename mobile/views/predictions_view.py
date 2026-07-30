import asyncio
import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_predictions_view(page: ft.Page) -> ft.Control:
    """Build interactive ML predictions view with power curve visualization."""
    c = state.colors

    # Labels
    txt_irrad = ft.Text(f"{state.irradiation:.0f} W/m²", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_temp = ft.Text(f"{state.ambient_temp:.0f} °C", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_module = ft.Text(f"{state.module_temp:.0f} °C", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_wind_spd = ft.Text(f"{state.wind_speed:.1f} m/s", size=11, weight=ft.FontWeight.BOLD, color=c["primary"])

    # Output text
    txt_solar = ft.Text("420.5 kW", size=20, weight=ft.FontWeight.BOLD, color=c["accent"])
    txt_wind = ft.Text("400.1 kW", size=20, weight=ft.FontWeight.BOLD, color=c["secondary"])
    txt_total = ft.Text("820.6 kW", size=24, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_rec = ft.Text("💡 Ұсыныс: Күн + Жел аралас өндірісі оңтайлы", size=12, weight=ft.FontWeight.W_600, color=c["text_primary"])
    progress_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2, color="#FFFFFF")

    # Sliders
    sl_irrad = ft.Slider(min=0, max=1500, value=state.irradiation, divisions=30, label="{value} W/m²", on_change=lambda e: (setattr(txt_irrad, 'value', f'{sl_irrad.value:.0f} W/m²'), page.update()))
    sl_temp = ft.Slider(min=-10, max=60, value=state.ambient_temp, divisions=70, label="{value} °C", on_change=lambda e: (setattr(txt_temp, 'value', f'{sl_temp.value:.0f} °C'), page.update()))
    sl_module = ft.Slider(min=-10, max=80, value=state.module_temp, divisions=90, label="{value} °C", on_change=lambda e: (setattr(txt_module, 'value', f'{sl_module.value:.0f} °C'), page.update()))
    sl_wind_spd = ft.Slider(min=0, max=25, value=state.wind_speed, divisions=50, label="{value} m/s", on_change=lambda e: (setattr(txt_wind_spd, 'value', f'{sl_wind_spd.value:.1f} m/s'), page.update()))

    # Power breakdown visual bars
    bar_solar = ft.Container(width=140, height=12, bgcolor=c["accent"], border_radius=6)
    bar_wind = ft.Container(width=130, height=12, bgcolor=c["secondary"], border_radius=6)

    async def run_prediction(e=None):
        progress_ring.visible = True
        page.update()

        state.irradiation = sl_irrad.value or 900.0
        state.ambient_temp = sl_temp.value or 30.0
        state.module_temp = sl_module.value or 38.0
        state.wind_speed = sl_wind_spd.value or 6.5

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
        )

        s_val = float(res.get('solar_power', 420.5))
        w_val = float(res.get('wind_power', 400.1))
        t_val = float(res.get('total_power', s_val + w_val))

        txt_solar.value = f"{s_val:.1f} kW"
        txt_wind.value = f"{w_val:.1f} kW"
        txt_total.value = f"{t_val:.1f} kW"

        # Update bar widths proportionally
        max_p = max(100.0, t_val)
        bar_solar.width = min(220.0, max(20.0, (s_val / max_p) * 220))
        bar_wind.width = min(220.0, max(20.0, (w_val / max_p) * 220))

        progress_ring.visible = False
        page.update()

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(run_prediction(None))
    except RuntimeError:
        pass

    btn_calc = ft.ElevatedButton(
        content=ft.Row(
            [ft.Icon(ft.Icons.AUTO_AWESOME, color="#FFFFFF"), ft.Text("ML Болжам жасау", color="#FFFFFF", weight=ft.FontWeight.BOLD), progress_ring],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        ),
        style=ft.ButtonStyle(bgcolor=c["primary"], shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=run_prediction,
    )

    return ft.ListView(
        controls=[
            ft.Text("⚡ ML Энергия Болжау Сервисі", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.WB_SUNNY, color=c["accent"]), ft.Text("Күн Батареясы Тізімі", weight=ft.FontWeight.BOLD)]),
                        ft.Row([ft.Text("Радиация:"), txt_irrad], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_irrad,
                        ft.Row([ft.Text("Ауа темп.:"), txt_temp], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_temp,
                        ft.Row([ft.Text("Панель темп.:"), txt_module], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_module,
                    ],
                    spacing=4,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(1, c["card_border"]),
            ),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.AIR, color=c["secondary"]), ft.Text("Жел Генераторы", weight=ft.FontWeight.BOLD)]),
                        ft.Row([ft.Text("Жел жылдамдығы:"), txt_wind_spd], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_wind_spd,
                    ],
                    spacing=4,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(1, c["card_border"]),
            ),
            btn_calc,
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text("Болжалған Тәуліктік Өндіріс:", size=12, color=c["text_secondary"]),
                        txt_total,
                        ft.Divider(height=1, color=c["card_border"]),
                        ft.Row([ft.Text("☀️ Күн қуаты:"), txt_solar], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bar_solar,
                        ft.Row([ft.Text("💨 Жел қуаты:"), txt_wind], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bar_wind,
                        ft.Container(height=4),
                        txt_rec,
                    ],
                    spacing=6,
                ),
                padding=14,
                border_radius=14,
                bgcolor=c["surface_variant"],
                border=ft.Border.all(1, c["primary"]),
            ),
        ],
        spacing=12,
        padding=12,
    )
