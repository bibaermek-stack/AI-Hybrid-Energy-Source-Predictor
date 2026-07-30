"""
EcoPredict AI Launcher - Multi-Service Orchestrator.

Runs both:
  1. FastAPI API server on port 8001 (for ML inference endpoints).
  2. Streamlit Dashboard on Railway's assigned $PORT (or 8080 locally).
"""

import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path

# Project root on sys.path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _wait_for_api(url="http://127.0.0.1:8001/health", timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=2)
            if req.status == 200:
                print("FastAPI API is ready!", flush=True)
                return True
        except Exception:
            pass
        time.sleep(1)
    print("WARNING: FastAPI API did not respond within timeout.", flush=True)
    return False


def main():
    # Railway public HTTP port
    port = os.environ.get("PORT", "8080")

    # Streamlit -> FastAPI on the same container (internal only)
    os.environ.setdefault("API_URL", "http://127.0.0.1:8001/predict")
    os.environ.setdefault("EXPLAIN_URL", "http://127.0.0.1:8001/explain")
    os.environ.setdefault("HEALTH_URL", "http://127.0.0.1:8001/health")
    os.environ.setdefault("FORECAST_URL", "http://127.0.0.1:8001/forecast-batch")
    os.environ.setdefault("CHAT_URL", "http://127.0.0.1:8001/chat")
    os.environ.setdefault("SOLARMAN_PROCESS_URL", "http://127.0.0.1:8001/solarman/process")
    os.environ.setdefault("SOLARMAN_ROI_URL", "http://127.0.0.1:8001/solarman/roi")
    os.environ.setdefault("SOLARMAN_WEATHER_URL", "http://127.0.0.1:8001/solarman/weather")
    os.environ.setdefault("SOLARMAN_ALERT_URL", "http://127.0.0.1:8001/solarman/alert")
    os.environ.setdefault("SOLARMAN_FC_URL", "http://127.0.0.1:8001/solarman/forecast")
    os.environ.setdefault("SOLARMAN_LIVE_URL", "http://127.0.0.1:8001/solarman/live")
    os.environ.setdefault("SOLARMAN_HISTORY_URL", "http://127.0.0.1:8001/solarman/history")
    os.environ.setdefault("SOLARMAN_STATUS_URL", "http://127.0.0.1:8001/solarman/status")

    print("Starting FastAPI API on port 8001...", flush=True)
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8001",
        ]
    )

    print(f"Starting Streamlit Dashboard on port {port}...", flush=True)
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "dashboard/app.py",
                "--server.port",
                port,
                "--server.address",
                "0.0.0.0",
                "--server.headless",
                "true",
                "--server.enableCORS",
                "true",
                "--client.showErrorDetails",
                "true",
                "--server.enableXsrfProtection",
                "false",
                "--server.enableWebsocketCompression",
                "false",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("Stopping services...", flush=True)
    finally:
        api_process.terminate()
        try:
            api_process.wait(timeout=10)
        except Exception:
            api_process.kill()


if __name__ == "__main__":
    main()
