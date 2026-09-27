"""
The fault diagnosis: the decision rule, the image-quality gate, the head file,
and (when ultralytics is installed) the whole pipeline behind POST /detect.

The pipeline cases use photos cut from the author's mosaics, which the final
heads were fitted on, so they check that the pieces fit together, not how
accurate the models are; that is measured by
scripts/fault_detection/train_head.py and stored in fault_head.json.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fault_detection import diagnosis as dg  # noqa: E402

HAS_ULTRALYTICS = importlib.util.find_spec("ultralytics") is not None
HAS_CV2 = importlib.util.find_spec("cv2") is not None


def probs(label: str, p: float) -> np.ndarray:
    """A classifier output with `p` on `label` and the rest spread evenly."""
    out = np.full(len(dg.CLASSES), (1 - p) / (len(dg.CLASSES) - 1))
    out[dg.CLASSES.index(label)] = p
    return out


def det(**scores: float) -> np.ndarray:
    out = np.zeros(len(dg.CLASSES))
    for k, v in scores.items():
        out[dg.CLASSES.index(k)] = v
    return out


class TestDecide(unittest.TestCase):
    expected = {"confirmed": 0.985, "likely": 0.8, "uncertain": 0.5}

    def test_quality_issues_ask_for_a_retake(self):
        d = dg.decide(probs("Dust", 0.99), det(Dust=0.9), 0.99, ["blurry"])
        self.assertEqual(d["status"], "retake")
        self.assertIsNone(d["label"])
        self.assertEqual(d["issues"], ["blurry"])

    def test_not_a_panel(self):
        d = dg.decide(probs("Dust", 0.99), det(Dust=0.9), 0.1, [])
        self.assertEqual(d["status"], "not_panel")
        self.assertIsNone(d["label"])

    def test_confirmed_needs_agreement_and_both_confident(self):
        d = dg.decide(probs("Snow", 0.95), det(Snow=0.8), 0.99, [], expected=self.expected)
        self.assertEqual((d["status"], d["label"], d["agree"]), ("confirmed", "Snow", True))
        self.assertEqual(d["expected_accuracy"], 0.985)
        self.assertEqual(d["severity"], "cleaning")

    def test_agreeing_but_unsure_is_only_likely(self):
        cfg = dg.DEFAULT_DECISION
        weak_clf = dg.decide(
            probs("Physical", cfg["classifier_min"] - 0.05), det(Physical=0.9), 0.99, []
        )
        weak_det = dg.decide(
            probs("Physical", 0.95), det(Physical=cfg["detector_min"] - 0.05), 0.99, []
        )
        for d in (weak_clf, weak_det):
            self.assertEqual((d["status"], d["label"]), ("likely", "Physical"))
            self.assertEqual(d["severity"], "repair")

    def test_disagreement_is_uncertain_however_confident(self):
        d = dg.decide(probs("Dust", 0.99), det(Bird=0.95), 0.99, [], expected=self.expected)
        self.assertEqual(d["status"], "uncertain")
        self.assertFalse(d["agree"])
        self.assertEqual(d["models"]["classifier"]["label"], "Dust")
        self.assertEqual(d["models"]["detector"]["label"], "Bird")
        self.assertEqual({c["label"] for c in d["candidates"][:2]}, {"Dust", "Bird"})
        self.assertEqual(d["expected_accuracy"], 0.5)

    def test_one_model_alone_is_never_confirmed(self):
        only_clf = dg.decide(probs("Clean", 0.999), None, 0.99, [])
        only_det = dg.decide(None, det(Clean=0.99), None, [])
        self.assertEqual(only_clf["status"], "uncertain")
        self.assertEqual(only_det["status"], "uncertain")
        self.assertEqual(only_det["label"], "Clean")

    def test_no_model_answered(self):
        d = dg.decide(None, None, None, [])
        self.assertEqual(d["status"], "uncertain")
        self.assertIsNone(d["label"])

    def test_confidence_is_the_fused_probability(self):
        d = dg.decide(probs("Dust", 0.9), det(Dust=0.8), 0.99, [])
        w = dg.DEFAULT_DECISION["classifier_weight"]
        self.assertAlmostEqual(d["confidence"], w * 0.9 + (1 - w) * 1.0, places=3)

    def test_detector_scores_keep_the_best_box_per_class(self):
        s = dg.detector_scores(
            [
                {"class_name": "Dust", "confidence": 0.3},
                {"class_name": "Dust", "confidence": 0.7},
                {"class_name": "Bird", "confidence": 0.2},
                {"class_name": "Unknown", "confidence": 0.9},
            ]
        )
        self.assertEqual(s[dg.CLASSES.index("Dust")], 0.7)
        self.assertEqual(s[dg.CLASSES.index("Bird")], 0.2)
        self.assertAlmostEqual(s.sum(), 0.9)


@unittest.skipUnless(HAS_CV2, "opencv not installed")
class TestQualityGate(unittest.TestCase):
    def issues(self, img):
        return dg.quality_issues(dg.quality_metrics(img))

    def test_a_textured_photo_passes(self):
        rng = np.random.default_rng(0)
        self.assertEqual(self.issues(rng.integers(40, 220, (300, 400, 3), dtype=np.uint8)), [])

    def test_dark_blurred_glare_and_tiny_are_named(self):
        rng = np.random.default_rng(0)
        texture = rng.integers(40, 220, (300, 400, 3), dtype=np.uint8)
        self.assertEqual(self.issues((texture * 0.05).astype(np.uint8)), ["too_dark"])
        self.assertEqual(self.issues(np.full((300, 400, 3), 128, np.uint8)), ["blurry"])
        self.assertEqual(self.issues(np.full((300, 400, 3), 255, np.uint8)), ["overexposed"])
        self.assertIn("too_small", self.issues(texture[:40, :40]))

    def test_large_photos_are_measured_at_512px(self):
        m = dg.quality_metrics(np.zeros((3000, 4000, 3), np.uint8))
        self.assertEqual((m["width"], m["height"]), (4000, 3000))


class TestHeads(unittest.TestCase):
    def test_softmax_rows_sum_to_one_and_binary_is_a_sigmoid(self):
        rng = np.random.default_rng(1)
        multi = dg.LinearHead(
            {
                "mean": [0, 0],
                "scale": [1, 1],
                "coef": rng.normal(size=(6, 2)).tolist(),
                "intercept": [0] * 6,
            }
        )
        np.testing.assert_allclose(multi.proba(rng.normal(size=(5, 2))).sum(axis=1), 1.0)
        binary = dg.LinearHead({"mean": [1.0], "scale": [2.0], "coef": [[3.0]], "intercept": [0.5]})
        z = (5.0 - 1.0) / 2.0 * 3.0 + 0.5
        self.assertAlmostEqual(float(binary.proba(np.array([5.0]))[0]), 1 / (1 + np.exp(-z)))


class TestHeadFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads(dg.HEAD_PATH.read_text())

    def test_shapes_and_classes(self):
        dim = self.spec["backbone"]["dim"]
        clf, panel = self.spec["classifier"], self.spec["panel"]
        self.assertEqual(tuple(clf["classes"]), dg.CLASSES)
        self.assertEqual(np.shape(clf["coef"]), (len(dg.CLASSES), dim))
        self.assertEqual(np.shape(panel["coef"]), (1, dim))
        for head in (clf, panel):
            self.assertEqual(len(head["mean"]), dim)
            self.assertTrue(all(s > 0 for s in head["scale"]))

    def test_backbone_file_is_the_one_the_heads_were_fitted_on(self):
        path = dg.HEAD_PATH.parent / self.spec["backbone"]["file"]
        self.assertTrue(path.exists(), path)
        self.assertEqual(dg.sha256_file(path), self.spec["backbone"]["sha256"])

    def test_backbone_fingerprint_is_recorded(self):
        fp = self.spec["backbone"]["fingerprint"]
        self.assertEqual(len(fp), 32)
        self.assertTrue(dg.fingerprint_matches(np.asarray(fp), fp))
        self.assertFalse(dg.fingerprint_matches(np.asarray(fp) + 0.5, fp))

    def test_metrics_are_recorded(self):
        m = self.spec["metrics"]
        for status in ("confirmed", "likely", "uncertain"):
            self.assertIn(status, m["expected_accuracy"])
        # the reason the rule exists: confirmed answers beat either model alone
        self.assertGreaterEqual(m["expected_accuracy"]["confirmed"], 0.95)
        self.assertGreater(
            m["expected_accuracy"]["confirmed"], m["accuracy"]["detector_alone_heldout"]
        )
        self.assertLessEqual(m["panel_gate"]["non_panels_accepted_unseen"], 0.01)
        self.assertEqual(m["quality_gate"]["real_photos_flagged"], 0)


def load_real_crops():
    spec = importlib.util.spec_from_file_location(
        "real_crops", ROOT / "scripts" / "fault_detection" / "real_crops.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mosaic_photo(split: str, stem: str, r: int, c: int) -> tuple[np.ndarray, str]:
    """One labelled photo cut from the author's mosaic, as BGR."""
    from PIL import Image

    rc = load_real_crops()
    mos = np.asarray(Image.open(rc.mosaic_path(split, stem)).convert("RGB")).astype(int)
    th, tw = mos.shape[0] // 4, mos.shape[1] // 4
    crop = rc.crop_tile(mos[r * th + 2 : (r + 1) * th - 2, c * tw + 2 : (c + 1) * tw - 2])
    return np.ascontiguousarray(crop[:, :, ::-1]).astype(np.uint8), rc.LABELS[(split, stem)][r][c]


