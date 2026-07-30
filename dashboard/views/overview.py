"""Home / overview tab — uses design-system components."""

from __future__ import annotations

import streamlit as st

from dashboard.components.metric_card import metric_row
from dashboard.components.models_status_banner import render_models_status_banner
from dashboard.components.prediction_card import prediction_card
from dashboard.components.states import empty_state
from dashboard.components.ui_kit import module_tile, section_header


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    texts = texts or {}
    models_status = models_status or {}
    is_kk = lang == "kk"

    section_header(
        "Platform overview" if not is_kk else "Платформаға шолу",
        "AI modules for hybrid solar–wind systems · Turkistan-ready"
        if not is_kk
        else "Гибридті күн–жел жүйелеріне арналған AI модульдері",
    )

    # Clear online / offline + demo metrics package (JSON)
    render_models_status_banner(lang, models_status)

    solar = float(st.session_state.get("last_solar", 0) or 0)
    wind = float(st.session_state.get("last_wind", 0) or 0)
    total = solar + wind
    rec = str(st.session_state.get("last_recommendation") or "—")

    if total > 0:
        metric_row(
            [
                {
                    "label": texts.get("solar_metric", "Solar"),
                    "value": f"{solar:.2f} kW",
                    "icon": "☀",
                    "variant": "solar",
                    "hint": "Last prediction",
                },
                {
                    "label": texts.get("wind_metric", "Wind"),
                    "value": f"{wind:.2f} kW",
                    "icon": "◌",
                    "variant": "wind",
                    "hint": "Last prediction",
                },
                {
                    "label": texts.get("total_metric", "Total"),
                    "value": f"{total:.2f} kW",
                    "icon": "⚡",
                    "variant": "total",
                    "hint": "Combined",
                },
            ]
        )
        prediction_card(
            title="Last dispatch" if not is_kk else "Соңғы диспетчер",
            recommendation=rec,
            solar_kw=solar,
            wind_kw=wind,
            total_kw=total,
        )
    else:
        empty_state(
            "No prediction data yet" if not is_kk else "Болжам деректері жоқ",
            "Open Forecasting or Predictions to populate metrics."
            if not is_kk
            else "Метрикаларды толтыру үшін Болжам немесе Predictions қойындысын ашыңыз.",
            icon="◇",
        )

    section_header(
        "Capability map" if not is_kk else "Мүмкіндіктер картасы",
        None,
    )

    modules = [
        ("📈", "Forecasting" if not is_kk else "Болжам",
         "RF / XGB solar–wind from weather features" if not is_kk else "RF/XGB ауа райы белгілерінен"),
        ("🔍", "Fault detection" if not is_kk else "Ақау анықтау",
         "YOLOv11 + clean/dirty triage" if not is_kk else "YOLOv11 + clean/dirty"),
        ("⚙", "Optimization" if not is_kk else "Оңтайландыру",
         "PuLP multi-hour hybrid + battery" if not is_kk else "PuLP көп сағаттық батарея"),
        ("💬", "AI Advisor" if not is_kk else "AI Кеңесші",
         "RAG · EN / KK" if not is_kk else "RAG · EN / KK"),
        ("🎓", "Learn & Explore" if not is_kk else "Оқу",
         "Lessons, labs, quizzes" if not is_kk else "Сабақ, зертхана, квиз"),
        ("🌿", "Sustainability" if not is_kk else "Тұрақтылық",
         "CO₂ · LCOE · ROI" if not is_kk else "CO₂ · LCOE · ROI"),
        ("📡", "Live monitoring" if not is_kk else "Live",
         "Solarman + weather" if not is_kk else "Solarman + ауа райы"),
    ]

    for i in range(0, len(modules), 3):
        chunk = modules[i : i + 3]
        cols = st.columns(3)
        for col, (icon, title, desc) in zip(cols, chunk):
            with col:
                module_tile(icon, title, desc)

    section_header("Quick start" if not is_kk else "Жылдам бастау", None)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            "1. `uvicorn api.main:app --port 8001`  \n"
            "2. Open module tabs  \n"
            "3. Sidebar: site · theme · optimization mode"
            if not is_kk
            else "1. `uvicorn api.main:app --port 8001`  \n"
            "2. Модуль қойындылары  \n"
            "3. Sidebar: орын · тема · оңтайландыру"
        )
    with c2:
        st.markdown(
            f"""
| Model | Status |
|-------|--------|
| Solar RF | {"Online" if models_status.get("solar") else "Offline"} |
| Wind XGB | {"Online" if models_status.get("wind") else "Offline"} |
| Forecast | {"Online" if models_status.get("forecast") else "Offline"} |
"""
        )
