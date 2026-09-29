"""
Async REST API Client for EcoPredict AI Backend using Python standard library.
"""

import asyncio
import hashlib
import json
import logging
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

try:
    from mobile import offline_cache
    from mobile.config import DEFAULT_API_BASE
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    import offline_cache  # type: ignore # pyright: ignore[reportMissingImports]
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
            url, headers={"User-Agent": "EcoPredict-Mobile/1.0", "Accept": "application/json"}
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


def _http_post_sync(
    url: str, payload: Dict[str, Any], timeout: float = 10.0
) -> Optional[Dict[str, Any]]:
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


def _http_json_sync(
    method: str,
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 20.0,
) -> Optional[Dict[str, Any]]:
    """Any method with a JSON body and extra headers (the classroom routes)."""
    global last_http_error
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "EcoPredict-Mobile/1.0",
                "Accept": "application/json",
                **(headers or {}),
            },
            method=method,
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
            last_http_error = f"HTTP {resp.status} from {url}"
    except urllib.error.HTTPError as e:
        last_http_error = _describe_http_error(e)
        logger.warning("HTTP %s %s rejected: %s", method, url, last_http_error)
    except Exception as e:
        last_http_error = f"{type(e).__name__}: {e}"
        logger.warning("HTTP %s error for %s: %s", method, url, e)
    return None


