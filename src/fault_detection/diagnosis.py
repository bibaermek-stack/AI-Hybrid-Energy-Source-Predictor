"""
Panel fault diagnosis that says how sure it is.

On the real photos in the repository (see docs/FAULT_DIAGNOSIS.md) the
YOLO11n detector alone names the right class for 78% of held-out photos, and
no single model trained on this data does much better. Two different models
that agree, each confidently, are right about 98% of the time. So the answer
is "confirmed" only then, "likely" when the two agree with less confidence and
"uncertain" when they disagree, where the user is asked to retake the photo
or check by hand rather than handed a guess dressed as a verdict. Before
that, a photo that is too dark, blurred, overexposed or tiny is sent back,
and an image that is not a solar panel is refused.

Steps for one image:
1. quality gate: sharpness (variance of the Laplacian), brightness, clipped
   highlights, size;
2. the YOLO26s-cls backbone gives a 512-d embedding (one forward pass);
3. panel gate: logistic regression on the embedding, "is this a panel?";
4. fault classifier: logistic regression on the embedding, six classes;
5. the YOLO11n detector: best box confidence per class;
6. decide().

The two heads are plain numbers in yolo_fault_detection/classifier/
fault_head.json, fitted by scripts/fault_detection/train_head.py on the
embeddings of the exact backbone file next to it (its sha256 is checked).
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any, Optional, Sequence

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLASSIFIER_DIR = PROJECT_ROOT / "yolo_fault_detection" / "classifier"
HEAD_PATH = CLASSIFIER_DIR / "fault_head.json"

CLASSES = ("Bird", "Clean", "Dust", "Electrical", "Physical", "Snow")
# what each finding asks of the owner
SEVERITY = {
    "Clean": "none",
    "Dust": "cleaning",
    "Bird": "cleaning",
    "Snow": "cleaning",
    "Electrical": "repair",
    "Physical": "repair",
}

DEFAULT_QUALITY = {
    "min_side": 64,  # px
    "min_sharpness": 30.0,  # variance of the Laplacian at <= 512 px
    "min_brightness": 20.0,  # mean grey level
    "max_clipped": 0.35,  # share of pixels at >= 250
}
DEFAULT_DECISION = {
    "panel_min": 0.5,
    "classifier_min": 0.8,
    "detector_min": 0.6,
    "classifier_weight": 0.7,
}


# ---- image quality -----------------------------------------------------------
def quality_metrics(img_bgr: np.ndarray) -> dict[str, Any]:
    """Measured on a copy no larger than 512 px so phone photos and crops compare."""
    import cv2

    h, w = img_bgr.shape[:2]
    scale = min(1.0, 512.0 / max(h, w))
    small = (
        img_bgr
        if scale >= 1.0
        else cv2.resize(img_bgr, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
    )
    grey = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    return {
        "width": int(w),
        "height": int(h),
        "sharpness": round(float(cv2.Laplacian(grey, cv2.CV_64F).var()), 1),
        "brightness": round(float(grey.mean()), 1),
        "clipped": round(float((grey >= 250).mean()), 3),
    }


def quality_issues(m: dict[str, Any], cfg: Optional[dict[str, float]] = None) -> list[str]:
    cfg = {**DEFAULT_QUALITY, **(cfg or {})}
    issues = []
    if min(m["width"], m["height"]) < cfg["min_side"]:
        issues.append("too_small")
    if m["brightness"] < cfg["min_brightness"]:
        issues.append("too_dark")
    if m["clipped"] > cfg["max_clipped"]:
        issues.append("overexposed")
    # a dark or tiny image is also flat; name the cause, not the symptom
    if m["sharpness"] < cfg["min_sharpness"] and not issues:
        issues.append("blurry")
    return issues


# ---- heads -------------------------------------------------------------------
class LinearHead:
    """StandardScaler + logistic regression, from the numbers scikit-learn fitted."""

    def __init__(self, spec: dict[str, Any]):
        self.mean = np.asarray(spec["mean"], dtype=np.float64)
        self.scale = np.asarray(spec["scale"], dtype=np.float64)
        self.coef = np.atleast_2d(np.asarray(spec["coef"], dtype=np.float64))
        self.intercept = np.atleast_1d(np.asarray(spec["intercept"], dtype=np.float64))
        self.classes = list(spec.get("classes", []))

    def proba(self, x: np.ndarray) -> np.ndarray:
        z = ((np.atleast_2d(x) - self.mean) / self.scale) @ self.coef.T + self.intercept
        if self.coef.shape[0] == 1:  # binary: probability of the positive class
            return 1.0 / (1.0 + np.exp(-z[:, 0]))
        z = z - z.max(axis=1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=1, keepdims=True)


# ---- decision ----------------------------------------------------------------
def detector_scores(detections: Sequence[Any]) -> np.ndarray:
    """Best confidence per class over the detector's boxes."""
    s = np.zeros(len(CLASSES))
    for d in detections:
        name = getattr(d, "class_name", None) or (
            d.get("class_name") if isinstance(d, dict) else None
        )
        conf = getattr(d, "confidence", None)
        if conf is None and isinstance(d, dict):
            conf = d.get("confidence")
        if name in CLASSES:
            k = CLASSES.index(name)
            s[k] = max(s[k], float(conf or 0.0))
    return s


