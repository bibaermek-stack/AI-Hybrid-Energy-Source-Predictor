"""
Optional LSTM forecast model.

Not loaded in production (Railway / TF-free path). Kept for offline research
and notebooks that still reference LSTM artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def get_lstm_builder():
    """Return LSTM architecture builder from legacy module (may require TF)."""
    from src.models.lstm_model import get_lstm_model  # type: ignore

    return get_lstm_model


def load_lstm_weights(artifacts_dir: str | Path = "artifacts") -> Any:
    """
    Load LSTM Keras model if TensorFlow is installed.

    Raises ImportError when TF is unavailable (expected on production).
    """
    try:
        from tensorflow import keras  # type: ignore
    except ImportError as e:
        raise ImportError(
            "TensorFlow is not installed. Production uses RF forecast instead."
        ) from e

    root = Path(artifacts_dir)
    for name in (
        "solar_forecast_lstm_best.keras",
        "solar_forecast_lstm.h5",
        "solar_lstm_model.h5",
    ):
        p = root / name
        if p.exists():
            return keras.models.load_model(p)
    raise FileNotFoundError(f"No LSTM artifact under {root}")


__all__ = ["get_lstm_builder", "load_lstm_weights"]
