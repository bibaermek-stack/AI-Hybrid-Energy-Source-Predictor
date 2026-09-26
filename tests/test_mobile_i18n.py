"""
Localization checks for the mobile app (mobile/i18n.py).

The app used to hardcode ~120 Kazakh strings in the screens, so switching to
English changed little more than the app bar, and five Settings labels existed
only in English. These tests keep both languages complete.
"""

import ast
import re
import string
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "mobile"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mobile.i18n import STRINGS, get_text  # noqa: E402

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
# Keys referenced as literals: t("key") or state.text("key").
KEY_CALL = re.compile(r'(?:\bt|state\.text)\(\s*"([a-z0-9_]+)"')
# Keys held in lookup tables (nav destinations, recommendations, ...).
TABLE_KEY = re.compile(r"^(?:nav_|more_|hub_|fl_rec_|feat_|lab_weather_|learn_|chat_chip)[a-z0-9_]*$")


def mobile_sources():
    for path in sorted(MOBILE.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "i18n.py":
            continue
        yield path


def string_constants(tree: ast.AST):
    """String literals that are not docstrings."""
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
            yield node


def fields(template: str) -> set:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


class TestStringsTable(unittest.TestCase):
    def test_every_entry_has_both_languages(self):
        for key, value in STRINGS.items():
            with self.subTest(key=key):
                self.assertIsInstance(value, tuple)
                self.assertEqual(len(value), 2)
                kk, en = value
                self.assertTrue(kk.strip(), "empty Kazakh text")
                self.assertTrue(en.strip(), "empty English text")

    def test_placeholders_match_and_format(self):
        for key, (kk, en) in STRINGS.items():
            with self.subTest(key=key):
                self.assertEqual(fields(kk), fields(en))
                # An int satisfies every spec used here ({v:.1f}, {hour:02d}, {s}).
                args = {name: 1 for name in fields(kk)}
                get_text("kk", key, **args)
                get_text("en", key, **args)

    def test_english_text_has_no_cyrillic(self):
        allowed = {"lang_name_kk"}  # each language is named in itself
        for key, (_, en) in STRINGS.items():
            if key in allowed:
                continue
            with self.subTest(key=key):
                self.assertIsNone(CYRILLIC.search(en), en)


class TestMobileCodeUsesTheTable(unittest.TestCase):
    def test_every_referenced_key_exists(self):
        missing = {}
        for path in mobile_sources():
            src = path.read_text(encoding="utf-8")
            keys = set(KEY_CALL.findall(src))
            for node in string_constants(ast.parse(src)):
                if TABLE_KEY.match(node.value):
                    keys.add(node.value)
            absent = sorted(k for k in keys if k not in STRINGS)
            if absent:
                missing[path.name] = absent
        self.assertEqual(missing, {})

    def test_no_hardcoded_kazakh_outside_the_table(self):
        found = {}
        for path in mobile_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            hits = [n.value for n in string_constants(tree) if CYRILLIC.search(n.value)]
            if hits:
                found[str(path.relative_to(ROOT))] = hits
        self.assertEqual(found, {}, "move these strings into mobile/i18n.py")


if __name__ == "__main__":
    unittest.main()
