"""
EcoPredict AI — premium unified Streamlit shell (2026 UI).

Run from project root:
    streamlit run dashboard/app.py

Architecture
------------
- Sidebar: brand, language, site, optimization mode, theme, API health
- Hero + glass metric cards
- Tabbed workspace wiring existing view modules under dashboard/views/
- Footer: commercial-style project strip

Legacy multipage routes under dashboard/pages/ still work independently.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Project root on path (before any dashboard / src imports)
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dashboard.utils import bootstrap  # noqa: F401  — path + static assets

import streamlit as st

from dashboard.components.sidebar import render_sidebar
from dashboard.components.ui_kit import footer, hero
from dashboard.styles.custom_css import inject_theme
from dashboard.utils.layout import apply_page_config

# View modules (lazy-friendly: import once at top for clearer errors)
from dashboard.views import advisor as view_advisor
from dashboard.views import diagnostics as view_faults
from dashboard.views import forecast as view_forecast
from dashboard.views import labs as view_labs
from dashboard.views import learn as view_learn
from dashboard.views import optimization as view_optimization
from dashboard.views import overview as view_overview
from dashboard.views import solarman as view_live
from dashboard.views import sustainability as view_sustainability

# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------
_FAVICON = Path(__file__).resolve().parent / "static" / "favicon.png"
apply_page_config(
    "EcoPredict AI",
    _FAVICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global chrome: sidebar → theme → session
# ---------------------------------------------------------------------------
lang, texts, models_status, theme = render_sidebar()
inject_theme(theme)

st.session_state["ep_lang"] = lang
st.session_state["ep_texts"] = texts
st.session_state["ep_models_status"] = models_status
st.session_state["ep_theme"] = theme

is_kk = lang == "kk"

# API status pills for hero
_pills: list[tuple[str, str]] = []
if models_status.get("solar") and models_status.get("wind"):
    _pills.append(("Models online", "ok") if not is_kk else ("Модельдер online", "ok"))
elif models_status.get("solar") or models_status.get("wind"):
    _pills.append(("Partial models", "warn") if not is_kk else ("Жартылай модельдер", "warn"))
else:
    _pills.append(("API offline", "err") if not is_kk else ("API offline", "err"))

site = st.session_state.get("ep_site") or {}
if site.get("label"):
    _pills.append((str(site["label"]), "accent"))

opt_mode = st.session_state.get("ep_opt_mode") or "balanced"
_pills.append((f"Mode: {opt_mode}", "default") if not is_kk else (f"Режим: {opt_mode}", "default"))
_pills.append((theme, "default"))

hero(
    title=texts.get("title") or ("EcoPredict AI" if not is_kk else "EcoPredict AI"),
    subtitle=(
        texts.get("subtitle")
        or (
            "Smart educational platform for hybrid renewable energy — "
            "forecasting, fault detection, optimization, and sustainability."
            if not is_kk
            else "Гибридті ЖЭК үшін ақылды білім беру платформасы — "
            "болжам, ақау анықтау, оңтайландыру және тұрақтылық."
        )
    ),
    kicker=(
        "AI · Energy · Education"
        if not is_kk
        else "AI · Энергия · Білім"
    ),
    pills=_pills,
)

# ---------------------------------------------------------------------------
# Primary navigation (tabs)
# ---------------------------------------------------------------------------
if is_kk:
    tab_labels = [
        "🏠 Басты",
        "📈 Болжам",
        "🔍 Ақау",
        "⚙ Оңтайландыру",
        "💬 AI Кеңесші",
        "🎓 Оқу",
        "🧪 Зертхана",
        "🌿 Тұрақтылық",
        "📡 Live",
    ]
else:
    tab_labels = [
        "🏠 Overview",
        "📈 Forecasting",
        "🔍 Fault Detection",
        "⚙ Optimization",
        "💬 AI Advisor",
        "🎓 Learn & Explore",
        "🧪 Labs",
        "🌿 Sustainability",
        "📡 Live Monitoring",
    ]

(
    tab_home,
    tab_fc,
    tab_fault,
    tab_opt,
    tab_adv,
    tab_learn,
    tab_labs,
    tab_sust,
    tab_live,
) = st.tabs(tab_labels)

with tab_home:
    view_overview.render(lang, texts, models_status)

with tab_fc:
    view_forecast.render(lang, texts, models_status)

with tab_fault:
    view_faults.render(lang, texts, models_status)

with tab_opt:
    # Pass sidebar optimization preference into session for future wiring
    st.session_state.setdefault("ep_opt_mode", "balanced")
    view_optimization.render(lang, texts, models_status)

with tab_adv:
    view_advisor.render(lang, texts, models_status)

with tab_learn:
    view_learn.render(lang, texts, models_status)

with tab_labs:
    view_labs.render(lang, texts, models_status)

with tab_sust:
    view_sustainability.render(lang, texts, models_status)

with tab_live:
    # Solarman live inverter + weather / economics
    view_live.render(lang, texts, models_status)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
footer(
    project="EcoPredict AI",
    tagline=(
        "Artificial Intelligence-Driven Optimization of Renewable Energy Systems"
        if not is_kk
        else "Жаңартылатын энергия жүйелерін AI-мен оңтайландыру"
    ),
    extra=(
        f"Site: {site.get('label', 'Turkistan, KZ')} · FastAPI :8001 · Streamlit multipage also under pages/"
        if not is_kk
        else f"Нысан: {site.get('label', 'Turkistan, KZ')} · FastAPI :8001 · pages/ multipage да бар"
    ),
)
