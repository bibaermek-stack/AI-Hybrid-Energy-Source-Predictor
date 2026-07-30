"""
CNN artifact helpers for clean/dirty and ResNet/VGG panel models.

Production Railway path avoids loading heavy TF models at import time.
These loaders are optional and fail gracefully without TensorFlow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ARTIFACTS = PROJECT_ROOT / "artifacts"

CNN_ARTIFACTS = {
    "clean_dirty": "clean_dirty_model.h5",
    "resnet50": "resnet50_solar_model.h5",
    "vgg16": "vgg16_solar_model.h5",
    "solar_dust": "solar_dust_model.h5",
}


def list_cnn_artifacts() -> dict[str, bool]:
    return {k: (ARTIFACTS / v).exists() for k, v in CNN_ARTIFACTS.items()}


class CleanDirtyClassifier:
    """Binary clean vs dirty panel classifier (.h5)."""

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path) if model_path else ARTIFACTS / CNN_ARTIFACTS["clean_dirty"]
        self._model = None

    def available(self) -> bool:
        return self.model_path.exists()

    def load(self) -> Any:
        try:
            from tensorflow import keras  # type: ignore
        except ImportError as e:
            raise ImportError(
                "TensorFlow required for CNN classifiers. Use YOLO path in production."
            ) from e
        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)
        if self._model is None:
            self._model = keras.models.load_model(self.model_path)
        return self._model

    def predict_proba(self, image_array: Any) -> float:
        """
        Return probability of 'dirty' class for a preprocessed batch (N,H,W,C).
        """
        model = self.load()
        preds = model.predict(image_array, verbose=0)
        arr = preds.ravel()
        return float(arr[0]) if len(arr) else 0.0
