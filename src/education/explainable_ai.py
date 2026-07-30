"""
Explainable AI helpers for EcoPredict educational module.

Provides:
  - Tree model feature importance (RandomForest / XGBoost style)
  - Simple sensitivity (what-if) deltas
  - Rule-based narrative in EN/KK

Does not require SHAP (optional if installed).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default solar feature names used by EcoPredict solar_model.pkl
SOLAR_FEATURES = [
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour",
    "day",
    "month",
]

ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts"


def _load_solar_model():
    try:
        import joblib

        path = ARTIFACT_PATH / "solar_model.pkl"
        if not path.is_file():
            return None
        return joblib.load(path)
    except Exception as e:
        logger.warning("Could not load solar_model.pkl: %s", e)
        return None


def feature_importance_table(model=None, feature_names: Sequence[str] | None = None) -> pd.DataFrame:
    """
    Return DataFrame with columns feature, importance (normalized 0–1).
    """
    feature_names = list(feature_names or SOLAR_FEATURES)
    model = model or _load_solar_model()
    if model is None:
        # Educational fallback ranks
        imp = np.array([0.45, 0.12, 0.18, 0.15, 0.05, 0.05], dtype=float)
        imp = imp / imp.sum()
        return pd.DataFrame({"feature": feature_names, "importance": imp})

    if hasattr(model, "feature_importances_"):
        imp = np.asarray(model.feature_importances_, dtype=float)
        if len(imp) != len(feature_names):
            # pad / trim
            n = min(len(imp), len(feature_names))
            feature_names = feature_names[:n]
            imp = imp[:n]
        if imp.sum() > 0:
            imp = imp / imp.sum()
        return (
            pd.DataFrame({"feature": feature_names, "importance": imp})
            .sort_values("importance", ascending=False)
            .reset_index(drop=True)
        )

    # Generic placeholder
    imp = np.ones(len(feature_names)) / len(feature_names)
    return pd.DataFrame({"feature": feature_names, "importance": imp})


def predict_solar(
    irradiation: float,
    ambient_temp: float,
    module_temp: float,
    hour: int,
    day: int = 15,
    month: int = 6,
    model=None,
) -> float:
    """Point prediction with solar RF (kW). Clips negatives."""
    model = model or _load_solar_model()
    row = {
        "IRRADIATION": float(irradiation),
        "AMBIENT_TEMPERATURE": float(ambient_temp),
        "MODULE_TEMPERATURE": float(module_temp),
        "hour": int(hour),
        "day": int(day),
        "month": int(month),
    }
    X = pd.DataFrame([row])
    if model is None:
        # Physics-inspired toy model for offline teaching
        hour_factor = max(0.0, np.sin((hour - 6) * np.pi / 14)) if 6 <= hour <= 18 else 0.0
        temp_pen = max(0.0, 1.0 - 0.004 * max(0.0, module_temp - 25.0))
        return float(max(0.0, irradiation / 1000.0 * 25.0 * hour_factor * temp_pen))
    try:
        y = float(model.predict(X)[0])
    except Exception:
        y = float(model.predict(X.values)[0])
    return float(max(0.0, y))


def sensitivity_analysis(
    base: dict[str, float],
    deltas: dict[str, float] | None = None,
    model=None,
) -> pd.DataFrame:
    """
    One-at-a-time sensitivity: change each feature, report Δ prediction.

    base keys: IRRADIATION, AMBIENT_TEMPERATURE, MODULE_TEMPERATURE, hour, day, month
    """
    deltas = deltas or {
        "IRRADIATION": 100.0,
        "AMBIENT_TEMPERATURE": 5.0,
        "MODULE_TEMPERATURE": 5.0,
        "hour": 1.0,
        "day": 0.0,
        "month": 0.0,
    }
    base_y = predict_solar(
        base["IRRADIATION"],
        base["AMBIENT_TEMPERATURE"],
        base["MODULE_TEMPERATURE"],
        int(base["hour"]),
        int(base.get("day", 15)),
        int(base.get("month", 6)),
        model=model,
    )
    rows = []
    for feat, d in deltas.items():
        if abs(d) < 1e-12:
            continue
        b2 = dict(base)
        b2[feat] = float(b2[feat]) + float(d)
        if feat == "hour":
            b2[feat] = float(int(b2[feat]) % 24)
        y2 = predict_solar(
            b2["IRRADIATION"],
            b2["AMBIENT_TEMPERATURE"],
            b2["MODULE_TEMPERATURE"],
            int(b2["hour"]),
            int(b2.get("day", 15)),
            int(b2.get("month", 6)),
            model=model,
        )
        rows.append(
            {
                "feature": feat,
                "delta_input": d,
                "base_pred_kw": base_y,
                "new_pred_kw": y2,
                "delta_pred_kw": y2 - base_y,
            }
        )
    return pd.DataFrame(rows).sort_values("delta_pred_kw", key=lambda s: s.abs(), ascending=False)


def explain_prediction_narrative(
    base: dict[str, float],
    pred_kw: float | None = None,
    lang: str = "en",
    model=None,
) -> str:
    """
    Human-readable rule-based explanation (teaching style).
    """
    lang = "kk" if lang == "kk" else "en"
    if pred_kw is None:
        pred_kw = predict_solar(
            base["IRRADIATION"],
            base["AMBIENT_TEMPERATURE"],
            base["MODULE_TEMPERATURE"],
            int(base["hour"]),
            int(base.get("day", 15)),
            int(base.get("month", 6)),
            model=model,
        )
    irr = base["IRRADIATION"]
    tmod = base["MODULE_TEMPERATURE"]
    hour = int(base["hour"])

    drivers = []
    if irr >= 700:
        drivers.append(
            "жоғары сәуле (күшті генерация драйвері)"
            if lang == "kk"
            else "high irradiance (strong generation driver)"
        )
    elif irr < 200:
        drivers.append(
            "төмен сәуле (бұлт/түн әсері)"
            if lang == "kk"
            else "low irradiance (cloud/night effect)"
        )
    else:
        drivers.append(
            "орташа сәуле" if lang == "kk" else "moderate irradiance"
        )

    if tmod >= 45:
        drivers.append(
            "ыстық панель (тиімділік аздап төмендейді)"
            if lang == "kk"
            else "hot modules (slight efficiency penalty)"
        )
    if 10 <= hour <= 15:
        drivers.append(
            "түскі сағат (күн биік)" if lang == "kk" else "midday hours (high sun angle)"
        )
    elif hour < 7 or hour > 19:
        drivers.append(
            "түн/кеш (күн төмен)" if lang == "kk" else "night/late (low sun)"
        )

    imp = feature_importance_table(model=model)
    top = imp.iloc[0]["feature"] if len(imp) else "IRRADIATION"

    if lang == "kk":
        return (
            f"**Болжам:** {pred_kw:.2f} кВт\n\n"
            f"**Негізгі драйверлер:** {', '.join(drivers)}.\n\n"
            f"**Модель бойынша ең маңызды белгі (жалпы):** `{top}`.\n\n"
            "Бұл түсіндірме feature importance + физикалық ережелерге негізделген "
            "(толық SHAP міндетті емес). Оператор әрқашан live телеметриямен салыстыруы керек."
        )
    return (
        f"**Prediction:** {pred_kw:.2f} kW\n\n"
        f"**Main drivers:** {', '.join(drivers)}.\n\n"
        f"**Top global feature (model importance):** `{top}`.\n\n"
        "This explanation combines tree importance with simple PV rules "
        "(full SHAP optional). Always cross-check with live inverter telemetry."
    )


def try_shap_values(
    X: pd.DataFrame,
    model=None,
) -> pd.DataFrame | None:
    """Optional SHAP if package installed; returns mean |shap| per feature or None."""
    model = model or _load_solar_model()
    if model is None:
        return None
    try:
        import shap  # type: ignore
    except ImportError:
        return None
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        arr = np.abs(np.asarray(sv)).mean(axis=0)
        names = list(X.columns)
        return (
            pd.DataFrame({"feature": names, "mean_abs_shap": arr})
            .sort_values("mean_abs_shap", ascending=False)
            .reset_index(drop=True)
        )
    except Exception as e:
        logger.warning("SHAP failed: %s", e)
        return None
