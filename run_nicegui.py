"""
EcoPredict AI - Root NiceGUI Web Dashboard Launcher.
"""

import importlib
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent / "EcoPredict AI"
if _ROOT.exists():
    os.chdir(str(_ROOT))
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))

_nicegui_main = importlib.import_module("nicegui_app.main")
run = _nicegui_main.run

if __name__ == "__main__":
    print("Starting EcoPredict AI NiceGUI Web Dashboard at http://127.0.0.1:8560 ...", flush=True)
    run()
