"""Standardized Streamlit button helpers."""

from __future__ import annotations

from typing import Any, Literal

import streamlit as st

ButtonType = Literal["primary", "secondary", "tertiary"]


def primary_button(
    label: str,
    *,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    use_container_width: bool = True,
) -> bool:
    """Primary action button (full width by default)."""
    return st.button(
        label,
        key=key,
        help=help,
        disabled=disabled,
        type="primary",
        use_container_width=use_container_width,
    )


def secondary_button(
    label: str,
    *,
    key: str | None = None,
    help: str | None = None,
    disabled: bool = False,
    use_container_width: bool = True,
) -> bool:
    """Secondary action button."""
    return st.button(
        label,
        key=key,
        help=help,
        disabled=disabled,
        type="secondary",
        use_container_width=use_container_width,
    )


def action_row(
    actions: list[dict[str, Any]],
) -> dict[str, bool]:
    """
    Render a row of buttons.

    Each action: ``{label, key, type?=primary|secondary, help?}``.
    Returns ``{key: clicked}``.
    """
    if not actions:
        return {}
    cols = st.columns(len(actions))
    out: dict[str, bool] = {}
    for col, act in zip(cols, actions):
        with col:
            kind = act.get("type", "secondary")
            key = str(act["key"])
            if kind == "primary":
                out[key] = primary_button(
                    act["label"],
                    key=key,
                    help=act.get("help"),
                    disabled=bool(act.get("disabled", False)),
                )
            else:
                out[key] = secondary_button(
                    act["label"],
                    key=key,
                    help=act.get("help"),
                    disabled=bool(act.get("disabled", False)),
                )
    return out
