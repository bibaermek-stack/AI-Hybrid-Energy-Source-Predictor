"""
Known Solarman inverters + local Meshy 3D model folders.

SN 2501221272 → models/inverter/
SN 2411046235 → models/inverter_2411046235/  (Meshy_AI__0722061656)
"""

from __future__ import annotations

from typing import Any

# Primary plant units used in EcoPredict demos / Turkistan site
INVERTERS: dict[str, dict[str, Any]] = {
    "2501221272": {
        "sn": "2501221272",
        "label": "Inverter2501221272",
        "model_dir": "inverter",
        "model_key": "inverter",
        "rated_kw_hint": 25,
        "notes": "Primary Meshy textured panel (texture_basecolor + normal + AO)",
    },
    "2411046235": {
        "sn": "2411046235",
        "label": "Inverter2411046235",
        "model_dir": "inverter_2411046235",
        "model_key": "inverter_2411046235",
        "rated_kw_hint": 25,
        "notes": "Second unit — Meshy_AI__0722080659 (+90° X + 180° Z)",
    },
}


def normalize_sn(sn: str | None) -> str:
    digits = "".join(c for c in str(sn or "") if c.isdigit())
    return digits


def resolve_inverter(sn: str | None = None, model_key: str | None = None) -> dict[str, Any]:
    """Return catalog entry for SN or model_key; default first inverter."""
    key = (model_key or "").strip().lower()
    if key in ("2411046235", "inverter_2411046235", "inverter2", "second"):
        return dict(INVERTERS["2411046235"])
    if key in ("2501221272", "inverter", "inverter_2501221272", "first", "primary"):
        return dict(INVERTERS["2501221272"])

    sn_n = normalize_sn(sn)
    if sn_n in INVERTERS:
        return dict(INVERTERS[sn_n])
    # partial match
    for k, v in INVERTERS.items():
        if k in sn_n or sn_n in k:
            return dict(v)
    return dict(INVERTERS["2501221272"])


def list_inverter_choices() -> list[dict[str, str]]:
    return [
        {"sn": v["sn"], "label": v["label"], "model_key": v["model_key"]}
        for v in INVERTERS.values()
    ]
