"""
Lab theory markdown for the mobile app.

The theory files use LaTeX for Streamlit/KaTeX. Flet's Markdown renders
``$inline$`` and ``$$display$$`` math too, with two differences that broke
formulas on the phone:

* ``\\[ … \\]`` / ``\\( … \\)`` delimiters are not recognised;
* inline math must be followed by whitespace or punctuation, so Kazakh
  suffixes written straight after a formula ("$25^{\\circ}\\mathrm{C}$-пен")
  showed as raw TeX. A space is inserted before such a suffix.
"""

from __future__ import annotations

import re
from pathlib import Path

CONTENT = Path(__file__).resolve().parents[1] / "content" / "labs"

_DISPLAY_BRACKET = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
_INLINE_PAREN = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
_DISPLAY_DOLLAR = re.compile(r"\$\$.*?\$\$", re.DOTALL)
_AFTER_OK = set(" \t\n.,;:!?)]")


def _space_glued_inline(text: str) -> str:
    """Pair the unescaped single $ in order; after each closing one that is
    glued to a word, insert a space."""
    out, open_math = [], False
    i = 0
    while i < len(text):
        ch = text[i]
        out.append(ch)
        if ch == "$" and (i == 0 or text[i - 1] != "\\"):
            if open_math and i + 1 < len(text) and text[i + 1] not in _AFTER_OK:
                out.append(" ")
            open_math = not open_math
        i += 1
    return "".join(out)


def to_flet_markdown(text: str) -> str:
    out = _DISPLAY_BRACKET.sub(lambda m: f"\n\n$$\n{m.group(1).strip()}\n$$\n\n", text or "")
    out = _INLINE_PAREN.sub(lambda m: f"${m.group(1).strip()}$", out)
    # Leave display blocks alone; fix inline math between them.
    parts, last = [], 0
    for m in _DISPLAY_DOLLAR.finditer(out):
        parts.append(_space_glued_inline(out[last : m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_space_glued_inline(out[last:]))
    return "".join(parts)


def theory_markdown(stem: str) -> dict[str, str]:
    """Theory of a lab in both languages, ready for Flet's Markdown."""
    out = {}
    for lang in ("en", "kk"):
        path = CONTENT / f"{stem}_{lang}.md"
        out[lang] = to_flet_markdown(path.read_text(encoding="utf-8")) if path.is_file() else ""
    return out
