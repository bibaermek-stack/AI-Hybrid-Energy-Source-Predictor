import asyncio
import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]


def build_optimization_view(page: ft.Page) -> ft.Control:
    """Build microgrid optimization & battery dispatch solver view."""
    c = state.colors

    # Inputs
    tf_load = ft.TextField(label=state.text("opt_load"), value=str(state.load_kw), keyboard_type=ft.KeyboardType.NUMBER)
    tf_battery = ft.TextField(label=state.text("opt_battery_cap"), value=str(state.battery_kw), keyboard_type=ft.KeyboardType.NUMBER)
    tf_solar_cost = ft.TextField(label=state.text("opt_solar_cost"), value=str(state.solar_cost), keyboard_type=ft.KeyboardType.NUMBER)
    tf_wind_cost = ft.TextField(label=state.text("opt_wind_cost"), value=str(state.wind_cost), keyboard_type=ft.KeyboardType.NUMBER)

    dd_strategy = ft.Dropdown(
        label=state.text("opt_strategy"),
        value=state.strategy,
        options=[
            ft.dropdown.Option("hybrid", "Hybrid Smart Dispatch (Оңтайлы гибрид)"),
            ft.dropdown.Option("min_cost", "Minimize Operational Cost (Минималды шығын)"),
            ft.dropdown.Option("max_power", "Maximize Renewable Output (Максималды ЖЭК)"),
            ft.dropdown.Option("balanced", "Balanced Battery/Grid (Балансталған)"),
        ],
    )

    # Output text controls
    txt_rec_source = ft.Text("⚡ Оңтайлы көз: Гибридті ЖЭК Микрожелісі", size=15, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_solar_kw = ft.Text("420.5 kW", size=14, color=c["accent"])
    txt_wind_kw = ft.Text("400.1 kW", size=14, color=c["secondary"])
    txt_bat_kw = ft.Text("50.0 kW", size=14, color=c["success"])
    txt_grid_kw = ft.Text("0.0 kW", size=14, color=c["error"])
    progress_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2, color="#FFFFFF")

    async def on_optimize(e=None):
        progress_ring.visible = True
        page.update()

        try:
            state.load_kw = float(tf_load.value or 0.0)
            state.battery_kw = float(tf_battery.value or 0.0)
            state.solar_cost = float(tf_solar_cost.value or 0.08)
            state.wind_cost = float(tf_wind_cost.value or 0.06)
            state.strategy = dd_strategy.value or "hybrid"
        except ValueError:
            pass

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

        opt_src = res.get('recommended_source', 'Hybrid Renewable')
        txt_rec_source.value = f"⚡ Оңтайлы көз: {opt_src}"
        dispatch = res.get("optimal_dispatch") or {}
        txt_solar_kw.value = f"{dispatch.get('solar_kw', res.get('solar_power', 420.5)):.1f} kW"
        txt_wind_kw.value = f"{dispatch.get('wind_kw', res.get('wind_power', 400.1)):.1f} kW"
        txt_bat_kw.value = f"{dispatch.get('battery_kw', min(state.battery_kw, 50.0)):.1f} kW"
        txt_grid_kw.value = f"{dispatch.get('grid_kw', 0.0):.1f} kW"
        progress_ring.visible = False
        page.update()

    # Trigger initial optimization on view load safely
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(on_optimize(None))
    except RuntimeError:
        pass

    btn_opt = ft.ElevatedButton(
        content=ft.Text(state.text("opt_btn")),
        icon=ft.Icons.TUNE,
        style=ft.ButtonStyle(
            bgcolor=c["primary"],
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        on_click=on_optimize,
    )

    card_results = ft.Container(
        content=ft.Column(
            [
                txt_rec_source,
                ft.Divider(height=1, color=c["card_border"]),
                ft.Text("Optimal Dispatch Breakdown:", size=12, weight=ft.FontWeight.W_600, color=c["text_secondary"]),
                ft.Row([ft.Text("☀️ Solar Supply:"), txt_solar_kw], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("💨 Wind Supply:"), txt_wind_kw], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("🔋 Battery Discharge:"), txt_bat_kw], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([ft.Text("⚡ Grid Import/Export:"), txt_grid_kw], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    return ft.ListView(
        controls=[
            ft.Text("⚙ " + state.text("opt_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            tf_load,
            tf_battery,
            ft.Row([ft.Container(tf_solar_cost, expand=True), ft.Container(tf_wind_cost, expand=True)], spacing=10),
            dd_strategy,
            btn_opt,
            card_results,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
    )
