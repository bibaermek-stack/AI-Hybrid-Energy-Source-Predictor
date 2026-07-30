"""YOLOv11 solar-panel fault detectors."""

from src.fault_detection.yolo.detector import YOLOFaultDetector, default_weights_path

__all__ = ["YOLOFaultDetector", "default_weights_path"]
