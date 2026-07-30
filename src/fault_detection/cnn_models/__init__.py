"""CNN clean/dirty and multi-class panel classifiers (artifact loaders)."""

from src.fault_detection.cnn_models.classifiers import (
    CleanDirtyClassifier,
    list_cnn_artifacts,
)

__all__ = ["CleanDirtyClassifier", "list_cnn_artifacts"]
