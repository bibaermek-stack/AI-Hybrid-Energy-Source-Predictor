"""
What the site and the NiceGUI page say for a /detect diagnosis
(src/fault_detection/texts.py), and that neither page has a verdict that did
not come from the server.
"""

from __future__ import annotations

import io
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fault_detection.diagnosis import CLASSES  # noqa: E402
from src.fault_detection.texts import ADVICE, CLASS_NAMES, WORDS, describe  # noqa: E402

CYRILLIC = re.compile(r"[Ѐ-ӿ]")


def sample(status, label="Dust", other="Bird", severity="cleaning"):
    return {
        "status": status,
        "label": None if status in ("retake", "not_panel") else label,
        "confidence": 0.93,
        "severity": severity,
        "expected_accuracy": {"confirmed": 0.985, "likely": 0.797, "uncertain": 0.496}.get(status),
        "issues": ["blurry", "overexposed"] if status == "retake" else [],
        "candidates": [{"label": label, "p": 0.6}, {"label": other, "p": 0.3}],
        "models": {
            "classifier": {"label": label, "p": 0.96},
            "detector": {"label": other if status == "uncertain" else label, "p": 0.7},
        },
    }


class TestDescribe(unittest.TestCase):
    def test_every_class_has_a_name_and_advice(self):
        for cls in CLASSES:
            self.assertIn(cls, CLASS_NAMES)
            self.assertIn(cls, ADVICE)

    def test_each_status_in_both_languages(self):
        for lang in ("kk", "en"):
            for status in ("confirmed", "likely", "uncertain", "not_panel", "retake"):
                with self.subTest(lang=lang, status=status):
                    d = describe(sample(status), lang)
                    self.assertTrue(d["headline"])
                    self.assertTrue(d["advice"])
                    self.assertIn(d["tone"], ("success", "warning", "error", "info"))
                    if lang == "en":
                        text = " ".join([d["headline"], d["advice"], *d["details"]])
                        self.assertIsNone(CYRILLIC.search(text), text)

    def test_confirmed_names_the_class_and_the_measured_accuracy(self):
        d = describe(sample("confirmed", label="Physical", severity="repair"), "en")
        self.assertEqual(d["headline"], "✓ Confirmed: Physical damage")
        self.assertIn("98.5%", d["confidence"])
        self.assertEqual(d["tone"], "error")
        self.assertEqual(describe(sample("confirmed", label="Clean"), "en")["tone"], "success")

    def test_uncertain_gives_no_verdict_only_what_each_model_said(self):
        d = describe(sample("uncertain"), "en")
        self.assertEqual(d["headline"], WORDS["uncertain"][1])
        self.assertIsNone(d["confidence"])
        self.assertNotIn(ADVICE["Dust"][1], d["advice"])
        self.assertIn("YOLO11 detector: Bird droppings 70%", d["details"][0])
        self.assertTrue(d["details"][1].startswith("Candidates: Dust 60%"))

    def test_retake_names_the_reasons(self):
        d = describe(sample("retake"), "en")
        self.assertIn("blurred", d["advice"])
        self.assertIn("overexposed", d["advice"])


class TestSiteBoxes(unittest.TestCase):
    def test_boxes_are_drawn_on_the_photo(self):
        try:
            from PIL import Image

            from dashboard.components.fault_check import boxed_image
        except ImportError as err:
            self.skipTest(str(err))
        buf = io.BytesIO()
        Image.new("RGB", (200, 100), (0, 0, 0)).save(buf, format="PNG")
        img = boxed_image(
            buf.getvalue(),
            [{"class_name": "Dust", "confidence": 0.8, "box": [10, 10, 90, 60]}],
            "en",
        )
        self.assertEqual(img.size, (200, 100))
        self.assertNotEqual(img.getpixel((10, 30)), (0, 0, 0))  # on the left edge
        self.assertEqual(img.getpixel((150, 80)), (0, 0, 0))  # outside
        self.assertIsNone(boxed_image(buf.getvalue(), [], "en"))


class TestNoMadeUpVerdicts(unittest.TestCase):
    """The pages that used to print fixed diagnoses must call /detect instead."""

    def test_nicegui_page_calls_detect(self):
        src = (ROOT / "nicegui_app" / "pages" / "faults_page.py").read_text(encoding="utf-8")
        self.assertIn("api_client.detect(", src)
        self.assertNotRegex(src, r"set_diagnosis\(\s*\"")
        self.assertNotIn("Analyzed Custom Upload", src)

    def test_site_page_has_one_check(self):
        src = (ROOT / "dashboard" / "views" / "diagnostics.py").read_text(encoding="utf-8")
        self.assertIn("run_fault_check(uploaded_file, lang)", src)
        self.assertNotIn("load_clean_dirty_model", src)
        self.assertNotIn("yolo_model.predict", src)


if __name__ == "__main__":
    unittest.main()
