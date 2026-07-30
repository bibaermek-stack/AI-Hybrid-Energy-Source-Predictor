"""
Data preprocessing helpers for solar/wind forecasting.

Wraps cleaned plant data and feature-frame construction used by the API
and educational labs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

DEFAULT_FEATURE_COLS = [
    "IRRADIATION",
    "AMBIENT_TEMPERATURE",
    "MODULE_TEMPERATURE",
    "hour",
    "day",
    "month",
]
TARGET_COL = "AC_POWER"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_solar_features(
    path: str | Path | None = None,
) -> pd.DataFrame:
    """
    Load processed solar CSV (build_features or solar_cleaned).

    Returns a DataFrame with at least IRRADIATION / temperatures / AC_POWER
    when available.
    """
    root = project_root()
    candidates = []
    if path is not None:
        candidates.append(Path(path))
    candidates.extend(
        [
            root / "data" / "processed" / "build_features.csv",
            root / "data" / "processed" / "solar_cleaned.csv",
            root / "data" / "sample" / "solar_sample.csv",
        ]
    )
    for p in candidates:
        if p.exists():
            df = pd.read_csv(p)
            if "DATE_TIME" in df.columns:
                df["DATE_TIME"] = pd.to_datetime(df["DATE_TIME"], errors="coerce")
            return df
    raise FileNotFoundError(
        "No processed solar features found. Run data pipeline or place CSV under data/processed/."
    )


def ensure_time_features(df: pd.DataFrame, dt_col: str = "DATE_TIME") -> pd.DataFrame:
    """Add hour / day / month if a datetime column exists."""
    out = df.copy()
    if dt_col in out.columns:
        ts = pd.to_datetime(out[dt_col], errors="coerce")
        if "hour" not in out.columns:
            out["hour"] = ts.dt.hour
        if "day" not in out.columns:
            out["day"] = ts.dt.day
        if "month" not in out.columns:
            out["month"] = ts.dt.month
    return out


def prepare_forecast_frame(
    df: pd.DataFrame,
    feature_cols: Sequence[str] | None = None,
    target_col: str = TARGET_COL,
) -> tuple[pd.DataFrame, pd.Series | None]:
    """
    Build X (and y if target present) for classical ML models.
    """
    feature_cols = list(feature_cols or DEFAULT_FEATURE_COLS)
    frame = ensure_time_features(df)
    missing = [c for c in feature_cols if c not in frame.columns]
    if missing:
        raise ValueError(f"Missing feature columns: {missing}")
    X = frame[feature_cols].astype(float)
    y = frame[target_col].astype(float) if target_col in frame.columns else None
    return X, y


def sequences_from_frame(
    df: pd.DataFrame,
    feature_cols: Sequence[str] | None = None,
    window: int = 24,
) -> np.ndarray:
    """
    Build (N, window, F) sequences for batch forecast APIs.
    """
    feature_cols = list(feature_cols or DEFAULT_FEATURE_COLS)
    frame = ensure_time_features(df)
    arr = frame[list(feature_cols)].astype(float).to_numpy()
    if len(arr) < window:
        raise ValueError(f"Need at least {window} rows, got {len(arr)}")
    seqs = []
    for i in range(window - 1, len(arr)):
        seqs.append(arr[i - window + 1 : i + 1])
    return np.asarray(seqs, dtype=float)
