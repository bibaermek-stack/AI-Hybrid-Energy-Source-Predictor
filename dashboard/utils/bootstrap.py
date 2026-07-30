"""Ensure project root is on sys.path so `import dashboard.*` works."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]  # EcoPredict AI/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Prepare dashboard/static for Streamlit enableStaticServing (/app/static)
try:
    from dashboard.static_server import ensure_streamlit_static_assets

    ensure_streamlit_static_assets()
except Exception:
    pass
