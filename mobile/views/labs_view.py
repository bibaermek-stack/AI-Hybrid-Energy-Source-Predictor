import flet as ft
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]


def build_labs_view(page: ft.Page) -> ft.Control:
    """Build experimental microgrid simulation lab view."""
    c = state.colors

    # Labels
    txt_solar_cap = ft.Text("1000 kW", size=11, weight=ft.FontWeight.BOLD, color=c["accent"])
    txt_wind_cap = ft.Text("800 kW", size=11, weight=ft.FontWeight.BOLD, color=c["secondary"])
    txt_bess_cap = ft.Text("500 kWh", size=11, weight=ft.FontWeight.BOLD, color=c["success"])

    # Sim Result Text
    txt_sim_power = ft.Text("1,820.0 kW", size=22, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_sim_efficiency = ft.Text("96.5%", size=18, weight=ft.FontWeight.BOLD, color=c["success"])

    def on_sim_change(e):
        s = float(sl_solar_cap.value or 1000.0)
        w = float(sl_wind_cap.value or 800.0)
        b = float(sl_bess_cap.value or 500.0)
        txt_solar_cap.value = f"{s:.0f} kW"
        txt_wind_cap.value = f"{w:.0f} kW"
        txt_bess_cap.value = f"{b:.0f} kWh"

        tot = (s * 0.85) + (w * 0.70)
        eff = 92.0 + (b / 1000.0) * 6.0
        txt_sim_power.value = f"{tot:.1f} kW"
        txt_sim_efficiency.value = f"{min(99.9, eff):.1f}%"
        page.update()

    sl_solar_cap = ft.Slider(min=100, max=5000, value=1000, divisions=49, label="{value} kW", on_change=on_sim_change)
    sl_wind_cap = ft.Slider(min=100, max=5000, value=800, divisions=49, label="{value} kW", on_change=on_sim_change)
    sl_bess_cap = ft.Slider(min=100, max=2000, value=500, divisions=19, label="{value} kWh", on_change=on_sim_change)

    return ft.ListView(
        controls=[
            ft.Text("🧪 AI Модельдеу Лабораториясы", size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(ft.Icons.SCIENCE, color=c["primary"]), ft.Text("Микрожелі Параметрлерін Сынау", weight=ft.FontWeight.BOLD)]),
                        ft.Row([ft.Text("☀️ Күн сыйымдылығы:"), txt_solar_cap], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_solar_cap,
                        ft.Row([ft.Text("💨 Жел сыйымдылығы:"), txt_wind_cap], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_wind_cap,
                        ft.Row([ft.Text("🔋 Батарея сыйымдылығы:"), txt_bess_cap], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        sl_bess_cap,
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
                        ft.Text("Симуляцияланған Модельдеу Нәтижесі:", size=12, color=c["text_secondary"]),
                        txt_sim_power,
                        ft.Row([ft.Text("Микрожелі ПӘК-і (Efficiency):"), txt_sim_efficiency], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
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
