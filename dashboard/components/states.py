"""
Loading, empty, and error UI states for Streamlit views.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import streamlit as st

from dashboard.components.ui_kit import _html


@contextmanager
def loading_state(message: str = "Loading…") -> Iterator[None]:
    """Context manager wrapping ``st.spinner``."""
    with st.spinner(message):
        yield


def empty_state(
    title: str,
    description: str | None = None,
    *,
    icon: str = "◇",
) -> None:
    """Centered empty-state card when no data is available."""
    desc = f'<p class="ep-empty-desc">{_escape(description)}</p>' if description else ""
    _html(
        f"""
        <div class="ep-empty-state">
          <div class="ep-empty-icon">{_escape(icon)}</div>
          <div class="ep-empty-title">{_escape(title)}</div>
          {desc}
        </div>
        """
    )


def error_state(
    message: str,
    *,
    detail: str | Exception | None = None,
    lang: str = "en",
) -> None:
    """
    User-visible error block. Shows ``detail`` traceback when provided.
    """
    st.error(message)
    if detail is not None:
        with st.expander("Details" if lang != "kk" else "Толығырақ"):
            if isinstance(detail, BaseException):
                st.exception(detail)
            else:
                st.code(str(detail))


def run_safe(
    fn: Callable[[], Any],
    *,
    error_message: str = "An unexpected error occurred.",
    lang: str = "en",
) -> Any | None:
    """Execute ``fn``; on failure render ``error_state`` and return None."""
    try:
        return fn()
    except Exception as e:
        error_state(error_message, detail=e, lang=lang)
        return None


def _escape(s: str) -> str:
    from html import escape

    return escape(s or "")
