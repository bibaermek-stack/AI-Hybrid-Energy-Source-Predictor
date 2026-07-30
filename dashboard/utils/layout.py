"""Shared Streamlit page layout helpers (mobile-friendly defaults)."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

_DEFAULT_FAVICON = Path(__file__).resolve().parent.parent / "static" / "favicon.png"


def apply_page_config(
    title: str,
    favicon: str | Path | None = None,
    *,
    layout: str = "wide",
    initial_sidebar_state: str = "expanded",
) -> None:
    """
    Standard page_config for EcoPredict pages.

    Sidebar starts expanded on desktop so brand / theme / site controls
    are visible; phones can still collapse via Streamlit chrome.
    """
    icon = favicon if favicon is not None else _DEFAULT_FAVICON
    if isinstance(icon, Path):
        icon = str(icon) if icon.exists() else None
    st.set_page_config(
        page_title=title,
        page_icon=icon,
        layout=layout,
        initial_sidebar_state=initial_sidebar_state,
    )


def chart_height(desktop: int = 360, mobile: int = 260) -> int:
    """
    Prefer shorter charts on narrow viewports when we can detect them.
    Streamlit has no reliable server-side width; default to desktop height
    and let CSS constrain overflow. Callers may pass mobile= for future use.
    """
    # Heuristic: if user-agent looks mobile (when available via headers)
    try:
        ua = (st.context.headers.get("User-Agent") or "").lower()
        if any(x in ua for x in ("mobile", "android", "iphone", "ipad")):
            return mobile
    except Exception:
        pass
    return desktop


def iframe_3d_height(desktop: int = 560, mobile: int = 340) -> int:
    """3D viewer iframe height: shorter on phones for less scroll."""
    try:
        ua = (st.context.headers.get("User-Agent") or "").lower()
        if any(x in ua for x in ("mobile", "android", "iphone", "ipod")):
            return mobile
        if "ipad" in ua:
            return min(desktop, 420)
    except Exception:
        pass
    return desktop


def width_stretch() -> dict:
    """Streamlit ≥1.50 prefers width='stretch' over use_container_width=True."""
    return {"width": "stretch"}


def safe_dataframe(df, **kwargs):
    """
    st.dataframe that avoids Arrow type errors on mixed object columns
    (e.g. Solarman raw keys with firmware strings like '0000').
    """
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(
                lambda x: "" if x is None else str(x)
            )
    kw = {**width_stretch(), **kwargs}
    # Drop deprecated alias if both present
    kw.pop("use_container_width", None)
    return st.dataframe(out, **kw)


def plotly_chart(fig, **kwargs):
    """st.plotly_chart with modern width=stretch default."""
    kw = {**width_stretch(), **kwargs}
    kw.pop("use_container_width", None)
    return st.plotly_chart(fig, **kw)
