"""API URLs and environment config for EcoPredict dashboard."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001/predict")
EXPLAIN_URL = os.getenv("EXPLAIN_URL", "http://127.0.0.1:8001/explain")
HEALTH_URL = os.getenv("HEALTH_URL", "http://127.0.0.1:8001/health")
FORECAST_URL = os.getenv("FORECAST_URL", "http://127.0.0.1:8001/forecast-batch")
CHAT_URL = os.getenv("CHAT_URL", "http://127.0.0.1:8001/chat")
SOLARMAN_PROCESS_URL = os.getenv("SOLARMAN_PROCESS_URL", "http://127.0.0.1:8001/solarman/process")
SOLARMAN_ROI_URL = os.getenv("SOLARMAN_ROI_URL", "http://127.0.0.1:8001/solarman/roi")
SOLARMAN_WEATHER_URL = os.getenv("SOLARMAN_WEATHER_URL", "http://127.0.0.1:8001/solarman/weather")
SOLARMAN_ALERT_URL = os.getenv("SOLARMAN_ALERT_URL", "http://127.0.0.1:8001/solarman/alert")
SOLARMAN_FC_URL = os.getenv("SOLARMAN_FC_URL", "http://127.0.0.1:8001/solarman/forecast")
SOLARMAN_LIVE_URL = os.getenv("SOLARMAN_LIVE_URL", "http://127.0.0.1:8001/solarman/live")
SOLARMAN_HISTORY_URL = os.getenv("SOLARMAN_HISTORY_URL", "http://127.0.0.1:8001/solarman/history")
SOLARMAN_STATUS_URL = os.getenv("SOLARMAN_STATUS_URL", "http://127.0.0.1:8001/solarman/status")
SOLARMAN_CONFIGURE_URL = os.getenv("SOLARMAN_CONFIGURE_URL", "http://127.0.0.1:8001/solarman/configure")
