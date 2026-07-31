"""
Solarman Live Telemetry for EcoPredict AI Mobile.

Mirrors the data-backed parts of the Streamlit Solarman page: live inverter
readings, device and firmware details, per-string DC and per-phase AC values,
Performance Ratio, KZT economics and the offline/fault check — each from its
own endpoint.

The dashboard's five analytics tabs (heatmap, MPPT curves, radar, savings area,
histogram) are deliberately not ported: _get_cached_solar_heatmap() and
_get_cached_mppt_telemetry() build their series with np.sin and hardcoded
arrays, so they would be decoration presented as measurement.
"""

import flet as ft
try:
    from mobile.state import state
    from mobile.api_client import api_client
    from mobile import api_client as api_client_module
    from mobile.components.metric_card import build_metric_card
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]
    from components.metric_card import build_metric_card  # type: ignore # pyright: ignore[reportMissingImports]

INVERTERS = ["2501221272", "2411046235"]


def build_live_view(page: ft.Page) -> ft.Control:
    c = state.colors
    selected_sn = INVERTERS[0]
    latest: dict = {}

    def card(title: str) -> tuple:
        """Section shell plus the column callers fill in."""
        body = ft.Column([], spacing=6)
        return (
            ft.Container(
                content=ft.Column(
                    [ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]), body],
                    spacing=8,
                ),
                padding=14,
                border_radius=16,
                bgcolor=c["surface_variant"],
                border=ft.Border.all(1, c["card_border"]),
            ),
            body,
        )

    def kv_rows(pairs) -> list:
        return [
            ft.Row(
                [
                    ft.Text(str(k), size=12, color=c["text_secondary"]),
                    ft.Text(str(v), size=12, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
            for k, v in pairs
        ]

    # ---- status ----------------------------------------------------------
    txt_status = ft.Text("Жүктелуде…", size=14, weight=ft.FontWeight.BOLD, color=c["text_secondary"])
    txt_source = ft.Text("", size=11, color=c["text_secondary"])
    progress = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)

    # ---- KPI cards -------------------------------------------------------
    r_ac, r_ac_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    r_dc, r_dc_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    r_eff, r_eff_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    r_temp, r_temp_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    r_today, r_today_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()
    r_total, r_total_s = ft.Ref[ft.Text](), ft.Ref[ft.Text]()

    def kpi(title, unit, icon, accent, vref, sref):
        return build_metric_card(title=title, value="—", unit=unit, icon=icon,
                                 accent_color=accent, subtitle="…", value_ref=vref, subtitle_ref=sref)

    kpi_grid = ft.Column(
        [
            ft.Row([
                ft.Container(kpi("AC қуаты", "kW", ft.Icons.BOLT, "#F59E0B", r_ac, r_ac_s), expand=True),
                ft.Container(kpi("DC қуаты", "kW", ft.Icons.SOLAR_POWER, "#3B82F6", r_dc, r_dc_s), expand=True),
            ], spacing=10),
            ft.Row([
                ft.Container(kpi("ПӘК (AC/DC)", "%", ft.Icons.SPEED, "#10B981", r_eff, r_eff_s), expand=True),
                ft.Container(kpi("Температура", "°C", ft.Icons.THERMOSTAT, "#EC4899", r_temp, r_temp_s), expand=True),
            ], spacing=10),
            ft.Row([
                ft.Container(kpi("Бүгінгі", "kWh", ft.Icons.TODAY, "#14B8A6", r_today, r_today_s), expand=True),
                ft.Container(kpi("Жалпы", "kWh", ft.Icons.HISTORY, "#8B5CF6", r_total, r_total_s), expand=True),
            ], spacing=10),
        ],
        spacing=10,
    )

    card_basic, body_basic = card("📋 Негізгі ақпарат")
    card_version, body_version = card("🔧 Нұсқа ақпараты")
    card_dc, body_dc = card("⚡ DC стрингтер (MPPT)")
    card_ac, body_ac = card("🔌 AC фазалар")
    card_weather, body_weather = card("🌤 Ауа райы (Түркістан)")
    card_alert, body_alert = card("🔔 Күй тексерісі")

    # ---- Performance Ratio ----------------------------------------------
    txt_irr_val = ft.Text("800 W/m²", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])
    sl_irr = ft.Slider(min=1, max=1200, value=800, divisions=24)
    card_pr, body_pr = card("📐 Өнімділік коэффициенті (PR)")
    # Results live in their own column; writing them into body_pr would wipe
    # out the slider above and leave the inputs unusable after the first load.
    body_pr_result = ft.Column([], spacing=6)

    # ---- ROI -------------------------------------------------------------
    txt_capex_val = ft.Text("15 000 000 ₸", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])
    sl_capex = ft.Slider(min=1_000_000, max=60_000_000, value=15_000_000, divisions=59)
    txt_tariff_val = ft.Text("28 ₸/kWh", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])
    sl_tariff = ft.Slider(min=5, max=120, value=28, divisions=23)
    card_roi, body_roi = card("💰 Экономика (ROI, ₸)")
    body_roi_result = ft.Column([], spacing=6)

    def _num(x, default=0.0) -> float:
        try:
            return float(x)
        except (TypeError, ValueError):
            return default

    async def compute_pr() -> None:
        gen = latest.get("generation") or {}
        basic = latest.get("basic") or {}
        if not gen:
            return
        res = await api_client.solarman_process(
            active_power_kw=_num(gen.get("ac_active_power_kw")),
            e_today_kwh=_num(gen.get("e_today_kwh")),
            e_total_kwh=_num(gen.get("e_total_kwh")),
            module_temp_c=_num(gen.get("temperature_c"), 25.0),
            fault_code=0,
            status=int(_num(basic.get("status"), 1)),
            device_sn=str(basic.get("sn") or selected_sn),
            dc_capacity_kwp=_num(basic.get("rated_power_kw"), 25.0),
            irradiance_w_m2=float(sl_irr.value or 800),
            ambient_temp_c=_num((latest.get("weather") or {}).get("temperature_2m_c"), 25.0),
        )
        if not res:
            body_pr_result.controls = kv_rows([("Күй", "есептелмеді")])
        else:
            body_pr_result.controls = kv_rows([
                ("Ағымдағы қуат", f"{_num(res.get('active_power_kw')):.3f} kW"),
                ("Күтілетін қуат", f"{_num(res.get('expected_power_kw')):.2f} kW"),
                ("Ұяшық температурасы", f"{_num(res.get('cell_temp_c')):.1f} °C"),
                ("PR (шикі)", f"{_num(res.get('raw_pr')) * 100:.1f} %"),
                ("PR (түзетілген)", f"{_num(res.get('corrected_pr')) * 100:.1f} %"),
            ])
        page.update()

    async def compute_roi() -> None:
        gen = latest.get("generation") or {}
        res = await api_client.solarman_roi(
            total_generation_kwh=_num(gen.get("e_total_kwh"), 45000.0),
            initial_investment_kzt=float(sl_capex.value or 15_000_000),
            tariff_kzt_per_kwh=float(sl_tariff.value or 28),
        )
        if not res:
            body_roi_result.controls = kv_rows([("Күй", "есептелмеді")])
        else:
            body_roi_result.controls = kv_rows([
                ("Инвестиция", f"{_num(res.get('initial_investment_kzt')):,.0f} ₸".replace(",", " ")),
                ("Жиынтық үнем", f"{_num(res.get('cumulative_savings_kzt')):,.0f} ₸".replace(",", " ")),
                ("Таза пайда", f"{_num(res.get('net_profit_kzt')):,.0f} ₸".replace(",", " ")),
                ("ROI", f"{_num(res.get('roi_pct')):.1f} %"),
                ("Өзін-өзі өтеу", f"{_num(res.get('payback_period_years')):.1f} жыл"),
            ])
        page.update()

    async def load(e=None) -> None:
        progress.visible = True
        txt_status.value = "Жүктелуде…"
        page.update()

        data = await api_client.get_solarman_live(selected_sn)
        gen = (data or {}).get("generation") or {}
        basic = (data or {}).get("basic") or {}
        version = (data or {}).get("version") or {}

        if not gen:
            reason = getattr(api_client_module, "last_http_error", "") or "жауап бос"
            txt_status.value = "⚠️ Телеметрия қолжетімсіз"
            txt_status.color = c["error"]
            txt_source.value = reason
            for body in (body_basic, body_version, body_dc, body_ac, body_pr_result, body_roi_result, body_alert):
                body.controls = []
            progress.visible = False
            page.update()
            return

        latest.clear()
        latest.update(data)

        online = basic.get("status") == 1
        txt_status.value = "🟢 Қалыпты жұмыс" if online else "🔴 Байланыс жоқ"
        txt_status.color = c["success"] if online else c["error"]
        txt_source.value = f"дереккөз: {data.get('source', '—')} · {str(data.get('fetched_at', ''))[:19]}"

        ac_kw = _num(gen.get("ac_active_power_kw"))
        dc_kw = _num(gen.get("dc_total_kw"))
        rated = _num(basic.get("rated_power_kw"), 25.0)
        # Near zero output the AC/DC ratio is just sensor noise — it read 120%
        # at night, which is not a thing an inverter can do. Only report it
        # once the array is producing something measurable.
        eff_known = dc_kw >= max(0.2, rated * 0.01)
        eff = (ac_kw / dc_kw * 100) if eff_known else 0.0

        def setv(ref, sref, value, sub):
            if ref.current is not None:
                ref.current.value = value
            if sref.current is not None:
                sref.current.value = sub

        setv(r_ac, r_ac_s, f"{ac_kw:.2f}", f"номинал {rated:.0f} kW")
        setv(r_dc, r_dc_s, f"{dc_kw:.2f}", f"{len(gen.get('dc') or [])} стринг")
        setv(r_eff, r_eff_s, f"{eff:.1f}" if eff_known else "—",
             "AC / DC" if eff_known else "қуат тым төмен")
        setv(r_temp, r_temp_s, f"{_num(gen.get('temperature_c')):.1f}", "инвертор")
        setv(r_today, r_today_s, f"{_num(gen.get('e_today_kwh')):.1f}", "бүгінгі өндіріс")
        setv(r_total, r_total_s, f"{_num(gen.get('e_total_kwh')):.0f}", "жұмыс ғұмырында")

        body_basic.controls = kv_rows([
            ("Сериялық нөмір", basic.get("sn", "—")),
            ("Құрылғы ID", basic.get("device_id", "—")),
            ("Түрі", basic.get("inverter_type", "—")),
            ("Номинал қуат", f"{rated:.1f} kW"),
            ("MPPT саны", basic.get("mppt_no", "—")),
            ("Күй", "Онлайн" if online else "Офлайн"),
        ])

        body_version.controls = kv_rows([
            ("Протокол", version.get("protocol_version", "—")),
            ("Негізгі", version.get("main", "—")),
            ("HMI", version.get("hmi", "—")),
            ("Басқару SW", version.get("control_sw_v1", "—")),
            ("Басқару SW v2", version.get("control_sw_v2", "—")),
            ("Comm CPU", version.get("comm_cpu_sw", "—")),
        ])

        body_dc.controls = kv_rows([
            (
                s.get("mppt", f"PV{i + 1}"),
                f"{_num(s.get('voltage_v')):.1f} V · {_num(s.get('current_a')):.1f} A · {_num(s.get('power_kw')):.2f} kW",
            )
            for i, s in enumerate(gen.get("dc") or [])
        ]) or kv_rows([("Стрингтер", "деректер жоқ")])

        body_ac.controls = kv_rows([
            (
                f"Фаза {p.get('phase', '?')}",
                f"{_num(p.get('voltage_v')):.1f} V · {_num(p.get('current_a')):.1f} A"
                + (f" · {_num(p.get('frequency_hz')):.2f} Hz" if p.get("frequency_hz") is not None else "")
                + f" · {_num(p.get('power_kw')):.2f} kW",
            )
            for p in (gen.get("ac") or [])
        ]) or kv_rows([("Фазалар", "деректер жоқ")])

        weather = await api_client.get_weather()
        if weather:
            latest["weather"] = weather
            body_weather.controls = kv_rows([
                ("Орналасқан жері", weather.get("location", "—")),
                ("Температура", f"{_num(weather.get('temperature_2m_c')):.1f} °C"),
                ("Бұлттылық", f"{_num(weather.get('cloud_cover_pct')):.0f} %"),
                ("UV индексі", f"{_num(weather.get('uv_index')):.1f}"),
                ("Дереккөз", weather.get("source", "—")),
            ])
        else:
            body_weather.controls = kv_rows([("Ауа райы", "қолжетімсіз")])

        alert = await api_client.solarman_alert({
            "deviceSn": str(basic.get("sn") or selected_sn),
            "deviceId": basic.get("device_id"),
            "faultCode": 0,
            "deviceStatus": basic.get("status", 1),
        })
        if alert:
            msg = alert.get("alert_message") or "Ескерту жоқ"
            body_alert.controls = kv_rows([
                ("Офлайн", "иә" if alert.get("is_offline") else "жоқ"),
                ("Ақау", "иә" if alert.get("is_faulty") else "жоқ"),
                ("Хабарлама жіберілді", "иә" if alert.get("alert_sent") else "жоқ"),
            ]) + [ft.Text(msg[:160], size=11, color=c["text_secondary"])]
        else:
            body_alert.controls = kv_rows([("Тексеріс", "орындалмады")])

        await compute_pr()
        await compute_roi()

        progress.visible = False
        page.update()

    # ---- interactions ----------------------------------------------------
    async def on_inverter_change(e):
        nonlocal selected_sn
        selected_sn = dd_inverters.value or INVERTERS[0]
        await load()

    dd_inverters = ft.Dropdown(
        label="Инвертор",
        value=selected_sn,
        options=[ft.DropdownOption(key=sn, text=f"SN {sn}") for sn in INVERTERS],
        # flet 0.86 renamed the Dropdown callback: on_change no longer exists.
        on_select=on_inverter_change,
        dense=True,
    )

    async def on_irr_change(e):
        txt_irr_val.value = f"{float(sl_irr.value):.0f} W/m²"
        page.update()
        await compute_pr()

    async def on_money_change(e):
        txt_capex_val.value = f"{float(sl_capex.value):,.0f} ₸".replace(",", " ")
        txt_tariff_val.value = f"{float(sl_tariff.value):.0f} ₸/kWh"
        page.update()
        await compute_roi()

    sl_irr.on_change = on_irr_change
    sl_capex.on_change = on_money_change
    sl_tariff.on_change = on_money_change

    btn_refresh = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.REFRESH, size=16), ft.Text("Жаңарту")],
                       alignment=ft.MainAxisAlignment.CENTER),
        on_click=load,
        style=ft.ButtonStyle(bgcolor=c["primary"], color="#FFFFFF",
                             shape=ft.RoundedRectangleBorder(radius=12)),
    )

    body_pr.controls = [
        ft.Row([ft.Text("Күн радиациясы:", size=12, color=c["text_secondary"]), txt_irr_val],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        sl_irr,
        body_pr_result,
    ]
    body_roi.controls = [
        ft.Row([ft.Text("Инвестиция (CAPEX):", size=12, color=c["text_secondary"]), txt_capex_val],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        sl_capex,
        ft.Row([ft.Text("Тариф:", size=12, color=c["text_secondary"]), txt_tariff_val],
               alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        sl_tariff,
        body_roi_result,
    ]

    view = ft.ListView(
        controls=[
            ft.Text("📡 " + state.text("live_title"), size=18, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Row([dd_inverters, progress], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Row([txt_status], alignment=ft.MainAxisAlignment.START),
            txt_source,
            btn_refresh,
            ft.Container(height=6),
            kpi_grid,
            ft.Container(height=6),
            card_basic,
            card_version,
            card_dc,
            card_ac,
            card_weather,
            card_pr,
            card_roi,
            card_alert,
            ft.Container(height=20),
        ],
        spacing=10,
        padding=12,
        expand=True,
    )
    # Re-fetched whenever the tab is opened (see on_nav_change in main.py).
    view.data = load
    return view
