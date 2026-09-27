"""
The fault screen shows the server's diagnosis as given: a verdict only when
the server confirmed or found it likely, never for "uncertain".
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from mobile.i18n import STRINGS, get_text
    from mobile.views.faults_view import RECOMMENDATIONS, describe_diagnosis
except ImportError as err:  # flet missing
    raise unittest.SkipTest(f"mobile app not importable: {err}")

from src.fault_detection.diagnosis import CLASSES  # noqa: E402

ISSUES = ("blurry", "too_dark", "overexposed", "too_small")


def texts(lang):
    return lambda key, default="", **fmt: get_text(lang, key, default, **fmt)


def sample(status, label="Dust", other="Bird"):
    return {
        "status": status,
        "label": label if status not in ("retake", "not_panel") else None,
        "confidence": 0.93,
        "expected_accuracy": {"confirmed": 0.985, "likely": 0.8, "uncertain": 0.5}.get(status),
        "issues": ["blurry", "too_dark"] if status == "retake" else [],
        "candidates": [{"label": label, "p": 0.6}, {"label": other, "p": 0.3}],
        "models": {
            "classifier": {"label": label, "p": 0.96},
            "detector": {"label": label if status != "uncertain" else other, "p": 0.7},
        },
    }


class TestDescribeDiagnosis(unittest.TestCase):
    def test_every_class_and_issue_has_text(self):
        for cls in CLASSES:
            self.assertIn(cls, RECOMMENDATIONS)
            self.assertIn(f"fl_class_{cls}", STRINGS)
        for issue in ISSUES:
            self.assertIn(f"fl_issue_{issue}", STRINGS)

    def test_each_status_in_both_languages(self):
        for lang in ("kk", "en"):
            t = texts(lang)
            for status in ("confirmed", "likely", "uncertain", "not_panel", "retake"):
                with self.subTest(lang=lang, status=status):
                    d = describe_diagnosis(sample(status), t)
                    self.assertTrue(d["headline"])
                    self.assertTrue(d["advice"])
                    self.assertIn(d["tone"], ("success", "warning", "error", "text_secondary"))

    def test_uncertain_gives_no_verdict(self):
        t = texts("en")
        d = describe_diagnosis(sample("uncertain"), t)
        self.assertEqual(d["headline"], get_text("en", "fl_st_uncertain"))
        self.assertEqual(d["confidence"], "—")
        self.assertNotIn(get_text("en", "fl_rec_dust"), d["advice"])
        # but says what each model thought
        self.assertTrue(any("Bird droppings" in line for line in d["details"]))

    def test_confirmed_names_the_class_and_the_measured_accuracy(self):
        d = describe_diagnosis(sample("confirmed", label="Electrical"), texts("en"))
        self.assertIn("Electrical damage", d["headline"])
        self.assertIn("98.5%", d["confidence"])
        self.assertEqual(d["tone"], "error")

    def test_retake_lists_the_reasons(self):
        d = describe_diagnosis(sample("retake"), texts("en"))
        self.assertIn("blurred", d["advice"])
        self.assertIn("too dark", d["advice"])


if __name__ == "__main__":
    unittest.main()
