"""
Inline SVG icons for EcoPredict UI (no emoji dependency).

Usage:
    from dashboard.components.icons import icon, icon_text, strip_emoji

    st.markdown(icon_text("zap", "EcoPredict AI"), unsafe_allow_html=True)
    st.markdown(icon("sun", size=20), unsafe_allow_html=True)
"""
from __future__ import annotations

import re
from html import escape

# Minimal stroke icons (Lucide-style, 24 viewBox)
_PATHS: dict[str, str] = {
    # brand / energy
    "zap": '<path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>',
    "sun": (
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2'
        'M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/>'
    ),
    "wind": (
        '<path d="M17.7 7.7A2.5 2.5 0 1 1 19 12H2"/>'
        '<path d="M9.6 4.6A2 2 0 1 1 11 8H2"/>'
        '<path d="M12.6 19.4A2 2 0 1 0 14 16H2"/>'
    ),
    "battery": (
        '<rect x="2" y="7" width="16" height="10" rx="2"/>'
        '<path d="M22 11v2M6 11v2M10 11v2M14 11v2"/>'
    ),
    # navigation / features
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "chart": (
        '<path d="M3 3v18h18"/>'
        '<path d="M7 16l4-8 4 4 5-7"/>'
    ),
    "bar_chart": (
        '<path d="M3 3v18h18"/>'
        '<rect x="7" y="10" width="3" height="8"/>'
        '<rect x="12" y="6" width="3" height="12"/>'
        '<rect x="17" y="12" width="3" height="6"/>'
    ),
    "gauge": (
        '<path d="M12 14l4-4"/>'
        '<path d="M3.34 19a10 10 0 1 1 17.32 0"/>'
    ),
    "cpu": (
        '<rect x="4" y="4" width="16" height="16" rx="2"/>'
        '<rect x="9" y="9" width="6" height="6"/>'
        '<path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>'
    ),
    "box": (
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
        '<path d="M3.3 7L12 12l8.7-5M12 22V12"/>'
    ),
    "cube": (
        '<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>'
    ),
    "search": (
        '<circle cx="11" cy="11" r="8"/>'
        '<path d="m21 21-4.3-4.3"/>'
    ),
    "wrench": (
        '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>'
    ),
    "alert": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<path d="M12 9v4M12 17h.01"/>'
    ),
    "check": (
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>'
    ),
    "check_circle": (
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/>'
    ),
    "x_circle": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="m15 9-6 6M9 9l6 6"/>'
    ),
    "info": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 16v-4M12 8h.01"/>'
    ),
    "message": (
        '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>'
    ),
    "bot": (
        '<rect x="3" y="11" width="18" height="10" rx="2"/>'
        '<circle cx="12" cy="5" r="2"/>'
        '<path d="M12 7v4M8 16h0M16 16h0"/>'
    ),
    "plug": (
        '<path d="M12 22v-5M9 8V2M15 8V2M6 8h12v4a6 6 0 0 1-12 0V8Z"/>'
    ),
    "radio": (
        '<circle cx="12" cy="12" r="2"/>'
        '<path d="M16.24 7.76a6 6 0 0 1 0 8.49M7.76 16.24a6 6 0 0 1 0-8.49'
        'M19.07 4.93a10 10 0 0 1 0 14.14M4.93 19.07a10 10 0 0 1 0-14.14"/>'
    ),
    "globe": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'
    ),
    "clock": (
        '<circle cx="12" cy="12" r="10"/>'
        '<path d="M12 6v6l4 2"/>'
    ),
    "refresh": (
        '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/>'
        '<path d="M21 3v5h-5M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/>'
        '<path d="M8 16H3v5"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42'
        'M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>'
    ),
    "layers": (
        '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/>'
        '<path d="m22 12.5-8.58 3.91a2 2 0 0 1-1.66 0L2 12.5"/>'
        '<path d="m22 17.5-8.58 3.91a2 2 0 0 1-1.66 0L2 17.5"/>'
    ),
    "home": (
        '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/>'
    ),
    "download": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="7 10 12 15 17 10"/>'
        '<line x1="12" y1="15" x2="12" y2="3"/>'
    ),
    "upload": (
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>'
        '<polyline points="17 8 12 3 7 8"/>'
        '<line x1="12" y1="3" x2="12" y2="15"/>'
    ),
    "lightbulb": (
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'
        '<path d="M9 18h6M10 22h4"/>'
    ),
    "thermometer": (
        '<path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/>'
    ),
    "droplet": (
        '<path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/>'
    ),
    "moon": (
        '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>'
    ),
    "circle": '<circle cx="12" cy="12" r="8"/>',
    "dot": '<circle cx="12" cy="12" r="5" fill="currentColor" stroke="none"/>',
    "status_ok": '<circle cx="12" cy="12" r="8" fill="#3fb950" stroke="none"/>',
    "status_warn": '<circle cx="12" cy="12" r="8" fill="#d29922" stroke="none"/>',
    "status_err": '<circle cx="12" cy="12" r="8" fill="#f85149" stroke="none"/>',
    "rocket": (
        '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>'
        '<path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>'
        '<path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>'
    ),
    "image": (
        '<rect x="3" y="3" width="18" height="18" rx="2"/>'
        '<circle cx="9" cy="9" r="2"/>'
        '<path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>'
    ),
    "sliders": (
        '<path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"/>'
    ),
    "key": (
        '<circle cx="7.5" cy="15.5" r="5.5"/>'
        '<path d="m21 2-9.6 9.6M15.5 7.5l3 3L22 7l-3-3"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
        '<path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3"/>'
    ),
    "link": (
        '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
    ),
}