def _top(p: np.ndarray, n: int = 3) -> list[dict[str, Any]]:
    order = np.argsort(-p)[:n]
    return [{"label": CLASSES[i], "p": round(float(p[i]), 4)} for i in order if p[i] > 0]


def decide(
    classifier_p: Optional[np.ndarray],
    det_scores: Optional[np.ndarray],
    panel_p: Optional[float],
    issues: Sequence[str],
    cfg: Optional[dict[str, float]] = None,
    expected: Optional[dict[str, float]] = None,
) -> dict[str, Any]:
    """
    status: retake | not_panel | confirmed | likely | uncertain.

    confirmed — both models name the same class, the classifier with
    p >= classifier_min and the detector with a box of confidence >=
    detector_min; likely — they agree, less confidently; uncertain — they
    disagree, or only one model answered.
    """
    cfg = {**DEFAULT_DECISION, **(cfg or {})}
    expected = expected or {}
    out: dict[str, Any] = {
        "status": "",
        "label": None,
        "confidence": None,
        "severity": None,
        "candidates": [],
        "agree": None,
        "models": {},
        "panel_p": None if panel_p is None else round(float(panel_p), 4),
        "issues": list(issues),
        "expected_accuracy": None,
    }
    if issues:
        out["status"] = "retake"
        return out
    if panel_p is not None and panel_p < cfg["panel_min"]:
        out["status"] = "not_panel"
        return out

    det = np.zeros(len(CLASSES)) if det_scores is None else np.asarray(det_scores, dtype=float)
    has_det = bool(det.max() > 0)
    if classifier_p is None and not has_det:
        out["status"] = "uncertain"
        return out
    if classifier_p is None:  # the backbone is missing: the detector alone
        fused = det / det.sum()
    elif has_det:
        w = cfg["classifier_weight"]
        fused = w * np.asarray(classifier_p) + (1 - w) * det / det.sum()
    else:
        fused = np.asarray(classifier_p, dtype=float)

    clf_k = None if classifier_p is None else int(np.argmax(classifier_p))
    det_k = int(np.argmax(det)) if has_det else None
    if clf_k is not None:
        out["models"]["classifier"] = {
            "label": CLASSES[clf_k],
            "p": round(float(classifier_p[clf_k]), 4),
        }
    if det_k is not None:
        out["models"]["detector"] = {"label": CLASSES[det_k], "p": round(float(det[det_k]), 4)}

    agree = clf_k is not None and clf_k == det_k
    k = clf_k if agree else int(np.argmax(fused))
    if agree and classifier_p[clf_k] >= cfg["classifier_min"] and det[det_k] >= cfg["detector_min"]:
        status = "confirmed"
    elif agree:
        status = "likely"
    else:
        status = "uncertain"
    out.update(
        status=status,
        label=CLASSES[k],
        confidence=round(float(fused[k]), 4),
        severity=SEVERITY[CLASSES[k]],
        candidates=_top(fused),
        agree=agree,
        expected_accuracy=expected.get(status),
    )
    return out


