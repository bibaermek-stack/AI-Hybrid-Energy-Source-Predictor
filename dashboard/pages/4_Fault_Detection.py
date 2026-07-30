from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dashboard.utils import bootstrap  # noqa: F401

import streamlit as st

from dashboard.components.icons import icon_text
from dashboard.components.sidebar import render_sidebar
from dashboard.styles.custom_css import inject_theme
from dashboard.utils.layout import apply_page_config
from dashboard.views.diagnostics import render

_FAVICON = Path(__file__).resolve().parent.parent / "static" / "favicon.png"
apply_page_config("EcoPredict | Fault Detection", _FAVICON)

lang, texts, models_status, theme = render_sidebar()
inject_theme(theme)
st.session_state["ep_lang"] = lang
st.session_state["ep_texts"] = texts
st.session_state["ep_models_status"] = models_status

st.markdown(
    icon_text("diagnostics", (texts.get("title") or "EcoPredict AI") + " · Fault Detection", size=26, as_heading=True, level=1),
    unsafe_allow_html=True,
)
render(lang, texts, models_status)
