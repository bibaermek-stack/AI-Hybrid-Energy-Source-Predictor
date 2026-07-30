"""
EcoPredict AI - NiceGUI Web Dashboard Launcher.

Usage:
    python run_nicegui.py          # Launch NiceGUI Web App at http://127.0.0.1:8560
"""

import sys
from pathlib import Path

# Project root on sys.path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from nicegui_app.main import run

if __name__ == "__main__":
    print("Starting EcoPredict AI NiceGUI Web Dashboard at http://127.0.0.1:8560 ...", flush=True)
    run()
