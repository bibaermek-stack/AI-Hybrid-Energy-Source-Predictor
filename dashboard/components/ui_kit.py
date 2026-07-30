"""
Reusable premium UI primitives for EcoPredict AI.

Use these helpers so every page shares the same glass cards, hero, pills, and footer.
"""

from __future__ import annotations

from html import escape
from typing import Literal

import streamlit as st

Variant = Literal["solar", "wind", "total", "default"]


def _html(fragment: str) -> None:
    """Render HTML fragment (prefer st.html so markup is not shown as plain text)."""
    fragment = (fragment or "").strip()
    if not fragment:
        return
    if hasattr(st, "html"):
        try:
            st.html(fragment)
            return
        except Exception:
            pass
    st.markdown(fragment, unsafe_allow_html=True)


def hero(
    title: str,
    subtitle: str,
    *,
    kicker: str = "Smart Energy Platform",
    pills: list[tuple[str, str]] | None = None,
) -> None:
    """
    Top page hero with gradient title.

    pills: list of (label, kind) where kind in ok|warn|err|accent|default
    """
    pills = pills or []
    pills_html = ""
    for label, kind in pills:
        cls = f"ep-pill ep-pill--{kind}" if kind in ("ok", "warn", "err", "accent") else "ep-pill"
        pills_html += f'<span class="{cls}">{escape(label)}</span>'

    _html(
        f"""
        <div class="ep-hero">
          <div class="ep-hero-kicker">{escape(kicker)}</div>
          <h1>{escape(title)}</h1>
          <p class="ep-hero-sub">{escape(subtitle)}</p>
          <div class="ep-hero-meta">{pills_html}</div>
        </div>
        """
    )


def section_header(title: str, caption: str | None = None) -> None:
    """Section title with teal accent bar."""
    _html(
        f'<div class="ep-section-title"><span class="ep-bar"></span>{escape(title)}</div>'
    )
    if caption:
        st.caption(caption)


def metric_card(
    label: str,
    value: str,
    *,
    hint: str | None = None,
    icon: str = "◆",
    variant: Variant = "default",
) -> None:
    """Glass metric card (emoji/symbol icon — no external images)."""
    hint_html = f'<div class="ep-card-hint">{escape(hint)}</div>' if hint else ""
    _html(
        f"""
        <div class="ep-card">
          <div class="ep-card-label"><span>{escape(icon)}</span>{escape(label)}</div>
          <div class="ep-card-value ep-card-value--{variant}">{escape(value)}</div>
          {hint_html}
        </div>
        """
    )


def metric_row(
    items: list[dict],
) -> None:
    """
    Render a row of metric cards.

    Each item: {label, value, icon?, variant?, hint?}
    """
    if not items:
        return
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            metric_card(
                item.get("label", ""),
                item.get("value", "—"),
                hint=item.get("hint"),
                icon=item.get("icon", "◆"),
                variant=item.get("variant", "default"),  # type: ignore[arg-type]
            )


def module_tile(icon: str, title: str, description: str) -> None:
    """Feature / module overview tile."""
    _html(
        f"""
        <div class="ep-module-tile">
          <div class="ep-module-icon">{escape(icon)}</div>
          <h4>{escape(title)}</h4>
          <p>{escape(description)}</p>
        </div>
        """
    )


def status_pill(label: str, kind: str = "default") -> str:
    """Return HTML for an inline status pill (use with render_status_pill or st.html)."""
    cls = f"ep-pill ep-pill--{kind}" if kind in ("ok", "warn", "err", "accent") else "ep-pill"
    return f'<span class="{cls}">{escape(label)}</span>'


def render_status_pill(label: str, kind: str = "default") -> None:
    """Draw a status pill in the UI (safe injection)."""
    _html(status_pill(label, kind))


def footer(
    *,
    project: str = "EcoPredict AI",
    tagline: str = "AI-Driven Optimization of Renewable Energy Systems",
    extra: str | None = None,
) -> None:
    """Clean commercial-style footer."""
    extra_html = f"<br/>{escape(extra)}" if extra else ""
    _html(
        f"""
        <div class="ep-footer">
          <strong>{escape(project)}</strong> · {escape(tagline)}
          {extra_html}
          <br/>© 2026 · Educational & research platform · EN / KK / RU
        </div>
        """
    )


def brand_block(
    name: str = "EcoPredict AI",
    tagline: str = "Hybrid Energy Intelligence",
    mark: str = "⚡",
) -> None:
    """Sidebar brand / logo block."""
    _html(
        f"""
        <div class="ep-brand">
          <div class="ep-brand-mark">{escape(mark)}</div>
          <div class="ep-brand-text">
            <strong>{escape(name)}</strong>
            <span>{escape(tagline)}</span>
          </div>
        </div>
        """
    )


# Re-export energy helpers for backward compatibility
def display_energy_metrics(
    solar: float,
    wind: float,
    total: float,
    labels: dict | None = None,
) -> None:
    from dashboard.components.metric_card import metric_row as _metric_row

    labels = labels or {"solar": "Solar", "wind": "Wind", "total": "Total"}
    _metric_row(
        [
            {
                "label": labels.get("solar", "Solar"),
                "value": f"{solar:.2f} kW",
                "icon": "☀",
                "variant": "solar",
                "hint": "PV generation",
            },
            {
                "label": labels.get("wind", "Wind"),
                "value": f"{wind:.2f} kW",
                "icon": "◌",
                "variant": "wind",
                "hint": "Wind generation",
            },
            {
                "label": labels.get("total", "Total"),
                "value": f"{total:.2f} kW",
                "icon": "⚡",
                "variant": "total",
                "hint": "Combined output",
            },
        ]
    )
