"""
Premium sidebar: brand, language, site location, optimization mode, theme, API health.
"""

from __future__ import annotations

import streamlit as st

from dashboard.components.ui_kit import brand_block, render_status_pill
from dashboard.utils.api_client import fetch_health
from dashboard.utils.i18n import get_texts, resolve_lang

# Demo sites used across monitoring / forecast defaults
SITE_OPTIONS = {
    "Turkistan, KZ": {"lat": 43.2973, "lon": 68.2517, "q": "Turkistan"},
    "Almaty, KZ": {"lat": 43.2220, "lon": 76.8512, "q": "Almaty"},
    "Astana, KZ": {"lat": 51.1694, "lon": 71.4491, "q": "Astana"},
    "Shymkent, KZ": {"lat": 42.3417, "lon": 69.5901, "q": "Shymkent"},
}

OPT_MODES = {
    "Balanced": "balanced",
    "Max profit": "max_profit",
    "Min CO₂": "min_co2",
}


def render_sidebar() -> tuple[str, dict, dict, str]:
    """
    Render global sidebar controls.

    Returns
    -------
    (lang_code, texts, models_status, theme)
    """
    # Everything brand/HTML must run under st.sidebar so it never spills into main.
    with st.sidebar:
        brand_block(
            name="EcoPredict AI",
            tagline="Hybrid · Forecast · Optimize",
            mark="⚡",
        )

        selected = st.selectbox(
            "Language / Тіл",
            ["Қазақша", "English", "Русский"],
            key="global_lang",
        )
        lang = resolve_lang(selected)
        texts = get_texts(lang)

        site_label = st.selectbox(
            "Site location" if lang != "kk" else "Нысан орны",
            list(SITE_OPTIONS.keys()),
            key="global_site",
        )
        site = SITE_OPTIONS[site_label]
        st.session_state["ep_site"] = {"label": site_label, **site}

        mode_labels = list(OPT_MODES.keys())
        if lang == "kk":
            mode_display = {
                "Balanced": "Теңдестірілген",
                "Max profit": "Макс. пайда",
                "Min CO₂": "Мин. CO₂",
            }
            mode_ui = st.selectbox(
                "Оңтайландыру режимі",
                mode_labels,
                format_func=lambda x: mode_display.get(x, x),
                key="global_opt_mode_ui",
            )
        else:
            mode_ui = st.selectbox(
                "Optimization mode",
                mode_labels,
                key="global_opt_mode_ui",
            )
        st.session_state["ep_opt_mode"] = OPT_MODES[mode_ui]

        theme = st.selectbox(
            "Theme / Тема",
            ["Dark", "Light"],
            key="global_theme",
            help="Premium dark navy / teal or clean light mode",
        )

        st.markdown("---")

        models_status = {
            "solar": False,
            "wind": False,
            "forecast": False,
            "lstm": False,
        }
        st.markdown(f"**{'System status' if lang != 'kk' else 'Жүйе күйі'}**")

        health = fetch_health()
        if health:
            ml = health.get("models_loaded") or {}
            models_status["solar"] = bool(ml.get("solar"))
            models_status["wind"] = bool(ml.get("wind"))
            models_status["forecast"] = bool(ml.get("forecast") or ml.get("solar"))
            models_status["lstm"] = models_status["forecast"]

            status = (health.get("status") or "").lower()
            if status == "healthy":
                render_status_pill("API Online", "ok")
            else:
                render_status_pill("API Degraded", "warn")

            backend = health.get("forecast_backend") or "random_forest"
            st.caption(
                f"Forecast: {backend} · "
                f"S{'✓' if models_status['solar'] else '—'} "
                f"W{'✓' if models_status['wind'] else '—'} "
                f"F{'✓' if models_status['forecast'] else '—'}"
            )
        else:
            render_status_pill("API Offline", "err")
            st.caption(
                "Start API on :8001 · paper metrics still in artifacts/*.json"
                if lang != "kk"
                else "API :8001 · paper метрика artifacts/*.json-да"
            )
            if not (models_status.get("solar") or models_status.get("wind")):
                st.caption(
                    "Models offline UI on Overview"
                    if lang != "kk"
                    else "Overview-да Models offline баннері"
                )

        st.markdown("---")
        st.caption(
            "Modules · Forecast · Faults · Opt · Advisor · Learn · Labs · Live"
            if lang != "kk"
            else "Модульдер · Болжам · Ақау · Оңтай · Кеңес · Оқу · Labs · Live"
        )

    return lang, texts, models_status, theme
