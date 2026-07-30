"""HTTP helpers for EcoPredict API."""
from __future__ import annotations

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from dashboard.utils.config import HEALTH_URL


def create_session_with_retries() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_health(timeout: float = 2.0) -> dict | None:
    try:
        r = requests.get(HEALTH_URL, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        return None
    return None
