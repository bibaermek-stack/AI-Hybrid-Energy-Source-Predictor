"""One-shot splitter: dashboard/app.py → modular package. Run from project root."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"
BACKUP = ROOT / "app_monolith_backup.py"


def main() -> None:
    app = APP.read_text(encoding="utf-8")
    shutil.copy2(APP, BACKUP)
    print("backup", BACKUP.stat().st_size)

    for d in ("components", "styles", "utils", "views", "pages"):
        (ROOT / d).mkdir(exist_ok=True)
        init = ROOT / d / "__init__.py"
        if not init.exists():
            init.write_text('"""EcoPredict dashboard package."""\n', encoding="utf-8")

    # Localization
    m = re.search(
        r"# Localization Dictionary\nLOCALIZATION = (\{.*?\n\})\n\n# st\.set_page_config",
        app,
        re.S,
    )
    if not m:
        raise SystemExit("LOCALIZATION block not found")
    loc_src = m.group(1)

    # CSS between <style>...</style>
    m2 = re.search(r"<style>(.*?)</style>", app, re.S)
    css = m2.group(1) if m2 else ""

    markers = [
        (
            "predict",
            "# ==================== TAB 1: PREDICT & OPTIMIZE ====================",
            "# ==================== TAB 2: 24-HOUR FORECASTING ====================",
        ),
        (
            "forecast",
            "# ==================== TAB 2: 24-HOUR FORECASTING ====================",
            "# ==================== TAB 3: SOLARMAN & ECONOMICS ====================",
        ),
        (
            "solarman",
            "# ==================== TAB 3: SOLARMAN & ECONOMICS ====================",
            "# ==================== TAB 4: FAULT DIAGNOSTICS & SOLUTIONS ====================",
        ),
        (
            "diagnostics",
            "# ==================== TAB 4: FAULT DIAGNOSTICS & SOLUTIONS ====================",
            "# ==================== TAB 5: AI MODEL TRAINING CENTER ====================",
        ),
        (
            "training",
            "# ==================== TAB 5: AI MODEL TRAINING CENTER ====================",
            "# ==================== TAB 6: 3D THERMAL MODEL ====================",
        ),
        (
            "model3d",
            "# ==================== TAB 6: 3D THERMAL MODEL ====================",
            None,
        ),
    ]

    bodies: dict[str, str] = {}
    for name, start, end in markers:
        i = app.find(start)
        if i < 0:
            raise SystemExit(f"marker missing: {start}")
        j = app.find(end) if end else len(app)
        lines = app[i:j].splitlines()
        out: list[str] = []
        skip_with = True
        for li, line in enumerate(lines):
            if li == 0 and line.startswith("# ==="):
                continue
            if skip_with and re.match(r"^with tab\d+:", line):
                skip_with = False
                continue
            if line.startswith("    "):
                out.append(line[4:])
            else:
                out.append(line)
        bodies[name] = "\n".join(out).strip() + "\n"
        print(name, len(out), "lines")

    (ROOT / "utils" / "config.py").write_text(
        '''"""API URLs and environment config for EcoPredict dashboard."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/predict")
EXPLAIN_URL = os.getenv("EXPLAIN_URL", "http://127.0.0.1:8001/explain")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8001/health")
FORECAST_URL = os.getenv("FORECAST_URL", "http://127.0.0.1:8001/forecast-batch")
CHAT_URL = os.getenv("CHAT_URL", "http://127.0.0.1:8001/chat")
SOLARMAN_PROCESS_URL = os.getenv("SOLARMAN_PROCESS_URL", "http://127.0.0.1:8001/solarman/process")
SOLARMAN_ROI_URL = os.getenv("SOLARMAN_ROI_URL", "http://127.0.0.1:8001/solarman/roi")
SOLARMAN_WEATHER_URL = os.getenv("SOLARMAN_WEATHER_URL", "http://127.0.0.1:8001/solarman/weather")
SOLARMAN_ALERT_URL = os.getenv("SOLARMAN_ALERT_URL", "http://127.0.0.1:8001/solarman/alert")
SOLARMAN_FC_URL = os.getenv("SOLARMAN_FC_URL", "http://127.0.0.1:8001/solarman/forecast")
SOLARMAN_LIVE_URL = os.getenv("SOLARMAN_LIVE_URL", "http://127.0.0.1:8001/solarman/live")
SOLARMAN_HISTORY_URL = os.getenv("SOLARMAN_HISTORY_URL", "http://127.0.0.1:8001/solarman/history")
SOLARMAN_STATUS_URL = os.getenv("SOLARMAN_STATUS_URL", "http://127.0.0.1:8001/solarman/status")
SOLARMAN_CONFIGURE_URL = os.getenv("SOLARMAN_CONFIGURE_URL", "http://127.0.0.1:8001/solarman/configure")
''',
        encoding="utf-8",
    )

    (ROOT / "utils" / "i18n.py").write_text(
        f'''"""Localization strings (kk / en / ru)."""
