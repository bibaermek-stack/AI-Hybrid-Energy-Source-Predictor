"""
Microgrid dispatch view for EcoPredict AI Mobile.

Shows the dispatch POST /predict computes (src/optimization/hybrid_optimizer):
how much of the available solar and wind is used, battery discharge, the
shortfall left for the grid and the curtailed surplus. It used to read an
`optimal_dispatch` block the API never sends, so "Solar Supply" displayed the
available generation and battery/grid fell back to invented 50 kW / 0 kW.
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


def build_optimization_view(page: ft.Page) -> ft.Control:
    """Build microgrid optimization & battery dispatch solver view."""
    c = state.colors
    t = state.text

    # Inputs
    tf_load = ft.TextField(label=t("opt_load"), value=str(state.load_kw), keyboard_type=ft.KeyboardType.NUMBER)
    tf_battery = ft.TextField(label=t("opt_battery_cap"), value=str(state.battery_kw), keyboard_type=ft.KeyboardType.NUMBER)
    tf_solar_cost = ft.TextField(label=t("opt_solar_cost"), value=str(state.solar_cost), keyboard_type=ft.KeyboardType.NUMBER)
    tf_wind_cost = ft.TextField(label=t("opt_wind_cost"), value=str(state.wind_cost), keyboard_type=ft.KeyboardType.NUMBER)

    dd_strategy = ft.Dropdown(
        label=t("opt_strategy"),
        value=state.strategy,
        options=[
            ft.dropdown.Option("hybrid", t("opt_strategy_hybrid")),
            ft.dropdown.Option("min_cost", t("opt_strategy_min_cost")),
            ft.dropdown.Option("max_power", t("opt_strategy_max_power")),
            ft.dropdown.Option("balanced", t("opt_strategy_balanced")),
        ],
    )

    txt_status = ft.Text("", size=12, color=c["error"], visible=False, selectable=True)
    txt_rec_source = ft.Text(t("opt_recommended", source="—"), size=15, weight=ft.FontWeight.BOLD, color=c["primary"])
    txt_scenario = ft.Text("", size=11, color=c["text_secondary"])
    progress_ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    def value_row(label: str, color: str) -> tuple:
        value = ft.Text("—", size=14, weight=ft.FontWeight.W_600, color=color)
        return ft.Row([ft.Text(label, size=13), value], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), value

    row_solar, txt_solar = value_row(t("opt_row_solar"), c["accent"])
    row_wind, txt_wind = value_row(t("opt_row_wind"), c["secondary"])
    row_batt, txt_batt = value_row(t("opt_row_battery"), c["success"])
    row_short, txt_short = value_row(t("opt_row_shortfall"), c["error"])
    row_curt, txt_curt = value_row(t("opt_row_curtailment"), c["text_secondary"])
    row_rel, txt_rel = value_row(t("opt_row_reliability"), c["primary"])
    row_cost, txt_cost = value_row(t("opt_row_cost"), c["text_secondary"])

    def _num(x) -> float:
        try:
            return float(x)
        except (TypeError, ValueError):
            return 0.0

    def _read_inputs() -> str:
        """Copy the fields into state; returns an error message or ''."""
        try:
            state.load_kw = float(tf_load.value or 0.0)
            state.battery_kw = float(tf_battery.value or 0.0)
            state.solar_cost = float(tf_solar_cost.value or 0.08)
            state.wind_cost = float(tf_wind_cost.value or 0.06)
        except ValueError:
            return t("opt_err_numbers")
        state.strategy = dd_strategy.value or "hybrid"
        return ""

    async def on_optimize(e=None):
        error = _read_inputs()
        if error:
            txt_status.value, txt_status.visible = error, True
            page.update()
            return

        progress_ring.visible = True
        txt_status.visible = False
        page.update()

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
        progress_ring.visible = False

        if res is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            txt_status.value = t("opt_err_failed", reason=reason)
            txt_status.visible = True
            txt_rec_source.value = t("opt_recommended", source="—")
            for t in (txt_solar, txt_wind, txt_batt, txt_short, txt_curt, txt_rel, txt_cost):
                t.value = "—"
            page.update()
            return

        txt_rec_source.value = t("opt_recommended", source=res.get("recommended_source", "—"))
        txt_scenario.value = t(
            "opt_scenario", irr=state.irradiation, wind=state.wind_speed, load=state.load_kw
        )
        txt_solar.value = f"{_num(res.get('solar_used')):.1f} / {_num(res.get('solar_power')):.1f} kW"
        txt_wind.value = f"{_num(res.get('wind_used')):.1f} / {_num(res.get('wind_power')):.1f} kW"
        txt_batt.value = f"{_num(res.get('battery_used')):.1f} kW"
        txt_short.value = f"{_num(res.get('shortfall_kw')):.1f} kW"
        txt_curt.value = f"{_num(res.get('curtailment_kw')):.1f} kW"
        txt_rel.value = f"{_num(res.get('reliability_index')) * 100:.0f} %"
        cost = res.get("estimated_cost")
        txt_cost.value = f"{_num(cost):.2f}" if cost is not None else "—"
        page.update()

    btn_opt = ft.Button(
        content=ft.Row([ft.Text(t("opt_btn")), progress_ring], tight=True, spacing=8),
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
                txt_scenario,
                ft.Divider(height=1, color=c["card_border"]),
                row_solar,
                row_wind,
                row_batt,
                row_short,
                row_curt,
                ft.Divider(height=1, color=c["card_border"]),
                row_rel,
                row_cost,
            ],
            spacing=8,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    view = ft.ListView(
        controls=[
            ft.Text("⚙ " + t("opt_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            tf_load,
            tf_battery,
            ft.Row([ft.Container(tf_solar_cost, expand=True), ft.Container(tf_wind_cost, expand=True)], spacing=10),
            dd_strategy,
            btn_opt,
            txt_status,
            card_results,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
        expand=True,
    )
    # Computed when the tab is opened (on_nav_change in main.py), not while
    # main() is still building every view — that raced the splash transition.
    view.data = on_optimize
    return view