# Semantic aliases used across the app
ALIASES: dict[str, str] = {
    "energy": "zap",
    "solar": "sun",
    "wind": "wind",
    "predict": "activity",
    "forecast": "chart",
    "solarman": "bar_chart",
    "fault": "search",
    "diagnostics": "wrench",
    "training": "cpu",
    "model3d": "box",
    "chat": "message",
    "advisor": "bot",
    "api": "radio",
    "ok": "status_ok",
    "warn": "status_warn",
    "error": "status_err",
    "offline": "status_err",
    "online": "status_ok",
    "degraded": "status_warn",
    "warning": "alert",
    "success": "check",
    "tip": "lightbulb",
    "temp": "thermometer",
    "inverter": "plug",
    "reload": "refresh",
    "params": "sliders",
    "analysis": "chart",
    "start": "rocket",
}


# Broad emoji strip (covers most UI emoji)
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # misc symbols & pictographs + supplemental
    "\U00002700-\U000027BF"  # dingbats
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0000200D"             # ZWJ
    "]+",
    flags=re.UNICODE,
)


def strip_emoji(text: str | None) -> str:
    if not text:
        return ""
    return _EMOJI_RE.sub("", str(text)).strip()


def clean_texts(texts: dict) -> dict:
    """Return a copy of localization dict with emoji removed from string values."""
    out = {}
    for k, v in texts.items():
        if isinstance(v, str):
            out[k] = strip_emoji(v)
        else:
            out[k] = v
    return out


def icon(
    name: str,
    size: int = 18,
    color: str = "currentColor",
    stroke_width: float = 2,
    class_name: str = "ep-icon",
) -> str:
    """Return inline SVG markup."""
    key = ALIASES.get(name, name)
    body = _PATHS.get(key, _PATHS["zap"])
    filled = key.startswith("status_") or key == "dot"
    stroke = "none" if filled else color
    fill = color if filled else "none"
    return (
        f'<svg class="{escape(class_name)}" xmlns="http://www.w3.org/2000/svg" '
        f'width="{int(size)}" height="{int(size)}" viewBox="0 0 24 24" '
        f'fill="{escape(fill)}" stroke="{escape(stroke)}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'style="display:inline-block;vertical-align:-0.2em;margin-right:0.35em;flex-shrink:0;">'
        f"{body}</svg>"
    )


def icon_text(
    name: str,
    text: str,
    size: int = 18,
    color: str = "currentColor",
    as_heading: bool = False,
    level: int = 3,
) -> str:
    """Icon + text as HTML (optionally wrapped in h2/h3/h4)."""
    label = escape(strip_emoji(text))
    html = (
        f'<span class="ep-icon-label" style="display:inline-flex;align-items:center;gap:0.15rem;">'
        f"{icon(name, size=size, color=color)}<span>{label}</span></span>"
    )
    if as_heading:
        lvl = max(1, min(6, int(level)))
        return f"<h{lvl} style='display:flex;align-items:center;gap:0.25rem;margin:0 0 0.5rem 0;'>{html}</h{lvl}>"
    return html


def status_icon(kind: str = "ok", size: int = 12) -> str:
    mapping = {"ok": "status_ok", "warn": "status_warn", "error": "status_err", "offline": "status_err"}
    return icon(mapping.get(kind, "status_ok"), size=size)
