"""Streamlit UI: CO₂, LCOE, ROI, impact analyzer."""

from __future__ import annotations

import math

import streamlit as st

from src.sustainability import analyze_impact, co2_avoided_kg, lcoe, payback_years, roi_percent


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def _f(x, default: float = 0.0) -> float:
    try:
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return default
        return v
    except (TypeError, ValueError):
        return default


def _fmt(n: float, digits: int = 0) -> str:
    try:
        if digits <= 0:
            return f"{_f(n):,.0f}"
        return f"{_f(n):,.{digits}f}"
    except Exception:
        return str(n)


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    try:
        _render(lang, texts, models_status)
    except Exception as e:
        st.error(
            ("Қате (Тұрақтылық): " if lang == "kk" else "Error (Sustainability): ") + str(e)
        )
        st.exception(e)


def _render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    lang = "kk" if lang == "kk" else "en"
    st.caption(
        _t(
            lang,
            "Carbon & economic sustainability metrics for renewable systems",
            "ЖЭК жүйелерінің көміртек және экономикалық тұрақтылық метрикалары",
        )
    )

    st.subheader(_t(lang, "Energy & carbon", "Энергия және көміртек"))
    c1, c2, c3 = st.columns(3)
    with c1:
        ren = _f(
            st.number_input(
                _t(lang, "Renewable kWh (period)", "ЖЭК кВт·сағ (кезең)"),
                min_value=0.0,
                max_value=10_000_000.0,
                value=120_000.0,
                step=1000.0,
                key="sust_ren",
            )
        )
    with c2:
        grid_imp = _f(
            st.number_input(
                _t(lang, "Grid import kWh", "Grid импорт кВт·сағ"),
                min_value=0.0,
                max_value=10_000_000.0,
                value=20_000.0,
                step=500.0,
                key="sust_grid",
            )
        )
    with c3:
        factor = _f(
            st.number_input(
                _t(lang, "Grid kgCO₂/kWh", "Grid кгCO₂/кВт·сағ"),
                min_value=0.1,
                max_value=1.5,
                value=0.45,
                step=0.05,
                key="sust_factor",
            ),
            0.45,
        )

    st.subheader(_t(lang, "Economics (treat kWh as annual)", "Экономика (кВт·сағ — жылдық)"))
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        capex = _f(
            st.number_input(
                _t(lang, "CAPEX $", "CAPEX $"),
                min_value=1000.0,
                max_value=50_000_000.0,
                value=250_000.0,
                step=1000.0,
                key="sust_capex",
            ),
            250_000.0,
        )
    with e2:
        price = _f(
            st.number_input(
                _t(lang, "Tariff $/kWh", "Тариф $/кВт·сағ"),
                min_value=0.01,
                max_value=1.0,
                value=0.12,
                step=0.01,
                key="sust_price",
            ),
            0.12,
        )
    with e3:
        opex = _f(
            st.number_input(
                _t(lang, "OPEX $/year", "OPEX $/жыл"),
                min_value=0.0,
                max_value=1_000_000.0,
                value=5_000.0,
                step=100.0,
                key="sust_opex",
            )
        )
    with e4:
        life = int(
            st.number_input(
                _t(lang, "Lifetime years", "Мерзім жыл"),
                min_value=5,
                max_value=40,
                value=25,
                step=1,
                key="sust_life",
            )
        )

    report = analyze_impact(
        renewable_kwh=ren,
        grid_import_kwh=grid_imp,
        grid_factor_kg_per_kwh=factor,
        capex=capex,
        price_per_kwh=price,
        opex_annual=opex,
        lifetime_years=life,
        lang=lang,
    )

    st.info(str(report.get("narrative") or ""))

    carbon = report.get("carbon") or {}
    energy = report.get("energy") or {}
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CO₂ avoided (kg)", _fmt(carbon.get("co2_avoided_kg", 0)))
    m2.metric("CO₂ net benefit (kg)", _fmt(carbon.get("co2_net_benefit_kg", 0)))
    m3.metric(_t(lang, "Tree-years", "Ағаш·жыл"), _fmt(carbon.get("trees_year_equiv", 0), 1))
    self_pct = _f(energy.get("self_sufficiency_pct", 0))
    m4.metric(_t(lang, "Self-sufficiency", "Өзін-өзі қамту"), f"{self_pct:.1f}%")

    # Prefer simple progress bar (avoids Plotly gauge crashes on some hosts)
    st.caption(_t(lang, "Self-sufficiency", "Өзін-өзі қамту"))
    st.progress(min(1.0, max(0.0, self_pct / 100.0)))

    try:
        from src.utils.visualization import gauge_metric
        from dashboard.utils.layout import plotly_chart

        plotly_chart(
            gauge_metric(
                self_pct,
                _t(lang, "Self-sufficiency", "Өзін-өзі қамту"),
                100,
                "%",
            )
        )
    except Exception:
        pass  # progress bar already shown

    eco = report.get("economics") or {}
    if eco:
        st.subheader(_t(lang, "Project economics", "Жоба экономикасы"))
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("LCOE $/kWh", _fmt(eco.get("lcoe", 0), 4))
        pb = _f(eco.get("payback_years", 0))
        k2.metric(
            _t(lang, "Payback years", "Өтелу жылы"),
            "∞" if pb == float("inf") or pb > 200 else _fmt(pb, 1),
        )
        k3.metric("ROI %", _fmt(eco.get("roi_percent_lifetime", 0), 1))
        k4.metric(
            _t(lang, "Annual net $", "Жылдық таза $"),
            _fmt(eco.get("annual_net_savings", 0)),
        )

    with st.expander(_t(lang, "Quick formulas", "Жылдам формулалар")):
        try:
            st.code(
                f"co2_avoided = {co2_avoided_kg(ren, factor):.1f} kg\n"
                f"LCOE = {lcoe(capex, ren, opex, life):.4f} $/kWh\n"
                f"payback = {payback_years(capex, ren * price - opex):.2f} y\n"
                f"ROI lifetime = {roi_percent(ren * price * life - opex * life - capex, capex):.1f} %"
            )
        except Exception as e:
            st.write(str(e))
