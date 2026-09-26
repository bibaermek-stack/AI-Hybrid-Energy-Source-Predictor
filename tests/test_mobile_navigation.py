"""
Navigation rules of the mobile app (mobile/components/nav_bar.py): which tab a
screen belongs to and where the Android Back button goes.
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import flet  # noqa: F401
except ImportError:  # pragma: no cover - flet is in requirements.txt
    flet = None


@unittest.skipIf(flet is None, "flet is not installed")
class TestNavigation(unittest.TestCase):
    def setUp(self):
        from mobile.components import nav_bar

        self.nav = nav_bar

    def test_five_tabs_with_home_first(self):
        self.assertEqual(self.nav.TAB_KEYS, ["overview", "forecast", "live", "chat", "more"])

    def test_more_screens_are_not_tabs(self):
        self.assertEqual(self.nav.MORE_KEYS & set(self.nav.TAB_KEYS), set())
        self.assertEqual(
            self.nav.MORE_KEYS,
            {"faults", "opt", "sustainability", "labs", "training", "learn", "settings"},
        )

    def test_more_screens_highlight_the_more_tab(self):
        more = self.nav.TAB_KEYS.index("more")
        for screen in self.nav.MORE_KEYS:
            self.assertEqual(self.nav.tab_index(screen), more, screen)

    def test_back_from_a_more_screen_returns_to_more(self):
        for screen in self.nav.MORE_KEYS:
            self.assertEqual(self.nav.back_target(screen), "more", screen)

    def test_back_from_other_tabs_returns_home(self):
        for screen in ("forecast", "live", "chat", "more"):
            self.assertEqual(self.nav.back_target(screen), "overview", screen)

    def test_back_on_home_leaves_the_app(self):
        self.assertIsNone(self.nav.back_target("overview"))


if __name__ == "__main__":
    unittest.main()
