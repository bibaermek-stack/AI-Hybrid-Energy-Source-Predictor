"""
Async REST API Client for EcoPredict AI Backend using Python standard library.
"""

import asyncio
import json
import logging
import ssl
import urllib.request
from typing import Dict, Any, Optional, List
try:
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

logger = logging.getLogger(__name__)

# Last transport-level failure, surfaced in Settings so a broken connection can
# be diagnosed from the phone instead of guessing.
last_http_error: str = ""


def _build_ssl_context() -> ssl.SSLContext:
    """
    Android has no OpenSSL CA bundle at the path Python compiles in, so every
    HTTPS request through urllib fails with CERTIFICATE_VERIFY_FAILED and the
    app reports "no internet" on a perfectly good connection. certifi ships in
    the APK (it comes along with flet), so point the context at its bundle.
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception as exc:  # desktop/dev, where the system store works
        logger.info("certifi unavailable, using system trust store: %s", exc)
        return ssl.create_default_context()


_SSL_CONTEXT = _build_ssl_context()


def _http_get_sync(url: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """Synchronous HTTP GET using urllib.request."""
    global last_http_error
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "EcoPredict-Mobile/1.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                return json.loads(body)
            last_http_error = f"HTTP {resp.status} from {url}"
    except Exception as e:
        last_http_error = f"{type(e).__name__}: {e}"
        logger.warning("HTTP GET error for %s: %s", url, e)
    return None


def _http_post_sync(url: str, payload: Dict[str, Any], timeout: float = 10.0) -> Optional[Dict[str, Any]]:
    """Synchronous HTTP POST using urllib.request."""
    global last_http_error
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "EcoPredict-Mobile/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            if resp.status == 200:
                body = resp.read().decode("utf-8")
                return json.loads(body)
            last_http_error = f"HTTP {resp.status} from {url}"
    except Exception as e:
        last_http_error = f"{type(e).__name__}: {e}"
        logger.warning("HTTP POST error for %s: %s", url, e)
    return None


class APIClient:
    """Handles REST API communication with FastAPI backend without third-party dependencies."""

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    @staticmethod
    def _serves_feature_routes(res: Dict[str, Any]) -> bool:
        """
        Whether a /health reply comes from a backend that actually mounts
        /predict, /chat and /solarman/*.

        main.py answers /health even when the API router fails to import, so a
        plain 200 proves nothing — accepting it makes the app report "online"
        while every feature 404s. `api: "full"` is the explicit contract;
        `forecast_backend` is what api/routes.py has always returned.
        """
        return res.get("api") == "full" or "forecast_backend" in res

    async def check_health(self) -> Dict[str, Any]:
        """Find a backend that serves the feature routes, not just /health."""
        candidates = [
            state.api_base_url.strip().rstrip("/"),
            "https://ecopradict-mobile-production.up.railway.app",
            "https://ecopradict-ai-production.up.railway.app",
            "https://www.ecopredict.kz",
            # Android blocks cleartext HTTP by default (targetSdk >= 28), so
            # these only ever resolve in the desktop/web preview.
            "http://127.0.0.1:8001",
            "http://127.0.0.1:8555",
        ]
        unique_candidates = [c for c in list(dict.fromkeys(candidates)) if c]

        stub_hosts: List[str] = []
        for base_url in unique_candidates:
            url = f"{base_url}/health"
            # 1.5s was too tight for a cold mobile connection.
            res = await asyncio.to_thread(_http_get_sync, url, 6.0)
            if not (res and isinstance(res, dict)):
                continue
            if not self._serves_feature_routes(res):
                err = res.get("api_router_error") or "feature routes not mounted"
                stub_hosts.append(f"{base_url} ({err})")
                logger.warning("Skipping %s — /health answers but %s", base_url, err)
                continue

            state.is_api_online = True
            state.api_base_url = base_url
            state.models_loaded = res.get("models_loaded", {"solar": False, "wind": False})
            state.api_status_detail = ""
            logger.info("API health check succeeded on %s", base_url)
            return res

        # No usable backend. Report it instead of faking a healthy status —
        # a green indicator over a dead API is worse than an honest error.
        state.is_api_online = False
        state.models_loaded = {"solar": False, "wind": False}
        if stub_hosts:
            state.api_status_detail = "Backend reachable but incomplete: " + "; ".join(stub_hosts)
        else:
            state.api_status_detail = (
                "No backend responded. Last error: "
                f"{last_http_error or 'none recorded'}"
            )
        logger.error("API health check failed: %s", state.api_status_detail)
        return {
            "status": "offline",
            "api": "none",
            "detail": state.api_status_detail,
            "models_loaded": {"solar": False, "wind": False},
        }

    async def predict(
        self,
        irradiation: float,
        temperature: float,
        module: float,
        hour: int,
        day: int,
        month: int,
        wind_speed: float,
        direction: float,
        theoretical: float,
        load_kw: float = 0.0,
        battery_kw: float = 0.0,
        solar_cost_per_kwh: float = 0.08,
        wind_cost_per_kwh: float = 0.06,
        strategy: str = "hybrid",
    ) -> Dict[str, Any]:
        """Request POST /predict from FastAPI backend."""
        url = f"{state.api_base_url}/predict"
        payload = {
            "irradiation": irradiation,
            "temperature": temperature,
            "module": module,
            "hour": hour,
            "day": day,
            "month": month,
            "wind_speed": wind_speed,
            "direction": direction,
            "theoretical": theoretical,
            "load_kw": load_kw,
            "battery_kw": battery_kw,
            "solar_cost_per_kwh": solar_cost_per_kwh,
            "wind_cost_per_kwh": wind_cost_per_kwh,
            "strategy": strategy,
        }

        res = await asyncio.to_thread(_http_post_sync, url, payload, self.timeout)
        if res and isinstance(res, dict):
            return res

        # Fallback estimation logic
        solar_est = max(0.0, (irradiation / 1000.0) * 850.0 * (1 - 0.004 * (module - 25)))
        wind_est = max(0.0, (wind_speed / 12.0) ** 3 * 600.0) if wind_speed > 2.5 else 0.0
        total_est = solar_est + wind_est

        return {
            "solar_power": round(solar_est, 2),
            "wind_power": round(wind_est, 2),
            "total_power": round(total_est, 2),
            "recommended_source": "Solar & Wind (Fallback)" if total_est > 0 else "Grid",
            "optimal_dispatch": {
                "solar_kw": round(solar_est, 2),
                "wind_kw": round(wind_est, 2),
                "battery_kw": 0.0,
                "grid_kw": max(0.0, load_kw - total_est),
            },
            "is_fallback": True,
        }

    async def chat(self, prompt: str) -> str:
        """Request POST /chat from RAG AI Assistant."""
        url = f"{state.api_base_url}/chat"
        # ChatRequest is {query, lang}; sending {message, user_id} made every
        # request fail validation with 422, so the advisor screen only ever
        # showed the offline fallback below.
        payload = {"query": prompt, "lang": state.lang}
        res = await asyncio.to_thread(_http_post_sync, url, payload, 15.0)
        if res and isinstance(res, dict):
            return res.get("response") or res.get("reply") or "No response from assistant."

        return (
            "EcoPredict AI: Негізгі сервер уақытша офлайн. "
            "Бірақ жергілікті режимде барлық есептеулер жұмыс істейді!"
        )

    async def get_solarman_live(self) -> Dict[str, Any]:
        """Fetch Solarman live plant telemetry."""
        # /solarman/live is a GET; POSTing to it returned 405 every time, which
        # is why the live telemetry screen never populated.
        url = f"{state.api_base_url}/solarman/live?demo=true"
        res = await asyncio.to_thread(_http_get_sync, url, self.timeout)
        if res and isinstance(res, dict):
            return res
        return {
            "inverter_power_kw": 845.2,
            "daily_yield_kwh": 3420.5,
            "ambient_temp_c": 28.5,
            "status": "Normal Operation",
        }


api_client = APIClient()
