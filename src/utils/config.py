"""
Central path and environment configuration for EcoPredict AI.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project root: .../EcoPredict AI
ROOT = Path(__file__).resolve().parents[2]

ARTIFACTS_DIR = Path(os.getenv("MODEL_PATH", ROOT / "artifacts")).resolve()
DATA_DIR = ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"
VECTOR_DB_DIR = ROOT / "vector_db"
LOGS_DIR = ROOT / "logs"

# API defaults (local / Railway internal)
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8001"))
API_BASE = os.getenv("API_BASE", f"http://{API_HOST}:{API_PORT}")

WEATHERAPI_KEY = (
    os.getenv("WEATHERAPI_KEY") or os.getenv("WEATHER_API_KEY") or ""
).strip()

# Site defaults — Turkistan, KZ
SITE_LAT = float(os.getenv("SITE_LAT", "43.2973"))
SITE_LON = float(os.getenv("SITE_LON", "68.2517"))
SITE_NAME = os.getenv("SITE_NAME", "Turkistan")

# Grid / carbon defaults
GRID_CO2_KG_PER_KWH = float(os.getenv("GRID_CO2_KG_PER_KWH", "0.45"))


def ensure_runtime_dirs() -> None:
    """Create commonly used directories if missing."""
    for d in (LOGS_DIR, VECTOR_DB_DIR, SAMPLE_DATA_DIR, PROCESSED_DATA_DIR):
        d.mkdir(parents=True, exist_ok=True)
