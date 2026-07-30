"""Random Forest solar forecast model (production default)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib

from src.models.solar_model import get_solar_model as get_solar_rf_model


def load_solar_rf(artifacts_dir: str | Path = "artifacts") -> Any:
    """Load trained solar RF pickle from artifacts/."""
    path = Path(artifacts_dir) / "solar_model.pkl"
    if not path.exists():
        alt = Path(artifacts_dir) / "solar_forecast_rf.pkl"
        path = alt if alt.exists() else path
    return joblib.load(path)


__all__ = ["get_solar_rf_model", "load_solar_rf"]
