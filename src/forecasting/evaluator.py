"""Regression metrics for forecast models (MAE, RMSE, R², MAPE)."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def metrics_dict(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute standard regression metrics; ignores NaN pairs."""
    yt = np.asarray(y_true, dtype=float).ravel()
    yp = np.asarray(y_pred, dtype=float).ravel()
    mask = np.isfinite(yt) & np.isfinite(yp)
    yt, yp = yt[mask], yp[mask]
    if len(yt) == 0:
        return {"mae": float("nan"), "rmse": float("nan"), "r2": float("nan"), "mape": float("nan"), "n": 0}

    mae = float(mean_absolute_error(yt, yp))
    rmse = float(np.sqrt(mean_squared_error(yt, yp)))
    r2 = float(r2_score(yt, yp))
    denom = np.where(np.abs(yt) < 1e-9, np.nan, yt)
    mape = float(np.nanmean(np.abs((yt - yp) / denom)) * 100.0)
    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape, "n": int(len(yt))}


def evaluate_regression(
    model: Any,
    X: Any,
    y_true: Any,
) -> Mapping[str, float]:
    """Predict with ``model`` and return metrics_dict."""
    y_pred = model.predict(X)
    return metrics_dict(np.asarray(y_true), np.asarray(y_pred))
