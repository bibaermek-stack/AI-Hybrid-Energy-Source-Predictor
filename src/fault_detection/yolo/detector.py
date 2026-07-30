"""
YOLOv11 wrapper for solar panel fault detection.

Weights: yolo_fault_detection/runs/runs/detect/train/weights/best.pt
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def default_weights_path() -> Path:
    candidates = [
        PROJECT_ROOT
        / "yolo_fault_detection"
        / "runs"
        / "runs"
        / "detect"
        / "train"
        / "weights"
        / "best.pt",
        PROJECT_ROOT / "artifacts" / "best.pt",
        PROJECT_ROOT / "yolo_fault_detection" / "yolo11n.pt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]


@dataclass
class Detection:
    class_name: str
    confidence: float
    box: list[float] = field(default_factory=list)


class YOLOFaultDetector:
    """Lazy-loaded Ultralytics YOLO detector."""

    def __init__(self, weights: str | Path | None = None, conf: float = 0.25):
        self.weights = Path(weights) if weights else default_weights_path()
        self.conf = conf
        self._model = None

    def _load(self) -> Any:
        if self._model is None:
            from ultralytics import YOLO

            if not self.weights.exists():
                raise FileNotFoundError(f"YOLO weights not found: {self.weights}")
            self._model = YOLO(str(self.weights))
        return self._model

    def predict(self, image_path: str | Path) -> list[Detection]:
        model = self._load()
        results = model.predict(source=str(image_path), conf=self.conf, verbose=False)
        detections: list[Detection] = []
        for r in results:
            names = r.names or {}
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls.item()) if box.cls is not None else -1
                conf = float(box.conf.item()) if box.conf is not None else 0.0
                xyxy = box.xyxy[0].tolist() if box.xyxy is not None else []
                detections.append(
                    Detection(
                        class_name=str(names.get(cls_id, cls_id)),
                        confidence=conf,
                        box=[float(x) for x in xyxy],
                    )
                )
        return detections
