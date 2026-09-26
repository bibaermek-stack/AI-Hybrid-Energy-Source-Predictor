"""
Async REST API Client for EcoPredict AI Backend using Python standard library.
"""

import asyncio
import json
import logging
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

try:
    from mobile.config import DEFAULT_API_BASE
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    from config import DEFAULT_API_BASE  # type: ignore # pyright: ignore[reportMissingImports]
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


def _describe_http_error(e: urllib.error.HTTPError) -> str:
    """HTTP status plus FastAPI's `detail`, so screens can say why a call failed."""
    detail: Any = ""
    try:
        detail = json.loads(e.read().decode("utf-8")).get("detail", "")
    except Exception:
        pass
    if isinstance(detail, list):  # 422 validation errors
        detail = "; ".join(str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail)
    return f"HTTP {e.code}: {detail or e.reason}"


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
    except urllib.error.HTTPError as e:
        last_http_error = _describe_http_error(e)
        logger.warning("HTTP GET %s rejected: %s", url, last_http_error)
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
    except urllib.error.HTTPError as e:
        last_http_error = _describe_http_error(e)
        logger.warning("HTTP POST %s rejected: %s", url, last_http_error)
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
        last_http_error = _describe_http_error(e)
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
        """Confirm the backend serves the feature routes, not just /health."""
        # Only this repository's Railway service. The app used to fall through
        # to services deployed from other repositories (ecopradict-ai,
        # ecopredict.kz) and silently switch to whichever answered first.
        candidates = [state.api_base_url.strip().rstrip("/"), DEFAULT_API_BASE]
        unique_candidates = [c for c in list(dict.fromkeys(candidates)) if c]

        stub_hosts: List[str] = []
        for index, base_url in enumerate(unique_candidates):
            url = f"{base_url}/health"
            # Give the configured backend room to wake up; the default is only
            # a fallback for a mistyped URL, so it stays impatient rather than
            # making a genuine outage take much longer to report.
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
    ) -> Optional[Dict[str, Any]]:
        """ML prediction + dispatch via POST /predict (PredictionResponse)."""
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
        # None when the backend cannot answer (reason in last_http_error). This
        # used to return a phone-side guess shaped like a real reply, with an
        # optimal_dispatch block /predict never sends — the screens showed it
        # as model output.
        return res if isinstance(res, dict) else None

    async def chat(self, prompt: str) -> Optional[str]:
        """
        Advisor reply via POST /chat, or None if the request failed (reason in
        last_http_error). It used to return a canned line in the advisor's
        voice claiming "local mode" still worked — there is no local mode.
        """
        url = f"{state.api_base_url}/chat"
        # ChatRequest is {query, lang}; sending {message, user_id} made every
        # request fail validation with 422.
        payload = {"query": prompt, "lang": state.lang}
        res = await asyncio.to_thread(_http_post_sync, url, payload, 30.0)
        if isinstance(res, dict):
            return res.get("response") or res.get("reply") or ""
        return None

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

    async def get_solarman_live(self, device_sn: str = "") -> Optional[Dict[str, Any]]:
        """
        Solarman telemetry for one inverter SN, or None if the request failed.

        demo=true lets the server fall back to its sample payload when it has
        no Solarman credentials. That reply carries source == "demo", and every
        screen showing it must say so (see is_demo).
        """
        # /solarman/live is a GET; POSTing to it returned 405 every time, which
        # is why the live telemetry screen never populated.
        url = f"{state.api_base_url}/solarman/live?demo=true"
        if device_sn:
            url += f"&device_sn={device_sn}"
        res = await asyncio.to_thread(_http_get_sync, url, self.timeout)
        return res if isinstance(res, dict) else None

    @staticmethod
    def is_demo(live: Optional[Dict[str, Any]]) -> bool:
        """Whether a /solarman/live reply is the server's sample, not the inverter."""
        return str((live or {}).get("source", "")).startswith("demo")

    async def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Model metrics and feature importances (GET /metrics)."""
        res = await asyncio.to_thread(_http_get_sync, f"{state.api_base_url}/metrics", self.timeout)
        return res if isinstance(res, dict) else None

    async def sustainability_impact(
        self,
        renewable_kwh: float,
        grid_import_kwh: float,
        grid_factor_kg_per_kwh: float = 0.45,
    ) -> Optional[Dict[str, Any]]:
        """CO₂ avoided and equivalents (POST /sustainability/impact)."""
        payload = {
            "renewable_kwh": renewable_kwh,
            "grid_import_kwh": grid_import_kwh,
            "grid_factor_kg_per_kwh": grid_factor_kg_per_kwh,
            "lang": state.lang,
        }
        res = await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/sustainability/impact", payload, self.timeout
        )
        return res if isinstance(res, dict) else None

    # ---- education labs (api/labs.py) ----------------------------------
    async def labs_list(self) -> Optional[List[Dict[str, Any]]]:
        """The 12 labs (GET /labs)."""
        res = await asyncio.to_thread(_http_get_sync, f"{state.api_base_url}/labs", self.timeout)
        labs = res.get("labs") if isinstance(res, dict) else None
        return labs if isinstance(labs, list) else None

    async def lab_detail(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """Parameters, theory (kk/en) and 3D viewer path of one lab (GET /labs/{id})."""
        res = await asyncio.to_thread(_http_get_sync, f"{state.api_base_url}/labs/{lab_id}", self.timeout)
        return res if isinstance(res, dict) else None

    async def lab_run(self, lab_id: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a lab on the server (POST /labs/{id}/run): metrics, charts, notes."""
        res = await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/labs/{lab_id}/run", {"params": params}, 60.0
        )
        return res if isinstance(res, dict) else None

    async def lab_test(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """The lab's final test without answers (GET /labs/{id}/test)."""
        res = await asyncio.to_thread(
            _http_get_sync, f"{state.api_base_url}/labs/{lab_id}/test?lang={state.lang}", self.timeout
        )
        return res if isinstance(res, dict) else None

    async def lab_grade(self, lab_id: str, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Grade the test on the server (POST /labs/{id}/test/grade)."""
        res = await asyncio.to_thread(
            _http_post_sync,
            f"{state.api_base_url}/labs/{lab_id}/test/grade",
            {"answers": answers, "lang": state.lang},
            60.0,
        )
        return res if isinstance(res, dict) else None

    @staticmethod
    def lab_viewer_url(viewer_path: str) -> str:
        """The 3D lab page on the API server; it calls back to the same server."""
        base = state.api_base_url
        return f"{base}{viewer_path}?lang={state.lang}&api={urllib.parse.quote(base, safe='')}"


api_client = APIClient()