from __future__ import annotations

LOCALIZATION = {loc_src}

def resolve_lang(selected: str) -> str:
    s = (selected or "en").strip()
    if s in ("kk", "en", "ru"):
        return s
    if s in ("Қазақша", "Kazakh", "KZ"):
        return "kk"
    if s in ("Русский", "Russian", "RU"):
        return "ru"
    return "en"


def get_texts(lang: str) -> dict:
    if lang == "ru":
        base = dict(LOCALIZATION["en"])
        base.update({{
            "title": "⚡ EcoPredict AI Платформа",
            "subtitle": "Прогноз и оптимизация гибридной солнечной и ветровой генерации",
            "tab_predict": "🔮 Оптимизация",
            "tab_forecast": "📈 24-часовой прогноз",
            "tab_chat": "💬 AI-консультант",
            "tab_solarman": "📊 Solarman и экономика",
            "tab_diagnostics": "🛠️ Диагностика",
            "tab_training": "🧠 Обучение моделей",
            "tab_3d_model": "📐 3D модель инвертора",
            "predict_btn": "🔮 Прогноз энергии",
            "solar_label": "Солнце",
            "wind_label": "Ветер",
            "hybrid_label": "Гибрид",
            "conn_error": "🌐 Нет связи с API. Запущен ли backend?",
            "timeout_error": "⏱️ Таймаут API.",
        }})
        return base
    return LOCALIZATION.get(lang, LOCALIZATION["en"])
''',
        encoding="utf-8",
    )

    # Escape CSS for triple-quoted string carefully
    css_escaped = css.replace("\\", "\\\\")
    (ROOT / "styles" / "custom_css.py").write_text(
        f'''"""Theme CSS for EcoPredict dashboard."""
from __future__ import annotations

import streamlit as st

DARK_CSS = r"""{css_escaped}"""

LIGHT_CSS = r"""
    h1, h2, h3 {{ font-family: 'Outfit', 'Inter', sans-serif !important; font-weight: 700 !important; }}
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 100%) !important;
        color: #0f172a !important;
    }}
    .energy-card, [data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255,255,255,0.92) !important;
        border: 1px solid rgba(15, 23, 42, 0.08) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06) !important;
    }}
    .metric-value {{
        font-size: 2.2rem; font-weight: 800; margin-top: 5px;
        background: linear-gradient(90deg, #2563eb 0%, #7c3aed 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }}
    .stButton>button {{
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%) !important;
        color: white !important; border: none !important; border-radius: 10px !important;
        font-weight: 600 !important;
    }}
"""


def inject_theme(theme: str = "Dark") -> None:
    css = LIGHT_CSS if str(theme).lower().startswith("light") else DARK_CSS
    st.markdown(f"<style>{{css}}</style>", unsafe_allow_html=True)
''',
        encoding="utf-8",
    )

    (ROOT / "utils" / "api_client.py").write_text(
        '''"""HTTP helpers for EcoPredict API."""
from __future__ import annotations

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from dashboard.utils.config import HEALTH_URL


def create_session_with_retries() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_health(timeout: float = 2.0) -> dict | None:
    try:
        r = requests.get(HEALTH_URL, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None
''',
        encoding="utf-8",
    )

    (ROOT / "utils" / "models_loader.py").write_text(
        '''"""Cached ML model loaders for dashboard pages."""
from __future__ import annotations

import os

import streamlit as st


@st.cache_resource
def load_clean_dirty_model():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"
    import tensorflow as tf

    model_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "artifacts", "clean_dirty_model.h5")
    )
    if not os.path.exists(model_path):
        model_path = "artifacts/clean_dirty_model.h5"
    return tf.keras.models.load_model(model_path)


@st.cache_resource
def load_yolo_model():
    from ultralytics import YOLO

    model_path = os.path.abspath(
        "yolo_fault_detection/runs/runs/detect/train/weights/best.pt"
    )
    return YOLO(model_path)
''',
        encoding="utf-8",
    )

    (ROOT / "components" / "metrics_cards.py").write_text(
        '''"""Reusable metric / energy cards."""
from __future__ import annotations

import streamlit as st