# ---- the pipeline ------------------------------------------------------------
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def embed_with(model: Any, images: Sequence[np.ndarray], imgsz: int) -> np.ndarray:
    """Pooled backbone features; the heads are fitted on exactly these."""
    feats = model.embed(list(images), imgsz=imgsz, verbose=False)
    return np.stack([f.detach().cpu().numpy().ravel() for f in feats]).astype(np.float64)


def decode_image(payload: bytes) -> np.ndarray:
    """Bytes to a BGR array (EXIF rotation applied); ValueError if not an image."""
    import cv2

    img = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Not a readable image.")
    return img


class FaultDiagnoser:
    """Loads the backbone and the heads once; safe to call from several threads."""

    def __init__(self, head_path: Path | str = HEAD_PATH):
        self.head_path = Path(head_path)
        spec = json.loads(self.head_path.read_text())
        bb = spec["backbone"]
        self.backbone_path = self.head_path.parent / bb["file"]
        self.backbone_sha256 = bb["sha256"]
        self.imgsz = int(bb["imgsz"])
        self.classifier = LinearHead(spec["classifier"])
        self.panel = LinearHead(spec["panel"])
        if self.classifier.classes and tuple(self.classifier.classes) != CLASSES:
            raise ValueError(f"head classes {self.classifier.classes} != {CLASSES}")
        self.quality_cfg = {**DEFAULT_QUALITY, **spec.get("quality", {})}
        self.decision_cfg = {**DEFAULT_DECISION, **spec.get("decision", {})}
        self.expected = spec.get("metrics", {}).get("expected_accuracy", {})
        self.metrics = spec.get("metrics", {})
        self._model = None
        self._lock = threading.Lock()

    def _backbone(self):
        if self._model is None:
            from ultralytics import YOLO

            if not self.backbone_path.exists():
                raise FileNotFoundError(f"Classifier backbone not found: {self.backbone_path}")
            digest = sha256_file(self.backbone_path)
            if digest != self.backbone_sha256:
                raise RuntimeError(
                    f"{self.backbone_path.name} is not the file the heads were fitted on "
                    f"(sha256 {digest[:12]} != {self.backbone_sha256[:12]}); rerun train_head.py"
                )
            self._model = YOLO(str(self.backbone_path))
        return self._model

    def embed(self, images: Sequence[np.ndarray]) -> np.ndarray:
        with self._lock:
            return embed_with(self._backbone(), images, self.imgsz)

    def diagnose(
        self, img_bgr: np.ndarray, detections: Optional[Sequence[Any]] = None
    ) -> dict[str, Any]:
        q = quality_metrics(img_bgr)
        issues = quality_issues(q, self.quality_cfg)
        if issues:
            out = decide(None, None, None, issues, self.decision_cfg, self.expected)
        else:
            x = self.embed([img_bgr])
            panel_p = float(self.panel.proba(x)[0])
            clf_p = self.classifier.proba(x)[0]
            det = None if detections is None else detector_scores(detections)
            out = decide(clf_p, det, panel_p, [], self.decision_cfg, self.expected)
        out["quality"] = q
        return out


_diagnoser: Optional[FaultDiagnoser] = None
_diagnoser_lock = threading.Lock()


def get_diagnoser() -> FaultDiagnoser:
    global _diagnoser
    with _diagnoser_lock:
        if _diagnoser is None:
            _diagnoser = FaultDiagnoser()
    return _diagnoser
