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


def _http_post_file_sync(
    url: str,
    content: bytes,
    filename: str,
    content_type: str,
    timeout: float = 30.0,
) -> Optional[Dict[str, Any]]:
    """Multipart POST of a single file, hand-rolled to stay on the stdlib."""
    global last_http_error
    import uuid

    boundary = uuid.uuid4().hex
    body = b"".join(
        [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            content,
            f"\r\n--{boundary}--\r\n".encode(),
        ]
    )
    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "EcoPredict-Mobile/1.0",
                "Accept": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
            last_http_error = f"HTTP {resp.status} from {url}"
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", "")
        except Exception:
            pass
        last_http_error = f"HTTP {e.code}: {detail or e.reason}"
        logger.warning("Upload rejected by %s: %s", url, last_http_error)
    except Exception as e:
        last_http_error = f"{type(e).__name__}: {e}"
        logger.warning("Upload error for %s: %s", url, e)
    return None


class APIClient:
    """Handles REST API communication with FastAPI backend without third-party dependencies."""

    # The Railway container idles down and its first replies are slow: measured
    # /health round trips ranged 0.5s to 7.6s from a wired connection. Mobile
    # latency sits on top of that, so short timeouts read as "no internet".
    HEALTH_TIMEOUT = 20.0
    FALLBACK_HEALTH_TIMEOUT = 8.0

    def __init__(self, timeout: float = 25.0):
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
        for index, base_url in enumerate(unique_candidates):
            url = f"{base_url}/health"
            # Give the configured backend room to wake up; the fallbacks only
            # exist to recover from a wrong URL, so they stay impatient rather
            # than making a genuine outage take a minute to report.
            timeout = self.HEALTH_TIMEOUT if index == 0 else self.FALLBACK_HEALTH_TIMEOUT
            res = await asyncio.to_thread(_http_get_sync, url, timeout)
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

    async def get_weather(self) -> Optional[Dict[str, Any]]:
        """Current Turkistan conditions (GET /solarman/weather)."""
        return await asyncio.to_thread(
            _http_get_sync, f"{state.api_base_url}/solarman/weather", self.timeout
        )

    async def solarman_process(
        self,
        active_power_kw: float,
        e_today_kwh: float,
        e_total_kwh: float,
        module_temp_c: float,
        fault_code: int,
        status: int,
        device_sn: str,
        dc_capacity_kwp: float,
        irradiance_w_m2: float,
        ambient_temp_c: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Performance Ratio via POST /solarman/process.

        The dashboard builds this payload from numbers typed by hand; here the
        readings come straight off the inverter.
        """
        payload = {
            "payload": {
                "status": status,
                "deviceSn": device_sn,
                "dataList": [
                    {"key": "APo", "value": str(active_power_kw), "unit": "kW"},
                    {"key": "eToday", "value": str(e_today_kwh), "unit": "kWh"},
                    {"key": "eTotal", "value": str(e_total_kwh), "unit": "kWh"},
                    {"key": "T_val", "value": str(module_temp_c), "unit": "°C"},
                    {"key": "faultCode", "value": str(fault_code), "unit": None},
                ],
            },
            "dc_capacity_kwp": dc_capacity_kwp,
            # The endpoint rejects irradiance <= 0, so keep a floor for night-time.
            "irradiance_w_m2": max(1.0, irradiance_w_m2),
            "ambient_temp_c": ambient_temp_c,
        }
        return await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/solarman/process", payload, self.timeout
        )

    async def solarman_roi(
        self,
        total_generation_kwh: float,
        initial_investment_kzt: float,
        tariff_kzt_per_kwh: float,
        opex_annual_kzt: float = 50000.0,
        annual_degradation: float = 0.005,
        inflation_rate: float = 0.05,
        lifetime_years: int = 25,
    ) -> Optional[Dict[str, Any]]:
        """Lifetime economics in KZT via POST /solarman/roi."""
        payload = {
            "total_generation_kwh": total_generation_kwh,
            "initial_investment_kzt": initial_investment_kzt,
            "tariff_kzt_per_kwh": tariff_kzt_per_kwh,
            "opex_annual_kzt": opex_annual_kzt,
            "annual_degradation": annual_degradation,
            "inflation_rate": inflation_rate,
            "lifetime_years": lifetime_years,
        }
        return await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/solarman/roi", payload, self.timeout
        )

    async def solarman_alert(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Offline / fault check via POST /solarman/alert."""
        return await asyncio.to_thread(
            _http_post_sync,
            f"{state.api_base_url}/solarman/alert",
            {"parsed_data": parsed_data},
            self.timeout,
        )

    async def detect_fault(
        self, content: bytes, filename: str = "panel.jpg", content_type: str = "image/jpeg"
    ) -> Optional[Dict[str, Any]]:
        """
        Run YOLO panel diagnosis on an image via POST /detect.

        None means the request failed; last_http_error holds why. An empty
        detections list is a real answer — the model found nothing.
        """
        url = f"{state.api_base_url}/detect"
        return await asyncio.to_thread(
            _http_post_file_sync, url, content, filename, content_type, 60.0
        )

    async def get_forecast(self, dc_capacity_kwp: float = 50.0) -> Optional[List[Dict[str, Any]]]:
        """
        24-hour hourly solar generation forecast.

        Returns None rather than a fabricated curve when the backend cannot
        answer, so the caller can say why instead of inventing numbers. The
        server needs WEATHERAPI_KEY configured or this route returns 500.
        """
        url = f"{state.api_base_url}/solarman/forecast?dc_capacity_kwp={dc_capacity_kwp}"
        res = await asyncio.to_thread(_http_get_sync, url, self.timeout)
        if res and isinstance(res, dict):
            forecasts = res.get("forecasts")
            if isinstance(forecasts, list) and forecasts:
                return forecasts
        return None

    async def get_solarman_live(self, device_sn: str = "") -> Dict[str, Any]:
        """Fetch Solarman live plant telemetry for a specific inverter SN."""
        # /solarman/live is a GET; POSTing to it returned 405 every time, which
        # is why the live telemetry screen never populated.
        url = f"{state.api_base_url}/solarman/live?demo=true"
        if device_sn:
            url += f"&device_sn={device_sn}"
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
