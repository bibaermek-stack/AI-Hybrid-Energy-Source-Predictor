"""
EcoPredict AI - Root Mobile Launcher.
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

_ft = importlib.import_module("flet")
_mobile_main = importlib.import_module("mobile.main")
main = _mobile_main.main

if __name__ == "__main__":
    is_web = "--web" in sys.argv
    if is_web:
        print("Launching EcoPredict AI Mobile in Web Browser Mode...", flush=True)
        _ft.run(main, view=_ft.AppView.WEB_BROWSER, port=8555)
    else:
        print("Launching EcoPredict AI Mobile in Desktop Preview Window...", flush=True)
        _ft.run(main)