@unittest.skipUnless(HAS_ULTRALYTICS and HAS_CV2, "ultralytics/opencv not installed")
class TestPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from src.fault_detection.yolo.detector import YOLOFaultDetector

        cls.diagnoser = dg.FaultDiagnoser()
        cls.detector = YOLOFaultDetector()

    def run_one(self, img):
        return self.diagnoser.diagnose(img, self.detector.predict(img, conf=0.05))

    def test_clear_photos_are_confirmed_with_the_right_class(self):
        for split, stem, r, c in (
            ("test", "val_batch0_labels", 2, 0),
            ("test", "val_batch0_labels", 0, 1),
        ):
            img, label = mosaic_photo(split, stem, r, c)
            with self.subTest(label=label):
                d = self.run_one(img)
                self.assertEqual((d["status"], d["label"]), ("confirmed", label))
                self.assertGreater(d["panel_p"], 0.9)

    def test_blurred_photo_is_sent_back(self):
        import cv2

        img, _ = mosaic_photo("test", "val_batch0_labels", 2, 0)
        d = self.run_one(cv2.GaussianBlur(img, (0, 0), 5))
        self.assertEqual((d["status"], d["issues"]), ("retake", ["blurry"]))

    def test_noise_is_not_a_panel(self):
        import cv2

        noise = sorted((ROOT / "data" / "solar-panel-images" / "Faulty_solar_panel").rglob("*.jpg"))
        self.assertTrue(noise)
        self.assertEqual(self.run_one(cv2.imread(str(noise[0])))["status"], "not_panel")


