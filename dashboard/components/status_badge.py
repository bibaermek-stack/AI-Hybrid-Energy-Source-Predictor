"""Status badge / pill component."""

from __future__ import annotations

from html import escape
from typing import Literal

from dashboard.components.ui_kit import _html

Kind = Literal["ok", "warn", "err", "accent", "default"]


def status_badge(label: str, kind: Kind = "default") -> str:
    """Return HTML string for an inline status pill."""
    cls = f"ep-pill ep-pill--{kind}" if kind in ("ok", "warn", "err", "accent") else "ep-pill"
    return f'<span class="{cls}">{escape(label)}</span>'


def render_status_badge(label: str, kind: Kind = "default") -> None:
    """Draw a status badge in the Streamlit document."""
    _html(status_badge(label, kind))


def api_status_badge(
    *,
    online: bool,
    degraded: bool = False,
    lang: str = "en",
) -> None:
    """Convenience badge for API health."""
    if online and not degraded:
        label = "API Online" if lang != "kk" else "API Online"
        render_status_badge(label, "ok")
    elif online and degraded:
        label = "API Degraded" if lang != "kk" else "API Degraded"
        render_status_badge(label, "warn")
    else:
        label = "API Offline" if lang != "kk" else "API Offline"
        render_status_badge(label, "err")
