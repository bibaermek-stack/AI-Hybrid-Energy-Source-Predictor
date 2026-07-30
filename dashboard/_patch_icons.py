"""Replace remaining markdown h3/h4 text headers with SVG icon_text."""
from __future__ import annotations

import re
from pathlib import Path

from dashboard.components.icons import _EMOJI_RE

ROOT = Path(__file__).resolve().parent
VIEWS = ROOT / "views"

ICON_MAP = {
    "solar_header": "sun",
    "wind_header": "wind",
    "opt_header": "gauge",
    "opt_dispatch": "sliders",
    "advisor_header": "bot",
    "tab_predict": "predict",
    "tab_forecast": "forecast",
    "tab_solarman": "solarman",
    "tab_diagnostics": "diagnostics",
    "tab_training": "training",
    "tab_3d_model": "model3d",
}

PAT = re.compile(
    r"""st\.markdown\(\s*f?['\"]<h([34])>\{texts\[['\"]([a-zA-Z0-9_]+)['\"]\]\}</h[34]>['\"]\s*,\s*unsafe_allow_html\s*=\s*True\s*\)"""
)


def main() -> None:
    for p in VIEWS.glob("*.py"):
        if p.name.startswith("_") or p.name == "__init__.py":
            continue
        t = p.read_text(encoding="utf-8")
        if "from dashboard.components.icons import" not in t:
            t = t.replace(
                "import streamlit as st\n",
                "import streamlit as st\n"
                "from dashboard.components.icons import icon, icon_text, strip_emoji\n",
                1,
            )

        def repl(m: re.Match) -> str:
            level = m.group(1)
            key = m.group(2)
            ic = ICON_MAP.get(key, "zap")
            return (
                f"st.markdown(icon_text('{ic}', texts['{key}'], size=20, "
                f"as_heading=True, level={level}), unsafe_allow_html=True)"
            )

        t2, n = PAT.subn(repl, t)
        t2 = _EMOJI_RE.sub("", t2)
        p.write_text(t2, encoding="utf-8")
        print(f"{p.name}: header_replacements={n}")

    # Solarman device header
    sp = VIEWS / "solarman.py"
    t = sp.read_text(encoding="utf-8")
    t = re.sub(
        r'st\.markdown\(\s*\n\s*"###\s*Device Data[^\"]*"\s*\n\s*if lang == "en"\s*\n\s*else\s*"[^"]*"\s*\n\s*\)',
        'st.markdown(icon_text("inverter", "Device Data — Inverter2501221272", size=22, as_heading=True, level=3), unsafe_allow_html=True)',
        t,
        count=1,
    )
    # credentials expander label
    t = t.replace(
        '"🔑 Solarman API credentials / API кілттері"',
        'icon_text("key", "Solarman API credentials / API кілттері", size=16)',
    )
    # may break expander if not string - fix carefully
    if 'st.expander(\n        icon_text("key"' in t or "st.expander(\n        icon_text('key'" in t:
        pass
    elif 'icon_text("key"' in t and "st.expander" in t:
        # expander needs plain string - use strip only
        t = t.replace(
            'icon_text("key", "Solarman API credentials / API кілттері", size=16)',
            '"Solarman API credentials / API кілттері"',
        )
    sp.write_text(t, encoding="utf-8")
    print("solarman header patched")

    # diagnostics main headers
    dp = VIEWS / "diagnostics.py"
    t = dp.read_text(encoding="utf-8")
    t = re.sub(
        r"st\.markdown\(f'<h3>\{\"[^\"]*System Diagnostics[^\"]*\" if lang == \"en\" else \"[^\"]*\"\}</h3>', unsafe_allow_html=True\)",
        'st.markdown(icon_text("diagnostics", "System Diagnostics & Faults" if lang == "en" else "Күн станциясының ақаулықтарын диагностикалау", size=22, as_heading=True, level=3), unsafe_allow_html=True)',
        t,
        count=1,
    )
    t = re.sub(
        r"st\.markdown\(f'<h4>\{\"[^\"]*Telemetry-Based[^\"]*\" if lang == \"en\" else \"[^\"]*\"\}</h4>', unsafe_allow_html=True\)",
        'st.markdown(icon_text("analysis", "Telemetry-Based Diagnostics" if lang == "en" else "Телеметрия негізіндегі диагностика", size=18, as_heading=True, level=4), unsafe_allow_html=True)',
        t,
        count=1,
    )
    # severity labels without emoji
    t = t.replace('"  Medium', '"Medium').replace('"  High', '"High').replace('"  Critical', '"Critical')
    t = t.replace('"  Warning', '"Warning').replace("'  Medium", "'Medium")
    dp.write_text(_EMOJI_RE.sub("", t), encoding="utf-8")
    print("diagnostics patched")


if __name__ == "__main__":
    main()
