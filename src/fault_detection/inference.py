"""
Unified fault-detection inference entry point.

Prefers YOLO when weights exist; falls back to educational stubs when not.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.fault_detection.yolo.detector import Detection, YOLOFaultDetector, default_weights_path


@dataclass
class FaultDetectionResult:
    engine: str
    detections: list[Detection] = field(default_factory=list)
    is_faulty: bool = False
    summary: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine": self.engine,
            "is_faulty": self.is_faulty,
            "summary": self.summary,
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "box": d.box,
                }
                for d in self.detections
            ],
            "meta": self.meta,
        }


def detect_faults(
    image_path: str | Path,
    conf: float = 0.25,
    engine: str = "auto",
) -> FaultDetectionResult:
    """
    Run panel fault detection on an image path.

    Parameters
    ----------
    image_path :
        Local image file.
    conf :
        YOLO confidence threshold.
    engine :
        ``auto`` | ``yolo`` — auto uses YOLO if weights exist.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    use_yolo = engine in ("auto", "yolo") and (
        engine == "yolo" or default_weights_path().exists()
    )

    if use_yolo:
        det = YOLOFaultDetector(conf=conf)
        boxes = det.predict(image_path)
        is_faulty = len(boxes) > 0
        labels = ", ".join(f"{d.class_name} ({d.confidence:.0%})" for d in boxes[:5])
        summary = (
            f"Detected {len(boxes)} fault region(s): {labels}"
            if is_faulty
            else "No faults detected above confidence threshold."
        )
        return FaultDetectionResult(
            engine="yolo",
            detections=boxes,
            is_faulty=is_faulty,
            summary=summary,
            meta={"weights": str(det.weights), "conf": conf},
        )

    return FaultDetectionResult(
        engine="none",
        detections=[],
        is_faulty=False,
        summary="No fault detector available (missing YOLO weights / ultralytics).",
        meta={},
    )
