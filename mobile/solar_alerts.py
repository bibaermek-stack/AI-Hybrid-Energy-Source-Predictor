"""
Station alerts inside the app: is a Solarman inverter offline, faulty, silent
or producing nothing in daylight?

The server's /solarman/alert only restates the status and fault code it is
sent, and nothing told the user unless the Solarman screen was open. The app
now reads each inverter's live data itself when it starts and every few
minutes while it is open (see main.py), and shows what it finds on Home and
as a badge on the Solarman tab. The server's sample data (no Solarman
credentials) and saved offline copies raise no alerts: they say nothing about
the station now.

Alerts while the phone is locked would need push notifications (Firebase).
"""

import time
from typing import Any, Callable, Dict, Iterable, List, Optional

TURKISTAN_UTC_OFFSET_S = 5 * 3600
STALE_AFTER_S = 3 * 3600  # Solarman reports every few minutes
DAYLIGHT_HOURS = range(9, 17)  # local hours when a PV plant must produce
NO_OUTPUT_KW = 0.05
CHECK_EVERY_S = 600


def evaluate(sn: str, live: Optional[Dict[str, Any]], now: Optional[float] = None) -> List[Dict[str, Any]]:
    """What is wrong with one inverter, from its /solarman/live reply."""
    if not isinstance(live, dict) or str(live.get("source", "")).startswith("demo"):
        return []
    now = time.time() if now is None else now
    basic = live.get("basic") or {}
    raw = live.get("raw_flat") or {}
    gen = live.get("generation") or {}
    alerts: List[Dict[str, Any]] = []

    status = raw.get("deviceStatus", basic.get("status"))
    offline = str(status) == "0" or str(status).lower() == "offline"
    if offline:
        alerts.append({"sn": sn, "kind": "offline", "level": "error"})
    try:
        fault = int(raw.get("faultCode") or 0)
    except (TypeError, ValueError):
        fault = 0
    if fault > 0:
        alerts.append({"sn": sn, "kind": "fault", "level": "error", "code": fault})
    collected = raw.get("collectionTime")
    if isinstance(collected, (int, float)) and collected > 0 and now - collected > STALE_AFTER_S:
        alerts.append({"sn": sn, "kind": "stale", "level": "warning", "since": float(collected)})
    local_hour = time.gmtime(now + TURKISTAN_UTC_OFFSET_S).tm_hour
    ac_kw = gen.get("ac_active_power_kw")
    if (
        not offline
        and local_hour in DAYLIGHT_HOURS
        and isinstance(ac_kw, (int, float))
        and ac_kw <= NO_OUTPUT_KW
    ):
        alerts.append({"sn": sn, "kind": "no_power", "level": "warning"})
    return alerts


def describe(alert: Dict[str, Any], text: Callable[..., str]) -> str:
    """One line for the user, through state.text."""
    kind, sn = alert["kind"], alert["sn"]
    if kind == "fault":
        return text("alert_fault", sn=sn, code=alert.get("code", "?"))
    if kind == "stale":
        when = time.strftime("%d.%m %H:%M", time.gmtime(alert["since"] + TURKISTAN_UTC_OFFSET_S))
        return text("alert_stale", sn=sn, when=when)
    return text(f"alert_{kind}", sn=sn)


async def check(client: Any, sns: Iterable[str]) -> List[Dict[str, Any]]:
    """Read every inverter and collect its alerts (current replies only)."""
    alerts: List[Dict[str, Any]] = []
    for sn in sns:
        live = await client.get_solarman_live(sn)
        if client.cache_note("live"):
            continue  # a saved copy from earlier: not the station's state now
        alerts.extend(evaluate(sn, live))
    return alerts
