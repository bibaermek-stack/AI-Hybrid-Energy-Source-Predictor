"""
Solarman OpenAPI client — live + historical device data.

Auth: POST {base}/account/v1.0/token?appId=...
Live: POST {base}/device/v1.0/currentData
History: POST {base}/device/v1.0/historical

Credentials via env:
  SOLARMAN_APP_ID, SOLARMAN_APP_SECRET, SOLARMAN_EMAIL, SOLARMAN_PASSWORD
  SOLARMAN_DEVICE_SN (default 2501221272)
  SOLARMAN_DEVICE_ID (optional numeric)
  SOLARMAN_BASE_URL (default https://globalapi.solarmanpv.com)
  SOLARMAN_PASSWORD_SHA256=1 if password is already hex sha256
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_BASE = "https://globalapi.solarmanpv.com"
DEFAULT_SN = "2501221272"

# Runtime credentials set via API/UI (override env for this process)
_RUNTIME_CREDS: dict[str, str] = {}


def set_runtime_credentials(
    app_id: str = "",
    app_secret: str = "",
    email: str = "",
    password: str = "",
    device_sn: str = "",
    device_id: str = "",
    base_url: str = "",
    password_is_sha256: bool = False,
) -> dict:
    """
    Store OpenAPI credentials in process memory.

    Deliberately does *not* mirror into os.environ: that mutated global state for the
    whole process and leaked the password into the environment of anything spawned
    afterwards. SolarmanClient reads _RUNTIME_CREDS first, so the override still wins
    over .env.
    """
    global _RUNTIME_CREDS
    if app_id:
        _RUNTIME_CREDS["SOLARMAN_APP_ID"] = app_id.strip()
    if app_secret:
        _RUNTIME_CREDS["SOLARMAN_APP_SECRET"] = app_secret.strip()
    if email:
        _RUNTIME_CREDS["SOLARMAN_EMAIL"] = email.strip()
    if password:
        _RUNTIME_CREDS["SOLARMAN_PASSWORD"] = password.strip()
    if device_sn:
        _RUNTIME_CREDS["SOLARMAN_DEVICE_SN"] = device_sn.strip()
    if device_id:
        _RUNTIME_CREDS["SOLARMAN_DEVICE_ID"] = str(device_id).strip()
    if base_url:
        _RUNTIME_CREDS["SOLARMAN_BASE_URL"] = base_url.strip().rstrip("/")
    if password_is_sha256:
        _RUNTIME_CREDS["SOLARMAN_PASSWORD_SHA256"] = "1"
    return credentials_status()


def credentials_status() -> dict:
    c = SolarmanClient()
    return {
        "credentials_configured": c.credentials_configured,
        "device_sn": c.device_sn,
        "device_id": c.device_id,
        "base_url": c.base_url,
        "app_id_set": bool(c.app_id),
        "email_set": bool(c.email),
        "password_set": bool(c.password),
        "app_secret_set": bool(c.app_secret),
        "source": "runtime" if _RUNTIME_CREDS.get("SOLARMAN_APP_ID") else "env",
    }


class SolarmanAPIError(RuntimeError):
    pass


class SolarmanClient:
    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        email: str | None = None,
        password: str | None = None,
        base_url: str | None = None,
        device_sn: str | None = None,
        device_id: int | str | None = None,
    ):
        def _g(key: str, default: str = "") -> str:
            return (
                _RUNTIME_CREDS.get(key)
                or os.getenv(key, default)
                or default
            ).strip()

        self.app_id = (app_id or _g("SOLARMAN_APP_ID")).strip()
        self.app_secret = (app_secret or _g("SOLARMAN_APP_SECRET")).strip()
        self.email = (email or _g("SOLARMAN_EMAIL")).strip()
        self.password = (password or _g("SOLARMAN_PASSWORD")).strip()
        self.base_url = (base_url or _g("SOLARMAN_BASE_URL", DEFAULT_BASE) or DEFAULT_BASE).rstrip("/")
        self.device_sn = (device_sn or _g("SOLARMAN_DEVICE_SN", DEFAULT_SN) or DEFAULT_SN).strip()
        raw_id = device_id if device_id is not None else _g("SOLARMAN_DEVICE_ID")
        self.device_id = int(raw_id) if str(raw_id).isdigit() else None

        self._access_token: str | None = None
        self._token_type: str = "bearer"
        self._token_expires_at: float = 0.0

    @property
    def credentials_configured(self) -> bool:
        return bool(self.app_id and self.app_secret and self.email and self.password)

    def _password_hash(self) -> str:
        """Solarman expects SHA-256 hex of the plain password (unless already hashed)."""
        flag = _RUNTIME_CREDS.get("SOLARMAN_PASSWORD_SHA256") or os.getenv(
            "SOLARMAN_PASSWORD_SHA256", ""
        )
        if flag.lower() in ("1", "true", "yes"):
            return self.password
        # If looks like sha256 hex already
        if len(self.password) == 64 and all(c in "0123456789abcdef" for c in self.password.lower()):
            return self.password
        return hashlib.sha256(self.password.encode("utf-8")).hexdigest()

    def authenticate(self, force: bool = False) -> str:
        if not self.credentials_configured:
            raise SolarmanAPIError(
                "Solarman credentials missing. Set SOLARMAN_APP_ID, SOLARMAN_APP_SECRET, "
                "SOLARMAN_EMAIL, SOLARMAN_PASSWORD in .env"
            )
        if (
            not force
            and self._access_token
            and time.time() < self._token_expires_at - 60
        ):
            return self._access_token

        url = f"{self.base_url}/account/v1.0/token"
        params = {"appId": self.app_id}
        body = {
            "appSecret": self.app_secret,
            "email": self.email,
            "password": self._password_hash(),
        }
        try:
            resp = requests.post(url, params=params, json=body, timeout=4)
            data = resp.json() if resp.content else {}
        except Exception as e:
            raise SolarmanAPIError(f"Token request failed: {e}") from e

        if resp.status_code >= 400 or not data.get("access_token"):
            raise SolarmanAPIError(
                f"Auth failed ({resp.status_code}): {data.get('msg') or data.get('message') or data}"
            )

        self._access_token = data["access_token"]
        self._token_type = data.get("token_type", "bearer")
        # expires_in often seconds
        expires_in = float(data.get("expires_in", 3600) or 3600)
        self._token_expires_at = time.time() + expires_in
        return self._access_token

    def _headers(self) -> dict[str, str]:
        token = self.authenticate()
        return {
            "Authorization": f"{self._token_type} {token}",
            "Content-Type": "application/json",
        }

    def list_stations(self) -> list[dict]:
        url = f"{self.base_url}/station/v1.0/list"
        resp = requests.post(url, headers=self._headers(), json={}, timeout=4)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            raise SolarmanAPIError(f"station list failed: {data}")
        return data.get("stationList") or data.get("station_list") or []

    def list_devices(self, station_id: int | str) -> list[dict]:
        url = f"{self.base_url}/station/v1.0/device"
        resp = requests.post(
            url, headers=self._headers(), json={"stationId": station_id}, timeout=4
        )
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            raise SolarmanAPIError(f"station device failed: {data}")
        return data.get("deviceListItems") or data.get("deviceList") or []

    def resolve_device(self) -> tuple[int | None, str]:
        """Return (deviceId, deviceSn), resolving id by SN if needed."""
        if self.device_id and self.device_sn:
            return self.device_id, self.device_sn

        stations = self.list_stations()
        for st in stations:
            sid = st.get("id") or st.get("stationId")
            if sid is None:
                continue
            for dev in self.list_devices(sid):
                sn = str(dev.get("deviceSn") or dev.get("device_sn") or "")
                did = dev.get("deviceId") or dev.get("device_id")
                if sn == self.device_sn or (not self.device_sn and did):
                    if did is not None:
                        self.device_id = int(did)
                    if sn:
                        self.device_sn = sn
                    return self.device_id, self.device_sn

        if self.device_sn:
            return self.device_id, self.device_sn
        raise SolarmanAPIError(f"Device SN {self.device_sn} not found under account stations")

    def get_current_data(self, device_id: int | None = None, device_sn: str | None = None) -> dict:
        did = device_id if device_id is not None else self.device_id
        sn = device_sn or self.device_sn
        if did is None:
            did, sn = self.resolve_device()

        url = f"{self.base_url}/device/v1.0/currentData"
        body: dict[str, Any] = {}
        if did is not None:
            body["deviceId"] = did
        if sn:
            body["deviceSn"] = sn

        resp = requests.post(url, headers=self._headers(), json=body, timeout=4)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            raise SolarmanAPIError(f"currentData failed: {data}")
        return data

    def get_historical(
        self,
        start_time: str,
        end_time: str,
        time_type: int = 1,
        device_id: int | None = None,
        device_sn: str | None = None,
    ) -> dict:
        """
        time_type: 1=day (HH), 2=month days, 3=year months, 4=years
        start/end format depends on type, e.g. day: '2026-07-10'
        """
        did = device_id if device_id is not None else self.device_id
        sn = device_sn or self.device_sn
        if did is None:
            did, sn = self.resolve_device()

        url = f"{self.base_url}/device/v1.0/historical"
        body: dict[str, Any] = {
            "startTime": start_time,
            "endTime": end_time,
            "timeType": time_type,
        }
        if did is not None:
            body["deviceId"] = did
        if sn:
            body["deviceSn"] = sn

        resp = requests.post(url, headers=self._headers(), json=body, timeout=40)
        data = resp.json() if resp.content else {}
        if resp.status_code >= 400:
            raise SolarmanAPIError(f"historical failed: {data}")
        return data


# ---------------------------------------------------------------------------
# Parsing helpers — map Solarman keys to UI structure (screenshot layout)
# ---------------------------------------------------------------------------

# Common Solarman key aliases (incl. live keys from SN 2501221272 / Deye)
_KEY_ALIASES = {
    "PV1_V": ["DV1", "Vpv1", "PV1", "pv1_v", "U_pv1"],
    "PV1_I": ["DC1", "Ipv1", "pv1_i", "I_pv1"],
    "PV1_P": ["DP1", "Ppv1", "pv1_p", "P_pv1"],
    "PV2_V": ["DV2", "Vpv2", "PV2", "pv2_v", "U_pv2"],
    "PV2_I": ["DC2", "Ipv2", "pv2_i", "I_pv2"],
    "PV2_P": ["DP2", "Ppv2", "pv2_p", "P_pv2"],
    "PV3_V": ["DV3", "Vpv3", "pv3_v"],
    "PV3_I": ["DC3", "Ipv3", "pv3_i"],
    "PV3_P": ["DP3", "Ppv3", "pv3_p"],
    "PV4_V": ["DV4"],
    "PV4_I": ["DC4"],
    "PV4_P": ["DP4"],
    "PV5_V": ["DV5"],
    "PV5_I": ["DC5"],
    "PV5_P": ["DP5"],
    "PV6_V": ["DV6"],
    "PV6_I": ["DC6"],
    "PV6_P": ["DP6"],
    "AC_R_V": ["AV1", "Va", "Vr", "Vac1", "U_a"],
    "AC_R_I": ["AC1", "Ia", "Ir", "Iac1", "I_a"],
    "AC_R_F": ["A_Fo1", "Fac", "F_ac", "grid_freq", "F"],
    "AC_S_V": ["AV2", "Vb", "Vs", "Vac2", "U_b"],
    "AC_S_I": ["AC2", "Ib", "Is", "Iac2", "I_b"],
    "AC_T_V": ["AV3", "Vc", "Vt", "Vac3", "U_c"],
    "AC_T_I": ["AC3", "Ic", "It", "Iac3", "I_c"],
    "AC_R_P": ["INV_O_P_L1"],
    "AC_S_P": ["INV_O_P_L2"],
    "AC_T_P": ["INV_O_P_L3"],
    "APo": ["APo_t1", "APo", "pac", "Pac", "P_ac", "active_power", "E_Puse_t1"],
    "eToday": ["Etdy_ge1", "Etdy_use1", "eToday", "Etoday", "E_day", "daily_energy"],
    "eTotal": ["Et_ge0", "Et_use1", "eTotal", "Etotal", "E_total", "total_energy"],
    "T_val": ["IGBT_T1", "T_AC_RDT1", "T_val", "Tinv", "temperature", "temp"],
    "rated_w": ["Pr1"],
    "sn": ["SN1", "deviceSn"],
    "inverter_type": ["I_T"],
    "product_type": ["PM1"],
    "general_settings": ["GESET"],
    "country": ["SS_CY1"],
    "mppt_no": ["MPPTn1"],
    "protocol": ["PTCv1"],
    "main": ["MAIN"],
    "hmi": ["HMI"],
    "sw1": ["SWctrl_v1"],
    "sw2": ["SWctrl_v2"],
    "comm_cpu": ["COMM_CPU_SWv1"],
    "arc_fw": ["A_B_F_V"],
    "grid_status": ["INV_ST1"],
}


def flatten_datalist(payload: dict) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for item in payload.get("dataList") or []:
        key = item.get("key")
        if key is None:
            continue
        val = item.get("value")
        unit = item.get("unit")
        try:
            if val is not None and val != "":
                if isinstance(val, str) and ("." in val or "e" in val.lower()):
                    num = float(val)
                elif isinstance(val, str) and val.lstrip("-").isdigit():
                    # Keep codes with leading zeros as strings (e.g. HMI "0257")
                    if len(val) > 1 and val.startswith("0"):
                        num = val
                    else:
                        num = int(val)
                else:
                    num = float(val) if not isinstance(val, (int, float)) else val
            else:
                num = None
        except (TypeError, ValueError):
            num = val
        out[str(key)] = num
        if unit:
            out[f"{key}__unit"] = unit
    # deviceState is the live online flag on newer Solarman payloads
    out["deviceStatus"] = payload.get("deviceState", payload.get("status"))
    out["deviceId"] = payload.get("deviceId")
    out["deviceSn"] = payload.get("deviceSn")
    out["collectionTime"] = payload.get("collectionTime") or payload.get("time")
    return out


def _pick(flat: dict, logical: str, default: Any = 0.0) -> Any:
    for k in _KEY_ALIASES.get(logical, [logical]):
        if k in flat and flat[k] is not None:
            return flat[k]
    if logical in flat and flat[logical] is not None:
        return flat[logical]
    return default


def _to_kw(value: Any, unit_hint: str | None = None) -> float:
    """Convert Solarman power (often W) to kW."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return 0.0
    u = (unit_hint or "").strip().lower()
    if u in ("w", "watt", "watts"):
        return v / 1000.0
    if u in ("kw", "kwh"):  # kWh not power but leave
        return v
    # Heuristic: inverter string power > 100 is almost always Watts
    if abs(v) >= 100:
        return v / 1000.0
    return v


