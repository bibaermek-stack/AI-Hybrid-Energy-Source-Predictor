"""
Fault detection package — YOLO panel defects + CNN clean/dirty classifiers.
"""

from src.fault_detection.inference import FaultDetectionResult, detect_faults

__all__ = ["detect_faults", "FaultDetectionResult"]