def energy_metric_card(label: str, value: str, gradient: str = "58a6ff, bc8cff") -> None:
    g1, g2 = [x.strip() for x in gradient.split(",")]
    st.markdown(
        f"""
        <div class="energy-card">
            <div style="font-size:0.9rem;color:#8b949e;text-transform:uppercase;">{label}</div>
            <div class="metric-value" style="background: linear-gradient(90deg, #{g1} 0%, #{g2} 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def display_energy_metrics(solar: float, wind: float, total: float, labels: dict | None = None) -> None:
    labels = labels or {"solar": "☀️ Solar", "wind": "💨 Wind", "total": "⚡ Total"}
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric(labels["solar"], f"{solar:.2f} kW")
    with c2:
        st.metric(labels["wind"], f"{wind:.2f} kW")
    with c3:
        st.metric(labels["total"], f"{total:.2f} kW")
''',
        encoding="utf-8",
    )

    (ROOT / "components" / "sidebar.py").write_text(
        '''"""Global sidebar: language, theme, API status."""
from __future__ import annotations

import streamlit as st

from dashboard.utils.api_client import fetch_health
from dashboard.utils.i18n import get_texts, resolve_lang


def render_sidebar() -> tuple[str, dict, dict, str]:
    """
    Returns (lang_code, texts, models_status, theme).
    """
    st.sidebar.markdown("## ⚡ EcoPredict AI")
    selected = st.sidebar.selectbox(
        "Language / Тіл / Язык",
        ["Қазақша", "English", "Русский"],
        key="global_lang",
    )
    lang = resolve_lang(selected)
    texts = get_texts(lang)

    theme = st.sidebar.selectbox(
        "Theme / Тема",
        ["Dark", "Light"],
        key="global_theme",
    )

    models_status = {"solar": False, "wind": False, "lstm": False}
    st.sidebar.markdown("---")
    st.sidebar.subheader("API Status / Сервер")
    health = fetch_health()
    if health:
        ml = health.get("models_loaded") or {}
        models_status["solar"] = bool(ml.get("solar"))
        models_status["wind"] = bool(ml.get("wind"))
        models_status["lstm"] = bool(ml.get("lstm"))
        if health.get("status") == "healthy":
            st.sidebar.success("🟢 Active")
        else:
            st.sidebar.warning("🟡 Degraded")
        st.sidebar.caption(
            f"Solar: {'OK' if models_status['solar'] else '—'} · "
            f"Wind: {'OK' if models_status['wind'] else '—'} · "
            f"LSTM: {'OK' if models_status['lstm'] else '—'}"
        )
    else:
        st.sidebar.error("🔴 Offline")
        st.sidebar.caption("Start: uvicorn api.main:app --port 8001")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
**Pages**
- Home  
- Predictions  
- Forecast  
- Solarman  
- Fault Detection  
- Training  
- 3D Inverter  
"""
    )
    return lang, texts, models_status, theme
''',
        encoding="utf-8",
    )

    (ROOT / "components" / "charts.py").write_text(
        '''"""Shared Plotly chart helpers."""
from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def style_fig(fig: go.Figure, height: int = 340) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        legend=dict(orientation="h"),
    )
    return fig


def bar_solar_wind(solar: float, wind: float, labels: dict) -> None:
    fig = px.bar(
        {labels.get("x", "Source"): [labels.get("solar", "Solar"), labels.get("wind", "Wind")],
         labels.get("y", "Power (kW)"): [solar, wind]},
        x=labels.get("x", "Source"),
        y=labels.get("y", "Power (kW)"),
        color=labels.get("x", "Source"),
        color_discrete_map={
            labels.get("solar", "Solar"): "#FDB462",
            labels.get("wind", "Wind"): "#80B1D3",
        },
        title=labels.get("title", "Energy comparison"),
    )
    st.plotly_chart(style_fig(fig), use_container_width=True)
''',
        encoding="utf-8",
    )

    # View modules — inject common imports + body
    view_header = '''"""View extracted from legacy monolith tab."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

from dashboard.utils.api_client import create_session_with_retries
from dashboard.utils.config import (
    API_URL,
    CHAT_URL,
    EXPLAIN_URL,
    FORECAST_URL,
    HEALTH_URL,
    SOLARMAN_ALERT_URL,
    SOLARMAN_CONFIGURE_URL,
    SOLARMAN_FC_URL,
    SOLARMAN_HISTORY_URL,
    SOLARMAN_LIVE_URL,
    SOLARMAN_PROCESS_URL,
    SOLARMAN_ROI_URL,
    SOLARMAN_STATUS_URL,
    SOLARMAN_WEATHER_URL,
)
from dashboard.utils.models_loader import load_clean_dirty_model, load_yolo_model

load_dotenv()


def render(lang: str, texts: dict, models_status: dict | None = None) -> None:
    models_status = models_status or {"solar": False, "wind": False, "lstm": False}
'''

    for name, body in bodies.items():
        # Fix relative paths that assumed cwd
        body2 = body
        path = ROOT / "views" / f"{name}.py"
        path.write_text(view_header + "\n" + _indent(body2, 4) + "\n", encoding="utf-8")
        print("wrote", path.name)

    # Home app.py
    (ROOT / "app.py").write_text(
        '''"""
