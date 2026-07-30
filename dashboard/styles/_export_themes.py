"""One-shot helper: export theme CSS files next to this script."""
from pathlib import Path

from dashboard.styles.custom_css import DARK_CSS, LIGHT_CSS, MOBILE_CSS, _FONT_LINK

OUT = Path(__file__).resolve().parent
HEADER = f"@import url('{_FONT_LINK}');\n"

for name, css in (("theme_dark.css", DARK_CSS), ("theme_light.css", LIGHT_CSS)):
    path = OUT / name
    path.write_text(HEADER + css + "\n" + MOBILE_CSS + "\n", encoding="utf-8")
    print("wrote", path, path.stat().st_size)