def _student() -> Optional[Dict[str, str]]:
    """The class this phone joined, sent with every graded answer."""
    room = state.classroom
    if room and room.get("code") and room.get("token"):
        return {"class_code": room["code"], "token": room["token"]}
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
        # screen data name -> when the reply now shown was saved, while a screen
        # shows a saved reply because the server could not be reached
        self.cache_hits: Dict[str, float] = {}

    async def _with_cache(self, name: str, key: str, fetch) -> Any:
        """
        Run fetch (a blocking HTTP call) off the event loop. A good reply is
        saved on the phone under key; when there is none (offline, server
        down) the saved one is returned and cache_hits[name] says from when.
        """
        res = await asyncio.to_thread(fetch)
        if res is not None:
            offline_cache.put(key, res)
            self.cache_hits.pop(name, None)
            return res
        saved = offline_cache.get(key)
        if saved is None:
            self.cache_hits.pop(name, None)
            return None
        self.cache_hits[name] = saved[1]
        return saved[0]

    def _get(self, name: str, path: str, timeout: Optional[float] = None):
        return self._with_cache(
            name,
            f"GET {path}",
            lambda: _http_get_sync(f"{state.api_base_url}{path}", timeout or self.timeout),
        )

    def _post(self, name: str, path: str, payload: Dict[str, Any], timeout: Optional[float] = None):
        digest = hashlib.sha1(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        return self._with_cache(
            name,
            f"POST {path} {digest}",
            lambda: _http_post_sync(
                f"{state.api_base_url}{path}", payload, timeout or self.timeout
            ),
        )

    def cache_note(self, name: str) -> str:
        """ "No connection — saved data from 14:30" while name shows a saved reply, else ""."""
        saved_at = self.cache_hits.get(name)
        if saved_at is None:
            return ""
        t = time.localtime(saved_at)
        same_day = time.strftime("%Y%m%d", t) == time.strftime("%Y%m%d")
        when = time.strftime("%H:%M" if same_day else "%d.%m %H:%M", t)
        return state.text("offline_note", when=when)

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
                f"No backend responded. Last error: {last_http_error or 'none recorded'}"
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

        res = await self._post("predict", "/predict", payload)
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
        return await self._get("weather", "/solarman/weather")

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

    async def get_forecast(self, dc_capacity_kwp: Optional[float] = None) -> Optional[List[Dict[str, Any]]]:
        """
        24-hour hourly solar generation forecast.

        Returns None rather than a fabricated curve when the backend cannot
        answer, so the caller can say why instead of inventing numbers. The
        server needs WEATHERAPI_KEY configured or this route returns 500.

        Without dc_capacity_kwp the server scales to the station's rated
        power; this used to send 50 kWp whatever the station was.
        forecast_meta keeps what the server says about the forecast itself:
        the capacity, where the sunlight came from, and the error measured on
        the station (accuracy, None until measured).
        """
        path = "/solarman/forecast"
        if dc_capacity_kwp:
            path += f"?dc_capacity_kwp={dc_capacity_kwp}"
        res = await self._get("forecast", path)
        if res and isinstance(res, dict):
            self.forecast_meta = {
                k: res.get(k) for k in ("dc_capacity_kwp", "irradiance_source", "accuracy")
            }
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
        path = "/solarman/live?demo=true"
        if device_sn:
            path += f"&device_sn={device_sn}"
        res = await self._get("live", path)
        return res if isinstance(res, dict) else None

    @staticmethod
    def is_demo(live: Optional[Dict[str, Any]]) -> bool:
        """Whether a /solarman/live reply is the server's sample, not the inverter."""
        return str((live or {}).get("source", "")).startswith("demo")

    async def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Model metrics and feature importances (GET /metrics)."""
        res = await self._get("metrics", "/metrics")
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
        res = await self._post("impact", "/sustainability/impact", payload)
        return res if isinstance(res, dict) else None

    # ---- education labs (api/labs.py) ----------------------------------
    async def labs_list(self) -> Optional[List[Dict[str, Any]]]:
        """The 12 labs (GET /labs)."""
        res = await self._get("labs", "/labs")
        labs = res.get("labs") if isinstance(res, dict) else None
        return labs if isinstance(labs, list) else None

    async def lab_detail(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """Parameters, theory (kk/en) and 3D viewer path of one lab (GET /labs/{id})."""
        res = await self._get(f"lab:{lab_id}", f"/labs/{lab_id}")
        return res if isinstance(res, dict) else None

    async def lab_run(self, lab_id: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run a lab on the server (POST /labs/{id}/run): metrics, charts, notes."""
        res = await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/labs/{lab_id}/run", {"params": params}, 60.0
        )
        return res if isinstance(res, dict) else None

    async def lab_test(self, lab_id: str) -> Optional[Dict[str, Any]]:
        """The lab's final test without answers (GET /labs/{id}/test)."""
        res = await self._get(f"test:{lab_id}", f"/labs/{lab_id}/test?lang={state.lang}")
        return res if isinstance(res, dict) else None

    async def lab_grade(self, lab_id: str, answers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Grade the test on the server (POST /labs/{id}/test/grade)."""
        res = await asyncio.to_thread(
            _http_post_sync,
            f"{state.api_base_url}/labs/{lab_id}/test/grade",
            {"answers": answers, "lang": state.lang, "student": _student()},
            60.0,
        )
        return res if isinstance(res, dict) else None

    async def lab_task_check(
        self,
        lab_id: str,
        task_id: str,
        number: Optional[float] = None,
        choice_index: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Check one practice task (POST /labs/{id}/tasks/{task}/check)."""
        res = await asyncio.to_thread(
            _http_post_sync,
            f"{state.api_base_url}/labs/{lab_id}/tasks/{task_id}/check",
            {"number": number, "choice_index": choice_index, "student": _student()},
            self.timeout,
        )
        return res if isinstance(res, dict) else None

    async def lab_report(self, lab_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """The student's report, built on the server (POST /labs/{id}/report)."""
        res = await asyncio.to_thread(
            _http_post_sync, f"{state.api_base_url}/labs/{lab_id}/report", payload, 60.0
        )
        return res if isinstance(res, dict) else None

    # ---- Learn lessons and quizzes (api/learn.py) -----------------------
    async def learn_lessons(self) -> Optional[List[Dict[str, Any]]]:
        """The lesson cards (GET /learn/lessons)."""
        res = await self._get("lessons", f"/learn/lessons?lang={state.lang}")
        lessons = res.get("lessons") if isinstance(res, dict) else None
        return lessons if isinstance(lessons, list) else None

    async def learn_lesson(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        """One lesson as Markdown, its quiz id and related labs (GET /learn/lessons/{id})."""
        res = await self._get(
            f"lesson:{lesson_id}", f"/learn/lessons/{lesson_id}?lang={state.lang}"
        )
        return res if isinstance(res, dict) else None

    async def learn_quiz(self, quiz_id: str) -> Optional[Dict[str, Any]]:
        """A lesson's quiz without the answers (GET /learn/quizzes/{id})."""
        res = await self._get(f"quiz:{quiz_id}", f"/learn/quizzes/{quiz_id}?lang={state.lang}")
        return res if isinstance(res, dict) else None

    async def learn_grade(self, quiz_id: str, answers: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Grade a quiz on the server (POST /learn/quizzes/{id}/grade)."""
        res = await asyncio.to_thread(
            _http_post_sync,
            f"{state.api_base_url}/learn/quizzes/{quiz_id}/grade",
            {"answers": answers, "lang": state.lang, "student": _student()},
            self.timeout,
        )
        return res if isinstance(res, dict) else None

    @staticmethod
    def lab_viewer_url(viewer_path: str) -> str:
        """The 3D lab page on the API server; it calls back to the same server."""
        base = state.api_base_url
        url = f"{base}{viewer_path}?lang={state.lang}&api={urllib.parse.quote(base, safe='')}"
        student = _student()
        if student:  # the viewer sends it with the test, so the class sees the result
            url += "&" + urllib.parse.urlencode(
                {"class": student["class_code"], "token": student["token"]}
            )
        return url

    # ---- classes (api/classroom.py) ---------------------------------------
    async def classroom_create(self, name: str) -> Optional[Dict[str, Any]]:
        """A new class: its code for the students and the teacher key."""
        return await asyncio.to_thread(
            _http_json_sync, "POST", f"{state.api_base_url}/classes", {"name": name}
        )

    async def classroom_join(self, code: str, name: str) -> Optional[Dict[str, Any]]:
        """Join a class with its code; returns the class name and this phone's token."""
        code = urllib.parse.quote(code.strip().upper(), safe="")
        return await asyncio.to_thread(
            _http_json_sync, "POST", f"{state.api_base_url}/classes/{code}/join", {"name": name}
        )

    async def classroom_results(self, code: str, key: str) -> Optional[Dict[str, Any]]:
        """The class table (teacher key required)."""
        code = urllib.parse.quote(code.strip().upper(), safe="")
        return await asyncio.to_thread(
            _http_json_sync,
            "GET",
            f"{state.api_base_url}/classes/{code}/results",
            None,
            {"X-Teacher-Key": key},
        )

    async def classroom_remove(
        self, code: str, key: str, student_id: int
    ) -> Optional[Dict[str, Any]]:
        code = urllib.parse.quote(code.strip().upper(), safe="")
        return await asyncio.to_thread(
            _http_json_sync,
            "DELETE",
            f"{state.api_base_url}/classes/{code}/students/{int(student_id)}",
            None,
            {"X-Teacher-Key": key},
        )


api_client = APIClient()