def build_device_dashboard(payload: dict, meta: dict | None = None) -> dict:
    """
    Structure matching Solarman Device Data page (screenshot).
    """
    flat = flatten_datalist(payload)
    meta = meta or {}

    def fnum(v, nd=2):
        try:
            return round(float(v), nd)
        except (TypeError, ValueError):
            return 0.0

    def power_kw_from_key(logical: str) -> float:
        """Read power field and convert W→kW using unit suffix if present."""
        for k in _KEY_ALIASES.get(logical, [logical]):
            if k in flat and flat[k] is not None:
                return round(_to_kw(flat[k], flat.get(f"{k}__unit")), 5)
        return 0.0

    pv_rows = []
    for i in range(1, 7):
        v = fnum(_pick(flat, f"PV{i}_V", 0))
        c = fnum(_pick(flat, f"PV{i}_I", 0))
        p = power_kw_from_key(f"PV{i}_P")
        if p == 0 and v and c:
            p = fnum(v * c / 1000.0, 5)  # V*A → W → kW
        pv_rows.append({"mppt": f"PV{i}", "voltage_v": v, "current_a": c, "power_kw": p})

    ac_rows = [
        {
            "phase": "R",
            "voltage_v": fnum(_pick(flat, "AC_R_V", 0)),
            "current_a": fnum(_pick(flat, "AC_R_I", 0)),
            "frequency_hz": fnum(_pick(flat, "AC_R_F", 0), 2),
            "power_kw": power_kw_from_key("AC_R_P"),
        },
        {
            "phase": "S",
            "voltage_v": fnum(_pick(flat, "AC_S_V", 0)),
            "current_a": fnum(_pick(flat, "AC_S_I", 0)),
            "frequency_hz": None,
            "power_kw": power_kw_from_key("AC_S_P"),
        },
        {
            "phase": "T",
            "voltage_v": fnum(_pick(flat, "AC_T_V", 0)),
            "current_a": fnum(_pick(flat, "AC_T_I", 0)),
            "frequency_hz": None,
            "power_kw": power_kw_from_key("AC_T_P"),
        },
    ]

    dc_total = sum(r["power_kw"] for r in pv_rows)
    ac_power = power_kw_from_key("APo")
    if ac_power == 0:
        phase_sum = sum(r.get("power_kw") or 0 for r in ac_rows)
        if phase_sum > 0:
            ac_power = round(phase_sum, 3)
        else:
            vr, ir = ac_rows[0]["voltage_v"], ac_rows[0]["current_a"]
            if vr and ir:
                ac_power = fnum(1.732 * vr * ir / 1000.0, 3)

    sn = str(_pick(flat, "sn", None) or flat.get("deviceSn") or meta.get("device_sn") or DEFAULT_SN)
    rated_w = _pick(flat, "rated_w", None)
    if rated_w is not None:
        rated_kw = _to_kw(rated_w, flat.get("Pr1__unit") or "W")
    else:
        rated_kw = float(meta.get("rated_power_kw", 25))

    inv_type = _pick(flat, "inverter_type", None) or meta.get("inverter_type", "String three Inverter")
    product_type = str(_pick(flat, "product_type", meta.get("product_type", "2")))
    general_settings = str(_pick(flat, "general_settings", meta.get("general_settings", "3,5,7")))
    country = str(_pick(flat, "country", meta.get("country", "2")))
    try:
        mppt_no = int(_pick(flat, "mppt_no", meta.get("mppt_no", 2)))
    except (TypeError, ValueError):
        mppt_no = 2

    grid_status = _pick(flat, "grid_status", None)

    return {
        "source": meta.get("source", "api"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "basic": {
            "sn": sn,
            "inverter_type": inv_type,
            "product_type": product_type,
            "general_settings": general_settings,
            "production_compliance_country": country,
            "rated_power_kw": round(float(rated_kw), 2),
            "mppt_no": mppt_no,
            "device_id": flat.get("deviceId") or meta.get("device_id"),
            "status": flat.get("deviceStatus"),
            "grid_status": grid_status,
        },
        "version": {
            "protocol_version": str(_pick(flat, "protocol", meta.get("protocol_version", "—"))),
            "main": str(_pick(flat, "main", meta.get("main", "—"))),
            "hmi": str(_pick(flat, "hmi", meta.get("hmi", "—"))),
            "control_sw_v1": str(_pick(flat, "sw1", meta.get("control_sw_v1", "—"))),
            "control_sw_v2": str(_pick(flat, "sw2", meta.get("control_sw_v2", "—"))),
            "comm_cpu_sw": str(_pick(flat, "comm_cpu", meta.get("comm_cpu_sw", "—"))),
            "arc_board_fw": str(_pick(flat, "arc_fw", meta.get("arc_board_fw", "—"))),
        },
        "generation": {
            "dc": pv_rows,
            "ac": ac_rows,
            "dc_total_kw": fnum(dc_total, 3),
            "ac_active_power_kw": fnum(ac_power, 3),
            "e_today_kwh": fnum(_pick(flat, "eToday", 0), 2),
            "e_total_kwh": fnum(_pick(flat, "eTotal", 0), 2),
            "temperature_c": fnum(_pick(flat, "T_val", 0), 1),
        },
        "raw_flat": flat,
        "raw_payload": payload,
    }


def demo_current_payload() -> dict:
    """Realistic payload matching user's Solarman screenshot (SN 2501221272)."""
    return {
        "code": None,
        "msg": None,
        "success": True,
        "requestId": "demo",
        "deviceId": 2501221272,
        "deviceSn": "2501221272",
        "deviceType": "INVERTER",
        "status": 1,
        "collectionTime": int(time.time()),
        "dataList": [
            {"key": "DV1", "value": "451.90", "unit": "V"},
            {"key": "DC1", "value": "10.50", "unit": "A"},
            {"key": "DP1", "value": "4.74495", "unit": "kW"},
            {"key": "DV2", "value": "388.40", "unit": "V"},
            {"key": "DC2", "value": "5.40", "unit": "A"},
            {"key": "DP2", "value": "2.09736", "unit": "kW"},
            {"key": "DV3", "value": "0.00", "unit": "V"},
            {"key": "DC3", "value": "0.00", "unit": "A"},
            {"key": "DP3", "value": "0", "unit": "W"},
            {"key": "AV1", "value": "226.50", "unit": "V"},
            {"key": "AC1", "value": "9.80", "unit": "A"},
            {"key": "A_Fo1", "value": "50.00", "unit": "Hz"},
            {"key": "AV2", "value": "224.10", "unit": "V"},
            {"key": "AC2", "value": "10.10", "unit": "A"},
            {"key": "AV3", "value": "225.00", "unit": "V"},
            {"key": "AC3", "value": "9.90", "unit": "A"},
            {"key": "APo", "value": "6.65", "unit": "kW"},
            {"key": "eToday", "value": "42.80", "unit": "kWh"},
            {"key": "eTotal", "value": "12850.5", "unit": "kWh"},
            {"key": "T_val", "value": "48.0", "unit": "℃"},
            {"key": "faultCode", "value": "0", "unit": None},
        ],
    }


def demo_history_series(hours: int = 24) -> list[dict]:
    """Synthetic hourly series for charts when API history unavailable."""
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    rows = []
    for h in range(hours, 0, -1):
        t = now - timedelta(hours=h)
        hour = t.hour
        if 6 <= hour <= 19:
            # simple solar curve
            x = (hour - 6) / 13.0
            shape = max(0.0, 1.0 - abs(x - 0.5) * 2.0)
            p_dc = 6.8 * shape * (0.85 + 0.15 * (1 if hour % 2 == 0 else 0.7))
        else:
            p_dc = 0.0
        p_ac = p_dc * 0.96
        rows.append(
            {
                "time": t.strftime("%Y-%m-%d %H:%M"),
                "dc_power_kw": round(p_dc, 3),
                "ac_power_kw": round(p_ac, 3),
                "pv1_power_kw": round(p_dc * 0.69, 3),
                "pv2_power_kw": round(p_dc * 0.31, 3),
                "e_today_kwh": round(sum(r["ac_power_kw"] for r in rows) if rows else p_ac, 2),
            }
        )
    # fix e_today cumulative
    cum = 0.0
    for r in rows:
        cum += r["ac_power_kw"]
        r["e_today_kwh"] = round(cum, 2)
    return rows


def _fmt_collect_time(t: Any) -> str:
    """Unix seconds/ms or ISO → 'YYYY-MM-DD HH:MM'."""
    if t is None:
        return ""
    try:
        if isinstance(t, str) and t.isdigit():
            t = int(t)
        if isinstance(t, (int, float)):
            ts = float(t)
            if ts > 1e12:
                ts /= 1000.0
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except Exception:
        pass
    return str(t)


def parse_historical_for_charts(hist: dict) -> list[dict]:
    """Parse Solarman historical paramDataList into chart rows (power in kW)."""
    rows: list[dict] = []
    candidates = (
        hist.get("paramDataList")
        or hist.get("dataList")
        or hist.get("stationDataItems")
        or hist.get("list")
        or []
    )
    if not isinstance(candidates, list):
        return rows

    for item in candidates:
        if not isinstance(item, dict):
            continue
        t_raw = item.get("collectTime") or item.get("time") or item.get("dateTime") or item.get("date")
        t = _fmt_collect_time(t_raw)
        nested = item.get("dataList") or []
        flat = flatten_datalist({"dataList": nested}) if nested else dict(item)

        def pkw(logical: str) -> float:
            for k in _KEY_ALIASES.get(logical, [logical]):
                if k in flat and flat[k] is not None:
                    return round(_to_kw(flat[k], flat.get(f"{k}__unit")), 4)
            return 0.0

        pv1 = pkw("PV1_P")
        pv2 = pkw("PV2_P")
        pv3 = pkw("PV3_P")
        # If power missing, estimate from V*I
        if pv1 == 0:
            try:
                pv1 = round(float(_pick(flat, "PV1_V", 0)) * float(_pick(flat, "PV1_I", 0)) / 1000.0, 4)
            except Exception:
                pass
        if pv2 == 0:
            try:
                pv2 = round(float(_pick(flat, "PV2_V", 0)) * float(_pick(flat, "PV2_I", 0)) / 1000.0, 4)
            except Exception:
                pass

        ac = pkw("APo")
        if ac == 0:
            ac = pkw("AC_R_P") + pkw("AC_S_P") + pkw("AC_T_P")

        e_today = 0.0
        try:
            e_today = float(_pick(flat, "eToday", 0) or 0)
        except Exception:
            e_today = 0.0

        rows.append(
            {
                "time": t,
                "timestamp": t_raw,
                "dc_power_kw": round(pv1 + pv2 + pv3, 4),
                "ac_power_kw": ac,
                "pv1_power_kw": pv1,
                "pv2_power_kw": pv2,
                "e_today_kwh": e_today,
                "temp_c": float(_pick(flat, "T_val", 0) or 0),
            }
        )

    # Sort by time string if possible
    try:
        rows.sort(key=lambda r: r.get("time") or "")
    except Exception:
        pass
    return rows


def get_live_dashboard(
    use_demo_if_no_creds: bool = True,
    force_demo: bool = False,
    device_sn: str | None = None,
) -> dict:
    """
    Main entry: live structured dashboard for a Solarman inverter SN.

    Known plant units: 2501221272 (primary), 2411046235 (second panel).
    """
    sn_pref = (device_sn or "").strip() or None
    if sn_pref:
        # Pin SN for this request (account may host multiple devices)
        set_runtime_credentials(device_sn=sn_pref)
    client = SolarmanClient(device_sn=sn_pref) if sn_pref else SolarmanClient()
    meta = {
        "device_sn": client.device_sn or sn_pref or DEFAULT_SN,
        "rated_power_kw": float(os.getenv("SOLARMAN_RATED_KW", "25")),
        "inverter_type": "String three Inverter",
        "product_type": "2",
        "mppt_no": 2,
        "general_settings": "3,5,7",
        "country": "2",
        "protocol_version": "V0.2.0.9",
        "main": "5512-0331",
        "hmi": "0257",
        "control_sw_v1": "5512-0331",
        "control_sw_v2": "V0.3.3.1",
        "comm_cpu_sw": "V0.2.5.7",
        "arc_board_fw": "0000",
    }

    if force_demo or not client.credentials_configured:
        if not use_demo_if_no_creds and not force_demo:
            raise SolarmanAPIError("No Solarman credentials configured")
        payload = demo_current_payload()
        dash = build_device_dashboard(payload, {**meta, "source": "demo"})
        dash["history"] = demo_history_series(24)
        # No credential/.env messages for public UI
        dash["warning"] = None
        return dash

    try:
        payload = client.get_current_data()
        dash = build_device_dashboard(payload, {**meta, "source": "solarman_api", "device_id": client.device_id})
        # history for today
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            hist = client.get_historical(today, today, time_type=1)
            chart_rows = parse_historical_for_charts(hist)
            dash["history"] = chart_rows if chart_rows else demo_history_series(24)
            dash["history_source"] = "api" if chart_rows else "demo_fallback"
            dash["raw_history"] = hist
        except Exception as he:
            logger.warning("History fetch failed: %s", he)
            dash["history"] = demo_history_series(24)
            dash["history_source"] = "demo_fallback"
            dash["history_error"] = str(he)
        return dash
    except Exception as e:
        logger.error("Live Solarman fetch failed: %s", e, exc_info=True)
        if use_demo_if_no_creds:
            payload = demo_current_payload()
            dash = build_device_dashboard(payload, {**meta, "source": "demo_fallback"})
            dash["history"] = demo_history_series(24)
            dash["warning"] = None
            return dash
        raise
