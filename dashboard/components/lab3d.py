"""
The 3D inverter lab (static/lab3d/) as a Streamlit component.

Streamlit serves the component folder itself, from the page's own origin and
with proper content types, so the viewer, three.js and the meshes load on
Railway exactly as locally — the earlier viewer linked out to a second static
server and to unpkg.com, and showed nothing when either was unreachable.

The viewer sends two events back (``check`` and ``test_submit``); Python grades
them here and passes the test result back in the component arguments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

_DIR = Path(__file__).resolve().parents[2] / "static" / "lab3d"
_component = components.declare_component("ecopredict_lab3d", path=str(_DIR))


def lab3d_viewer(
    *,
    lang: str,
    test: dict[str, Any] | None = None,
    test_result: dict[str, Any] | None = None,
    height: int = 640,
    key: str = "lab3d",
) -> dict[str, Any] | None:
    """Render the viewer; return a new event from it, once, or None."""
    value = _component(
        lang="kk" if lang == "kk" else "en",
        test=test,
        test_result=test_result,
        height=height,
        key=key,
        default=None,
    )
    if not isinstance(value, dict):
        return None
    seen = f"{key}__last_nonce"
    if st.session_state.get(seen) == value.get("nonce"):
        return None  # the same value comes back on every rerun
    st.session_state[seen] = value.get("nonce")
    return value
