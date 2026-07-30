"""
EcoPredict AI - Mobile Application Launcher.

Usage:
    python run_mobile.py           # Launch in desktop/mobile window mode
    python run_mobile.py --web     # Launch in web browser mode
"""

import sys
from pathlib import Path

# Ensure root on sys.path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import flet as ft
from mobile.main import main

if __name__ == "__main__":
    is_web = "--web" in sys.argv
    if is_web:
        print("Launching EcoPredict AI Mobile in Web Browser Mode...", flush=True)
        ft.run(main, view=ft.AppView.WEB_BROWSER, port=8550)
    else:
        print("Launching EcoPredict AI Mobile in Desktop Preview Window...", flush=True)
        ft.run(main)
