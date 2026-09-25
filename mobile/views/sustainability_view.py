"""
Sustainability view for EcoPredict AI Mobile.

CO₂ avoided and its equivalents from POST /sustainability/impact, which runs
src.sustainability.analyze_impact — the same calculator as the dashboard's
Sustainability page. The screen used to print 412.8 t CO₂, 18 650 trees,
245 t of coal and an 88.4 % green share, none of it computed from anything.

The renewable energy figure can be typed in or taken from the inverter's
lifetime yield (/solarman/live); a demo reply is labelled as such.
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


def build_sustainability_view(page: ft.Page) -> ft.Control:
    """CO₂ impact calculator backed by the sustainability endpoint."""
    c = state.colors
    t = state.text

    # Same starting values as the dashboard's Sustainability page.
    tf_renewable = ft.TextField(label=t("su_renewable"), value="120000", keyboard_type=ft.KeyboardType.NUMBER)
    tf_grid = ft.TextField(label=t("su_grid_import"), value="20000", keyboard_type=ft.KeyboardType.NUMBER)
    tf_factor = ft.TextField(label=t("su_grid_factor"), value="0.45", keyboard_type=ft.KeyboardType.NUMBER)
    txt_input_source = ft.Text("", size=11, color=c["text_secondary"])
    txt_status = ft.Text("", size=12, color=c["error"], visible=False, selectable=True)
    progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    def stat_card(icon, title: str, color: str) -> tuple:
        value = ft.Text("—", size=18, weight=ft.FontWeight.BOLD, color=color)
        card = ft.Container(
            content=ft.Column(
                [ft.Icon(icon, color=color, size=26), ft.Text(title, size=11, color=c["text_secondary"]), value],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, color),
            expand=True,
        )
        return card, value

    card_co2, val_co2 = stat_card(ft.Icons.CO2, t("su_co2_net"), c["success"])
    card_trees, val_trees = stat_card(ft.Icons.PARK, t("su_trees"), c["accent"])
    card_cars, val_cars = stat_card(ft.Icons.DIRECTIONS_CAR, t("su_cars"), c["warning"])
    card_emitted, val_emitted = stat_card(ft.Icons.FACTORY, t("su_emitted"), c["error"])

    bar_self = ft.ProgressBar(value=0, color=c["success"], bgcolor=ft.Colors.with_opacity(0.1, c["text_secondary"]), height=12)
    txt_self = ft.Text("—", size=13, weight=ft.FontWeight.BOLD, color=c["success"])
    txt_narrative = ft.Text("", size=12, color=c["text_secondary"])

    def _read(tf: ft.TextField) -> float:
        try:
            value = float((tf.value or "").replace(" ", "").replace(",", "."))
        except ValueError:
            raise ValueError(t("su_err_number", field=tf.label))
        if value < 0:
            raise ValueError(t("su_err_negative", field=tf.label))
        return value

    async def calculate(e=None) -> None:
        try:
            renewable = _read(tf_renewable)
            grid = _read(tf_grid)
            factor = _read(tf_factor)
        except ValueError as err:
            txt_status.value, txt_status.visible = str(err), True
            page.update()
            return

        progress.visible = True
        txt_status.visible = False
        page.update()
        res = await api_client.sustainability_impact(renewable, grid, factor)
        progress.visible = False

        if res is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("reason_unknown")
            txt_status.value, txt_status.visible = t("su_err_failed", reason=reason), True
            for v in (val_co2, val_trees, val_cars, val_emitted):
                v.value = "—"
            page.update()
            return

        carbon = res.get("carbon") or {}
        energy = res.get("energy") or {}
        net_t = float(carbon.get("co2_net_benefit_kg") or 0.0) / 1000.0
        val_co2.value = t("su_tonnes", v=f"{net_t:,.1f}".replace(",", " "))
        val_trees.value = t("su_tree_years", v=f"{float(carbon.get('trees_year_equiv') or 0.0):,.0f}".replace(",", " "))
        val_cars.value = t("su_car_years", v=f"{float(carbon.get('cars_year_equiv') or 0.0):,.1f}".replace(",", " "))
        val_emitted.value = t("su_tonnes", v=f"{float(carbon.get('co2_emitted_kg') or 0.0) / 1000.0:,.1f}".replace(",", " "))
        self_pct = float(energy.get("self_sufficiency_pct") or 0.0)
        bar_self.value = max(0.0, min(1.0, self_pct / 100.0))
        txt_self.value = f"{self_pct:.1f} %"
        txt_narrative.value = str(res.get("narrative") or "")
        page.update()

    async def use_inverter_yield(e=None) -> None:
        progress.visible = True
        page.update()
        live = await api_client.get_solarman_live()
        progress.visible = False
        total = ((live or {}).get("generation") or {}).get("e_total_kwh")
        if total is None:
            reason = getattr(api_client_module, "last_http_error", "") or t("su_no_e_total")
            txt_input_source.value = t("su_err_inverter", reason=reason)
            txt_input_source.color = c["error"]
            page.update()
            return
        tf_renewable.value = f"{float(total):.0f}"
        tf_grid.value = "0"
        if api_client.is_demo(live):
            txt_input_source.value = t("su_inverter_demo")
            txt_input_source.color = c["warning"]
        else:
            txt_input_source.value = t("su_inverter_live", at=str(live.get("fetched_at", ""))[:19])
            txt_input_source.color = c["success"]
        await calculate()

    btn_calc = ft.Button(
        content=ft.Row([ft.Text(t("su_btn_calc")), progress], tight=True, spacing=8),
        icon=ft.Icons.CALCULATE,
        style=ft.ButtonStyle(bgcolor=c["primary"], color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=12)),
        on_click=calculate,
    )
    btn_inverter = ft.OutlinedButton(
        content=ft.Text(t("su_btn_inverter")),
        icon=ft.Icons.SOLAR_POWER,
        on_click=use_inverter_yield,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
    )

    inputs = ft.Container(
        content=ft.Column([tf_renewable, tf_grid, tf_factor, txt_input_source, ft.Row([btn_calc, btn_inverter], wrap=True, spacing=8)], spacing=10),
        padding=12,
        border_radius=14,
        bgcolor=c["surface"],
        border=ft.Border.all(1, c["card_border"]),
    )

    self_card = ft.Container(
        content=ft.Column(
            [
                ft.Text(t("su_self_title"), size=13, weight=ft.FontWeight.BOLD),
                bar_self,
                ft.Row([ft.Text(t("su_self_formula"), size=11, color=c["text_secondary"]), txt_self], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                txt_narrative,
            ],
            spacing=6,
        ),
        padding=14,
        border_radius=14,
        bgcolor=c["surface_variant"],
        border=ft.Border.all(1, c["card_border"]),
    )

    view = ft.ListView(
        controls=[
            ft.Text(t("su_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("su_source"), size=11, color=c["text_secondary"]),
            inputs,
            txt_status,
            ft.Row([card_co2, card_trees], spacing=10),
            ft.Row([card_cars, card_emitted], spacing=10),
            self_card,
            ft.Container(height=20),
        ],
        spacing=12,
        padding=12,
        expand=True,
    )
    view.data = calculate
    return view
