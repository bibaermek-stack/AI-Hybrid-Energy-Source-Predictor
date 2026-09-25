"""
Smoke test for the Flet mobile app (mobile/).

Builds every screen, the app bar and the bottom navigation against the flet
version pinned in mobile/pyproject.toml. This is the check that would have
caught the flet 1.0 upgrade: ft.ElevatedButton was removed, six screens raised
AttributeError at construction, and because main() builds every view on launch
the whole app crashed before drawing anything.

It does not render through Flutter — layout errors still need a device or the
web preview — but it catches removed or renamed controls and arguments.
"""

import re
import sys
import unittest
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import flet as ft
except ImportError:  # pragma: no cover - flet is in requirements.txt
    ft = None


def pinned_flet_version() -> str:
    text = (ROOT / "mobile" / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'"flet==([^"]+)"', text)
    return match.group(1) if match else ""


class FakePage:
    """The slice of ft.Page the view builders touch while constructing."""

    def __init__(self):
        self.services = []
        self.overlay = []
        self.navigation_bar = None
        self.appbar = None

    def update(self, *args, **kwargs):
        pass

    def run_task(self, *args, **kwargs):
        pass


@unittest.skipIf(ft is None, "flet is not installed")
class TestMobileScreensBuild(unittest.TestCase):
    def test_installed_flet_matches_mobile_pin(self):
        pinned = pinned_flet_version()
        self.assertTrue(pinned, "mobile/pyproject.toml must pin flet with ==")
        from importlib.metadata import version

        self.assertEqual(
            version("flet"),
            pinned,
            "requirements.txt installs a different flet than the mobile build "
            "bundles, so this smoke test would check the wrong version",
        )

    def test_every_screen_builds_without_deprecations(self):
        """Every screen, in both languages and both themes."""
        import mobile.state as state_module
        from mobile.components.header import build_app_header
        from mobile.components.nav_bar import build_bottom_nav, build_nav_rail
        from mobile.state import state
        from mobile.views import (
            chat_view,
            faults_view,
            forecast_hub_view,
            labs_view,
            learn_view,
            live_view,
            more_view,
            optimization_view,
            overview_view,
            settings_view,
            sustainability_view,
            training_view,
        )

        page = FakePage()
        builders = {
            "overview": lambda: overview_view.build_overview_view(page, lambda key: None),
            "forecast_hub": lambda: forecast_hub_view.build_forecast_hub(page)[0],
            "faults": lambda: faults_view.build_faults_view(page),
            "training": lambda: training_view.build_training_view(page),
            "learn": lambda: learn_view.build_learn_view(page),
            "opt": lambda: optimization_view.build_optimization_view(page),
            "sustainability": lambda: sustainability_view.build_sustainability_view(page),
            "labs": lambda: labs_view.build_labs_view(page),
            "chat": lambda: chat_view.build_chat_view(page),
            "live": lambda: live_view.build_live_view(page),
            "settings": lambda: settings_view.build_settings_view(page, lambda: None),
            "more": lambda: more_view.build_more_view(page, lambda key: None),
            "header": lambda: build_app_header(page, lambda: None),
            "header_back": lambda: build_app_header(page, lambda: None, on_back=lambda: None, title="x"),
            "nav": lambda: build_bottom_nav(0, lambda e: None),
            "rail": lambda: build_nav_rail(0, lambda e: None),
        }

        # Record lookups of keys missing from mobile/i18n.py while building.
        missing_keys = set()
        real_get_text = state_module.get_text

        def recording_get_text(lang, key, default="", **fmt):
            if key not in state_module_strings:
                missing_keys.add(key)
            return real_get_text(lang, key, default, **fmt)

        from mobile.i18n import STRINGS as state_module_strings

        saved = (state.lang, state.theme_mode)
        state_module.get_text = recording_get_text
        try:
            for lang in ("kk", "en"):
                for theme in ("dark", "light"):
                    state.lang, state.theme_mode = lang, theme
                    for name, build in builders.items():
                        with self.subTest(screen=name, lang=lang, theme=theme):
                            with warnings.catch_warnings(record=True) as caught:
                                warnings.simplefilter("always")
                                control = build()
                            self.assertIsNotNone(control)
                            # A deprecation today is a removal in the next flet release.
                            deprecations = sorted(
                                {str(w.message) for w in caught if "deprecat" in str(w.message).lower()}
                            )
                            self.assertEqual(deprecations, [], f"{name} uses deprecated flet API")
        finally:
            state_module.get_text = real_get_text
            state.lang, state.theme_mode = saved
        self.assertEqual(sorted(missing_keys), [], "keys missing from mobile/i18n.py")

if __name__ == "__main__":
    unittest.main()
