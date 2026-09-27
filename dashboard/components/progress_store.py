"""
The labs progress kept in the browser (localStorage).

Streamlit's session_state lives as long as the browser tab's connection: a
reload, a closed tab or the next day's visit started from zero, and a student
lost the labs they had passed. The hidden component here reads the browser's
copy once per page load (merged into the session, then one rerun) and writes
the session's progress back on every run.

Use ``slot = progress_slot()`` first on the page and ``sync_progress(slot, …)``
last: the component then saves what this run changed and never moves (a
component that changes position is remounted).
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.education.progress import ProgressTracker

STORAGE_KEY = "ecopredict.labs_progress.v1"
SLOT_KEY = "ep_progress_store"
RESTORED = "_ep_progress_restored"

_DIR = Path(__file__).resolve().parent / "progress_store_frontend"
_component = components.declare_component("ecopredict_progress_store", path=str(_DIR))


def progress_slot():
    """An invisible container at a fixed place on the page."""
    slot = st.container(key=SLOT_KEY)
    with slot:
        st.html(f"<style>.st-key-{SLOT_KEY}{{display:none}}</style>")
    return slot


def sync_progress(slot, progress: ProgressTracker) -> None:
    """Load the browser's progress once, then save the session's on every run."""
    restored = bool(st.session_state.get(RESTORED))
    with slot:
        value = _component(
            storage_key=STORAGE_KEY,
            save=json.dumps(progress.data, ensure_ascii=False) if restored else None,
            key=f"{SLOT_KEY}_component",
            default=None,
        )
    if restored or not isinstance(value, dict):
        return
    st.session_state[RESTORED] = True
    if progress.merge(value.get("stored")):
        st.rerun()  # redraw with the restored progress
