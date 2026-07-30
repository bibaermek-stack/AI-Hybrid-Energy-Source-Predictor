"""XGBoost wind model factory / loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from src.models.wind_model import get_wind_model


def load_wind_model(artifacts_dir: str | Path = "artifacts") -> Any:
    """Load trained wind model pickle."""
    path = Path(artifacts_dir) / "wind_model.pkl"
    return joblib.load(path)


__all__ = ["get_wind_model", "load_wind_model"]
