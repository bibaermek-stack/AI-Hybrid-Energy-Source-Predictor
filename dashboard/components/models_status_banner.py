"""
Clear Models online / offline banner for Overview and other views.

Uses API health when available; falls back to committed metrics JSON so the UI
always explains what is offline without crashing.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from dashboard.components.status_badge import render_status_badge

_ROOT = Path(__file__).resolve().parents[2]
_METRICS = _ROOT / "artifacts" / "model_metrics.json"


def _load_metrics_snapshot() -> dict:
    if not _METRICS.is_file():
        return {}
    try:
        return json.loads(_METRICS.read_text(encoding="utf-8"))
    except Exception:
        return {}


def render_models_status_banner(
    lang: str,
    models_status: dict | None = None,
    *,
    compact: bool = False,
) -> None:
    """Show online/offline badges + paper metrics when weights are missing."""
    is_kk = lang == "kk"
    ms = models_status or {}
    solar_ok = bool(ms.get("solar"))
    wind_ok = bool(ms.get("wind"))
    forecast_ok = bool(ms.get("forecast") or solar_ok)
    any_online = solar_ok or wind_ok or forecast_ok
    all_online = solar_ok and wind_ok

    if all_online:
        if not compact:
            render_status_badge(
                "All forecast models online" if not is_kk else "Барлық болжам модельдері online",
                "ok",
            )
        return

    # Offline / partial
    if not any_online:
        st.warning(
            (
                "**Models offline** — API did not load production weights "
                "(`artifacts/solar_model.pkl`, `wind_model.pkl`, …). "
                "Start FastAPI on :8001 or place pickles under `artifacts/`. "
                "Paper metrics below remain valid from committed JSON."
            )
            if not is_kk
            else (
                "**Модельдер offline** — API салмақтарды жүктемеді "
                "(`artifacts/solar_model.pkl`, `wind_model.pkl`, …). "
                "FastAPI :8001-ді іске қосыңыз немесе pickle-дерді `artifacts/`-қа қойыңыз. "
                "Төмендегі paper метрикалар JSON-нан жарамды."
            )
        )
    else:
        st.info(
            (
                f"**Partial models** — Solar: {'OK' if solar_ok else 'offline'} · "
                f"Wind: {'OK' if wind_ok else 'offline'} · "
                f"Forecast: {'OK' if forecast_ok else 'offline'}"
            )
            if not is_kk
            else (
                f"**Жартылай модельдер** — Күн: {'OK' if solar_ok else 'offline'} · "
                f"Жел: {'OK' if wind_ok else 'offline'} · "
                f"Болжам: {'OK' if forecast_ok else 'offline'}"
            )
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_status_badge(
            "Solar RF Online" if solar_ok else "Solar RF Offline",
            "ok" if solar_ok else "err",
        )
    with c2:
        render_status_badge(
            "Wind XGB Online" if wind_ok else "Wind XGB Offline",
            "ok" if wind_ok else "err",
        )
    with c3:
        render_status_badge(
            "Forecast ready" if forecast_ok else "Forecast offline",
            "ok" if forecast_ok else "warn",
        )

    # Demo / paper metrics package (always available from git)
    snap = _load_metrics_snapshot()
    if not snap:
        return

    with st.expander(
        "Demo metrics package (committed JSON)"
        if not is_kk
        else "Demo метрика пакеті (JSON, git-те)",
        expanded=not any_online,
    ):
        sf = snap.get("solar_forecast") or {}
        yolo = snap.get("yolo11n_fault_detection") or {}
        best = (yolo.get("best") or {})
        test = (yolo.get("test_set_all") or {})
        cnn = (snap.get("cnn_improved") or {})
        st.markdown(
            (
                "| Model | Metric | Value |\n"
                "|-------|--------|------:|\n"
                f"| Solar RF | R² | **{(sf.get('random_forest') or {}).get('r2', '—')}** |\n"
                f"| Solar XGB | R² | **{(sf.get('xgboost') or {}).get('r2', '—')}** |\n"
                f"| Solar LSTM | R² | **{(sf.get('lstm') or {}).get('r2', '—')}** |\n"
                f"| YOLO best | mAP@50 | **{best.get('mAP50', '—')}** |\n"
                f"| YOLO test | mAP@50 | **{test.get('mAP50', '—')}** |\n"
                f"| ResNet50 binary probe | val acc % | **{(cnn.get('resnet50_binary') or {}).get('val_accuracy_pct', '—')}** |\n"
                f"| VGG16 binary probe | val acc % | **{(cnn.get('vgg16_binary') or {}).get('val_accuracy_pct', '—')}** |\n"
            )
            if not is_kk
            else (
                "| Модель | Метрика | Мән |\n"
                "|-------|--------|------:|\n"
                f"| Solar RF | R² | **{(sf.get('random_forest') or {}).get('r2', '—')}** |\n"
                f"| Solar XGB | R² | **{(sf.get('xgboost') or {}).get('r2', '—')}** |\n"
                f"| Solar LSTM | R² | **{(sf.get('lstm') or {}).get('r2', '—')}** |\n"
                f"| YOLO best | mAP@50 | **{best.get('mAP50', '—')}** |\n"
                f"| YOLO test | mAP@50 | **{test.get('mAP50', '—')}** |\n"
                f"| ResNet50 binary | val acc % | **{(cnn.get('resnet50_binary') or {}).get('val_accuracy_pct', '—')}** |\n"
                f"| VGG16 binary | val acc % | **{(cnn.get('vgg16_binary') or {}).get('val_accuracy_pct', '—')}** |\n"
            )
        )
        st.caption(
            "Canonical paper table: `docs/PAPER_METRICS_LOCKED.md` · "
            "Large `.pt` weights are gitignored; metrics JSON is the demo package."
            if not is_kk
            else "Paper кестесі: `docs/PAPER_METRICS_LOCKED.md` · "
            "Үлкен `.pt` git-те жоқ; demo пакет — metrics JSON."
        )