EcoPredict AI — multipage Streamlit entry (Home).

Run:
  streamlit run dashboard/app.py

Pages live in dashboard/pages/
Legacy monolith backup: dashboard/app_monolith_backup.py
"""
from __future__ import annotations

import streamlit as st

from dashboard.components.metrics_cards import display_energy_metrics
from dashboard.components.sidebar import render_sidebar
from dashboard.styles.custom_css import inject_theme
from dashboard.utils.api_client import create_session_with_retries
from dashboard.utils.config import API_URL

st.set_page_config(
    page_title="EcoPredict AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

lang, texts, models_status, theme = render_sidebar()
inject_theme(theme)

st.title(texts.get("title", "⚡ EcoPredict AI"))
st.markdown(f"**{texts.get('subtitle', '')}**")

# Live snapshot from last prediction in session, else sample
solar = float(st.session_state.get("last_solar", 0) or 0)
wind = float(st.session_state.get("last_wind", 0) or 0)
total = solar + wind
if total <= 0:
    st.info(
        "Сол жақтағы мәзірден бет таңдаңыз · Use the sidebar pages menu."
        if lang == "kk"
        else "Open a page from the sidebar to run models."
    )
else:
    display_energy_metrics(
        solar,
        wind,
        total,
        {
            "solar": texts.get("solar_metric", "Solar"),
            "wind": texts.get("wind_metric", "Wind"),
            "total": texts.get("total_metric", "Total"),
        },
    )
    rec = st.session_state.get("last_recommendation", "—")
    st.success(texts.get("recommended", "Recommended: **{source}**").format(source=rec))

st.markdown("---")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 🔮 " + (texts.get("tab_predict") or "Predictions"))
    st.caption("Hybrid solar/wind dispatch" if lang == "en" else "Гибридті күн/жел диспетчерлеу")
with c2:
    st.markdown("### 📊 " + (texts.get("tab_solarman") or "Solarman"))
    st.caption("Live inverter SN 2501221272")
with c3:
    st.markdown("### 🛠️ " + (texts.get("tab_diagnostics") or "Faults"))
    st.caption("YOLO / CNN panel diagnostics")

st.markdown("---")
st.markdown(
    """
### 🚀 Quick start
1. Backend: `uvicorn api.main:app --port 8001`
2. Dashboard: `streamlit run dashboard/app.py`
3. Pages → **Predictions**, **Solarman**, **Fault Detection**, **3D Inverter**
"""
)

# store context for pages (same process)
st.session_state["ep_lang"] = lang
st.session_state["ep_texts"] = texts
st.session_state["ep_models_status"] = models_status
st.session_state["ep_theme"] = theme
''',
        encoding="utf-8",
    )

    # Multipage wrappers
    pages = [
        ("1_🔮_Predictions.py", "predict", "Predictions"),
        ("2_📈_Forecast.py", "forecast", "Forecast"),
        ("3_📊_Solarman.py", "solarman", "Solarman"),
        ("4_🛠️_Fault_Detection.py", "diagnostics", "Fault Detection"),
        ("5_🧠_Training.py", "training", "Training"),
        ("6_📐_3D_Inverter.py", "model3d", "3D Inverter"),
    ]
    for fname, mod, title in pages:
        (ROOT / "pages" / fname).write_text(
            f'''"""Streamlit multipage: {title}."""
from __future__ import annotations

import streamlit as st

from dashboard.components.sidebar import render_sidebar
from dashboard.styles.custom_css import inject_theme
from dashboard.views.{mod} import render

st.set_page_config(page_title="EcoPredict · {title}", page_icon="⚡", layout="wide")

lang, texts, models_status, theme = render_sidebar()
inject_theme(theme)
st.session_state["ep_lang"] = lang
st.session_state["ep_texts"] = texts
st.session_state["ep_models_status"] = models_status

st.title(texts.get("title", "EcoPredict AI") + f" · {title}")
render(lang, texts, models_status)
''',
            encoding="utf-8",
        )
        print("page", fname)

    print("DONE")


def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())


if __name__ == "__main__":
    main()