@unittest.skipUnless(HAS_ULTRALYTICS and HAS_CV2, "ultralytics/opencv not installed")
class TestDetectRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient

        from main import app

        cls.client = TestClient(app)

    def test_detect_returns_boxes_and_the_diagnosis(self):
        import cv2

        img, label = mosaic_photo("test", "val_batch0_labels", 0, 1)
        ok, buf = cv2.imencode(".jpg", img)
        r = self.client.post("/detect", files={"file": ("panel.jpg", buf.tobytes(), "image/jpeg")})
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertIsNone(body["diagnosis_error"])
        self.assertEqual(body["diagnosis"]["status"], "confirmed")
        self.assertEqual(body["diagnosis"]["label"], label)
        self.assertIsNotNone(body["diagnosis"]["expected_accuracy"])
        # older apps read these
        self.assertEqual(body["primary"]["class_name"], label)
        self.assertEqual(body["count"], len(body["detections"]))

    def test_unreadable_upload_is_a_400(self):
        r = self.client.post("/detect", files={"file": ("x.jpg", b"not an image", "image/jpeg")})
        self.assertEqual(r.status_code, 400)

    def test_model_card(self):
        r = self.client.get("/detect/model")
        self.assertEqual(r.status_code, 200)
        self.assertIn("expected_accuracy", r.json()["metrics"])


if __name__ == "__main__":
    unittest.main()
