"""
Render markdown with Streamlit KaTeX math support.

Streamlit natively renders KaTeX for:
  - ``$inline$`` and ``$$display$$`` inside ``st.markdown``
  - ``st.latex(r"...")`` for pure TeX blocks

This helper also converts classic LaTeX delimiters used in theory files:
  ``\\[ ... \\]`` → ``$$ ... $$``
  ``\\( ... \\)`` → ``$ ... $``
"""

from __future__ import annotations

import re
from typing import Any

import streamlit as st

_DISPLAY_BRACKET = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
_INLINE_PAREN = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
# Some notes use single-line \[ ... \] without newlines
_DISPLAY_DOLLAR_SPACES = re.compile(r"(?<!\$)\$\$(.+?)\$\$(?!\$)", re.DOTALL)


def latex_to_streamlit_md(text: str) -> str:
    """Normalize LaTeX delimiters to Streamlit/KaTeX-friendly ``$`` / ``$$``."""
    if not text:
        return ""
    out = str(text)

    def _disp(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        return f"\n\n$$\n{body}\n$$\n\n"

    def _inl(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        return f"${body}$"

    out = _DISPLAY_BRACKET.sub(_disp, out)
    out = _INLINE_PAREN.sub(_inl, out)
    return out


def render_markdown_math(text: str, *, unsafe_allow_html: bool = False) -> None:
    """``st.markdown`` with KaTeX delimiter normalization."""
    st.markdown(latex_to_streamlit_md(text), unsafe_allow_html=unsafe_allow_html)


def render_latex(expr: str) -> None:
    """Display a pure TeX expression via Streamlit's KaTeX (``st.latex``)."""
    expr = (expr or "").strip()
    if not expr:
        return
    # Strip accidental $$ wrappers
    if expr.startswith("$$") and expr.endswith("$$"):
        expr = expr[2:-2].strip()
    st.latex(expr)


def render_section_math(
    body: str = "",
    *,
    latex: str | None = None,
    items: list[str] | None = None,
) -> None:
    """
    Render a lesson/lab section that may mix prose, bullet tasks, and formulas.

    - ``latex``: pure TeX block (preferred for formula sections)
    - ``body``: markdown + ``$`` / ``$$`` / ``\\(`` / ``\\[``
    - ``items``: bullet lines (each may contain inline math)
    """
    if latex:
        render_latex(latex)
    if body:
        render_markdown_math(body)
    if items:
        for item in items:
            render_markdown_math(f"- {item}")


def katex_help_caption(lang: str = "en") -> None:
    """Short note for students about math notation in tasks."""
    if lang == "kk":
        st.caption(
            "Формулалар KaTeX арқылы көрсетіледі: "
            "жол ішінде `$E=mc^2$`, бөлек жолда `$$P=\\eta A G$$`."
        )
    else:
        st.caption(
            "Formulas render with KaTeX: "
            "inline `$E=mc^2$`, display `$$P=\\eta A G$$`."
        )


# Re-export for type checkers / tests
__all__ = [
    "latex_to_streamlit_md",
    "render_markdown_math",
    "render_latex",
    "render_section_math",
    "katex_help_caption",
]
