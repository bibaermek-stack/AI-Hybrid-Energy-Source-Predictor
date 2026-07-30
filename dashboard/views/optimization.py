"""Streamlit UI: multi-hour hybrid optimization (PuLP) — design system."""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from dashboard.components.buttons import primary_button
from dashboard.components.metric_card import metric_row
from dashboard.components.prediction_card import prediction_card
from dashboard.components.states import empty_state, error_state, loading_state
from dashboard.components.ui_kit import section_header
from dashboard.utils.plotly_theme import themed_line
from src.optimization import BatteryParams, HybridEnergyOptimizer, describe_mode


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    try:
        _render(lang)
    except Exception as e:
        error_state(
            _t(lang, "Optimization view failed.", "Оңтайландыру беті сәтсіз."),
            detail=e,
            lang=lang,
        )


def _render(lang: str) -> None:
    lang = "kk" if lang == "kk" else "en"
    theme = str(st.session_state.get("ep_theme") or "Dark")

    section_header(
        _t(lang, "Hybrid dispatch optimizer", "Гибридті диспетчер"),
        _t(
            lang,
            "24–48 h solar + wind + battery + grid linear program (PuLP)",
            "24–48 сағ күн + жел + батарея + grid LP (PuLP)",
        ),
    )

    default_mode = st.session_state.get("ep_opt_mode") or "balanced"
    mode_options = ["balanced", "max_profit", "min_co2"]
    try:
        mode_index = mode_options.index(default_mode)
    except ValueError:
        mode_index = 0

    c1, c2, c3 = st.columns(3)
    with c1:
        hours = st.slider(_t(lang, "Horizon (h)", "Горизонт (сағ)"), 12, 48, 24, 1)
        mode = st.selectbox(
            _t(lang, "Objective mode", "Мақсат режимі"),
            mode_options,
            index=mode_index,
            format_func=lambda m: describe_mode(m, lang),
        )
    with c2:
        cap = st.number_input(_t(lang, "Battery kWh", "Батарея кВт·сағ"), 10.0, 500.0, 100.0, 10.0)
        p_ch = st.number_input(_t(lang, "Max charge kW", "Макс заряд кВт"), 5.0, 200.0, 40.0, 5.0)
        p_dis = st.number_input(_t(lang, "Max discharge kW", "Макс разряд кВт"), 5.0, 200.0, 40.0, 5.0)
    with c3:
        price_imp = st.number_input(_t(lang, "Import $/kWh", "Импорт $/кВт·сағ"), 0.01, 1.0, 0.12, 0.01)
        price_exp = st.number_input(_t(lang, "Export $/kWh", "Экспорт $/кВт·сағ"), 0.0, 1.0, 0.06, 0.01)
        co2 = st.number_input(_t(lang, "Grid kgCO₂/kWh", "Grid кгCO₂/кВт·сағ"), 0.1, 1.5, 0.45, 0.05)

    section_header(
        _t(lang, "Profiles (synthetic demo)", "Профильдер (синтетикалық демо)"),
        None,
    )
    t = np.arange(int(hours))
    solar = np.maximum(0, 80 * np.sin(np.pi * (t - 6) / 12)) * (t >= 6) * (t <= 18)
    wind = 25 + 15 * np.sin(2 * np.pi * t / 24 + 1.2)
    load = 40 + 20 * (t >= 18) * (t <= 22) + 10 * np.sin(2 * np.pi * t / 24)

    if st.checkbox(_t(lang, "Edit load profile", "Жүктеме профилін өзгерту"), False):
        peak = st.slider(_t(lang, "Evening peak kW", "Кешкі шың кВт"), 40.0, 150.0, 70.0, 5.0)
        load = 35 + (peak - 35) * ((t >= 17) & (t <= 22)).astype(float)

    df_in = pd.DataFrame({"hour": t, "solar_kw": solar, "wind_kw": wind, "load_kw": load})
    st.dataframe(df_in.round(2), width="stretch", hide_index=True)

    if not primary_button(
        _t(lang, "Run optimizer", "Оңтайландырғышты іске қосу"),
        key="opt_run_btn",
    ):
        empty_state(
            _t(lang, "No schedule yet", "Жоспар жоқ"),
            _t(
                lang,
                "Configure parameters and run the optimizer.",
                "Параметрлерді баптап, оңтайландырғышты іске қосыңыз.",
            ),
            icon="⚙",
        )
        return

    with loading_state(_t(lang, "Solving LP…", "LP шешілуде…")):
        bat = BatteryParams(
            capacity_kwh=float(cap),
            max_charge_kw=float(p_ch),
            max_discharge_kw=float(p_dis),
        )
        opt = HybridEnergyOptimizer(
            battery=bat,
            co2_grid_kg_per_kwh=float(co2),
            price_import=float(price_imp),
            price_export=float(price_exp),
        )
        try:
            result = opt.optimize(
                solar_forecast=solar,
                wind_forecast=wind,
                load=load,
                mode=mode,
            )
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    data = result if isinstance(result, dict) else {}
    st.success(_t(lang, "Optimization complete", "Оңтайландыру аяқталды"))

    metric_row(
        [
            {
                "label": "Status",
                "value": str(data.get("status", "ok")),
                "icon": "●",
                "variant": "success",
            },
            {
                "label": _t(lang, "Profit $", "Пайда $"),
                "value": f"{float(data.get('total_profit', 0)):.2f}",
                "icon": "$",
                "variant": "default",
            },
            {
                "label": "CO₂ kg",
                "value": f"{float(data.get('total_co2_kg', 0)):.2f}",
                "icon": "◈",
                "variant": "warn",
            },
            {
                "label": _t(lang, "Self-cons %", "Өз тұтыну %"),
                "value": f"{float(data.get('self_consumption_rate', 0)):.1f}",
                "icon": "%",
                "variant": "total",
            },
        ]
    )

    prediction_card(
        title=_t(lang, "Dispatch summary", "Диспетчер қорытындысы"),
        recommendation=str(data.get("mode", mode)),
        extra_rows=[
            ("Grid import kWh", f"{float(data.get('grid_import_kwh', 0)):.1f}"),
            ("Grid export kWh", f"{float(data.get('grid_export_kwh', 0)):.1f}"),
            ("Renewable used kWh", f"{float(data.get('renewable_used_kwh', 0)):.1f}"),
        ],
    )

    try:
        fig = opt.plot_results(result)
        from dashboard.utils.plotly_theme import apply_theme

        apply_theme(fig, theme)
        st.plotly_chart(fig, width="stretch")
    except Exception as plot_err:
        st.warning(str(plot_err))
        schedule = data.get("schedule")
        if isinstance(schedule, pd.DataFrame) and not schedule.empty:
            st.dataframe(schedule.round(3), width="stretch")
            cols = [
                c
                for c in (
                    "load",
                    "solar_avail",
                    "wind_avail",
                    "grid_import",
                    "grid_export",
                    "charge",
                    "discharge",
                )
                if c in schedule.columns
            ]
            if cols:
                x = list(range(len(schedule)))
                st.plotly_chart(
                    themed_line(
                        x,
                        {c: schedule[c].tolist() for c in cols},
                        title="Dispatch",
                        y_title="kW",
                        theme=theme,
                    ),
                    width="stretch",
                )
