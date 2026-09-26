"""
Config and colour themes for EcoPredict AI Mobile.
"""

import os

APP_VERSION = "1.2.0"

# The one backend the app talks to: the Railway service deployed from this
# repository (AI-Hybrid-Energy-Source-Predictor). It must serve root main.py
# (`uvicorn main:app --port $PORT`) so /health reports api: "full".
# Must stay HTTPS: Android blocks cleartext HTTP by default from targetSdk 28,
# so an http:// base silently fails in the APK no matter what the server does.
PRODUCTION_API_BASE = "https://ecopradict-mobile-production.up.railway.app"

# Desktop/web preview can point at a local API instead, e.g.
#   ECOPREDICT_API_BASE=http://127.0.0.1:8001 python run_mobile.py
# The variable is never set inside the APK/IPA, so phones always use production.
DEFAULT_API_BASE = (os.environ.get("ECOPREDICT_API_BASE") or PRODUCTION_API_BASE).strip().rstrip("/")

# App Colors - Dark & Light Palettes
COLORS = {
    "dark": {
        "bg": "#0F172A",
        "surface": "#1E293B",
        "surface_variant": "#334155",
        "primary": "#3B82F6",
        "primary_container": "#1E3A8A",
        "secondary": "#14B8A6",
        "accent": "#F59E0B",
        "text_primary": "#F8FAFC",
        "text_secondary": "#94A3B8",
        "success": "#10B981",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "card_border": "#334155",
    },
    "light": {
        "bg": "#F8FAFC",
        "surface": "#FFFFFF",
        "surface_variant": "#E2E8F0",
        "primary": "#2563EB",
        "primary_container": "#DBEAFE",
        "secondary": "#0D9488",
        "accent": "#D97706",
        "text_primary": "#0F172A",
        "text_secondary": "#64748B",
        "success": "#059669",
        "warning": "#D97706",
        "error": "#DC2626",
        "card_border": "#E2E8F0",
    },
}

# UI strings live in i18n.py as (kk, en) pairs; re-exported for state.text().
try:
    from mobile.i18n import get_text  # noqa: E402,F401
except (ImportError, ModuleNotFoundError):
    from i18n import get_text  # type: ignore # noqa: E402,F401 # pyright: ignore[reportMissingImports]
