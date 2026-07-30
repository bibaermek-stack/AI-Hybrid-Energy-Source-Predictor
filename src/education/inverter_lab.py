"""
Interactive solar inverter subsystem training (3D + wiring board).

Educational wiring / component tasks based on the multi-part
``Solar Inverter Subsystem`` assembly under
``dashboard/static/models/solar_inverter_subsystem/``.

Scenarios start with deliberate faults (reversed DC, open isolator, wrong AC phase,
unseated logger). Students correct each connection; answers are graded.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Logical ports on the inverter training board
PORTS = (
    "dc_pos",
    "dc_neg",
    "pe",
    "ac_l",
    "ac_n",
    "isolator",
    "logger",
)

PORT_LABELS: dict[str, dict[str, str]] = {
    "dc_pos": {"en": "DC+ (PV positive)", "kk": "DC+ (PV оң)"},
    "dc_neg": {"en": "DC− (PV negative)", "kk": "DC− (PV теріс)"},
    "pe": {"en": "PE earth", "kk": "PE жер"},
    "ac_l": {"en": "AC Line (L)", "kk": "AC фаза (L)"},
    "ac_n": {"en": "AC Neutral (N)", "kk": "AC ноль (N)"},
    "isolator": {"en": "AC isolator", "kk": "AC ажыратқыш"},
    "logger": {"en": "Data logger COM", "kk": "Data logger COM"},
}

# Allowed wire / state choices per port
CHOICES: dict[str, list[dict[str, str]]] = {
    "dc_pos": [
        {"id": "pv_pos", "en": "PV string +", "kk": "PV тізбек +"},
        {"id": "pv_neg", "en": "PV string − (WRONG)", "kk": "PV тізбек − (ҚАТЕ)"},
        {"id": "open", "en": "Disconnected", "kk": "Ажыратылған"},
    ],
    "dc_neg": [
        {"id": "pv_neg", "en": "PV string −", "kk": "PV тізбек −"},
        {"id": "pv_pos", "en": "PV string + (WRONG)", "kk": "PV тізбек + (ҚАТЕ)"},
        {"id": "open", "en": "Disconnected", "kk": "Ажыратылған"},
    ],
    "pe": [
        {"id": "earth", "en": "Site earth bar", "kk": "Жер шинасы"},
        {"id": "open", "en": "Disconnected", "kk": "Ажыратылған"},
        {"id": "ac_n", "en": "Tied to N only (WRONG)", "kk": "Тек N-ге (ҚАТЕ)"},
    ],
    "ac_l": [
        {"id": "grid_l", "en": "Grid L", "kk": "Желі L"},
        {"id": "grid_n", "en": "Grid N (WRONG)", "kk": "Желі N (ҚАТЕ)"},
        {"id": "open", "en": "Disconnected", "kk": "Ажыратылған"},
    ],
    "ac_n": [
        {"id": "grid_n", "en": "Grid N", "kk": "Желі N"},
        {"id": "grid_l", "en": "Grid L (WRONG)", "kk": "Желі L (ҚАТЕ)"},
        {"id": "open", "en": "Disconnected", "kk": "Ажыратылған"},
    ],
    "isolator": [
        {"id": "on", "en": "ON (closed)", "kk": "ON (жабық)"},
        {"id": "off", "en": "OFF (open)", "kk": "OFF (ашық)"},
    ],
    "logger": [
        {"id": "seated", "en": "Firmly seated on COM", "kk": "COM-ға тығыз қосылған"},
        {"id": "loose", "en": "Loose / unplugged", "kk": "Босаң / суырылған"},
    ],
}

# Correct healthy topology
CORRECT: dict[str, str] = {
    "dc_pos": "pv_pos",
    "dc_neg": "pv_neg",
    "pe": "earth",
    "ac_l": "grid_l",
    "ac_n": "grid_n",
    "isolator": "on",
    "logger": "seated",
}

# Map multi-OBJ parts → logical component (for 3D highlight)
OBJ_PART_MAP: dict[str, str] = {
    "model_0": "inverter_body",
    "model_1": "generation_meter",
    "model_2": "dc_pos",
    "model_3": "dc_neg",
    "model_4": "ac_l",
    "model_5": "pe",
    "model_6": "isolator",
    "model_7": "logger",
    "model_8": "ac_n",
    "model_9": "fuse",
    "model_10": "pv_string",
    "model_11": "structure",
    "model_12": "cable_tray",
}

PART_COLORS: dict[str, int] = {
    "inverter_body": 0x4b5563,
    "generation_meter": 0x38bdf8,
    "dc_pos": 0xef4444,
    "dc_neg": 0x3b82f6,
    "ac_l": 0xf59e0b,
    "pe": 0x22c55e,
    "isolator": 0xa855f7,
    "logger": 0xec4899,
    "ac_n": 0xeab308,
    "fuse": 0xf97316,
    "pv_string": 0x14b8a6,
    "structure": 0x6b7280,
    "cable_tray": 0x78716c,
}


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


SCENARIOS: dict[str, dict[str, Any]] = {
    "healthy": {
        "id": "healthy",
        "title": _L("Healthy system (reference)", "Сау жүйе (үлгі)"),
        "story": _L(
            "All connections correct. Use as a reference before fault labs.",
            "Барлық қосылыстар дұрыс. Ақау зертханаларына дейін үлгі ретінде қолданыңыз.",
        ),
        "initial": dict(CORRECT),
        "symptoms": _L("Normal AC output when PV available.", "PV бар кезде қалыпты AC шығыс."),
    },
    "reversed_dc": {
        "id": "reversed_dc",
        "title": _L("Fault A — reversed DC polarity", "Ақау A — кері DC полярлық"),
        "story": _L(
            "Installer swapped PV+ and PV− on the inverter DC terminals. "
            "Inverter may refuse to start or show insulation/polarity alarm.",
            "Монтажник PV+ мен PV−-ны DC терминалдарында ауыстырып қойған. "
            "Инвертор іске қосылмауы немесе полярлық/изоляция дабылы беруі мүмкін.",
        ),
        "initial": {
            **CORRECT,
            "dc_pos": "pv_neg",
            "dc_neg": "pv_pos",
        },
        "symptoms": _L(
            "No power / polarity fault code; reverse the DC cables.",
            "Қуат жоқ / полярлық код; DC кабельдерді дұрыстаңыз.",
        ),
        "focus_parts": ["dc_pos", "dc_neg"],
    },
    "open_isolator": {
        "id": "open_isolator",
        "title": _L("Fault B — AC isolator open", "Ақау B — AC ажыратқыш ашық"),
        "story": _L(
            "AC isolator left OFF after maintenance. Inverter cannot export to grid.",
            "Қызметтен кейін AC ажыратқыш OFF қалған. Инвертор желіге бере алмайды.",
        ),
        "initial": {**CORRECT, "isolator": "off"},
        "symptoms": _L(
            "PV produces DC but grid export is zero until isolator is ON.",
            "PV DC өндіреді, бірақ ажыратқыш ON болмайынша экспорт 0.",
        ),
        "focus_parts": ["isolator", "ac_l", "ac_n"],
    },
    "swapped_ac": {
        "id": "swapped_ac",
        "title": _L("Fault C — AC L/N swapped", "Ақау C — AC L/N ауысқан"),
        "story": _L(
            "AC line and neutral are reversed on the inverter AC terminals.",
            "Инвертор AC терминалдарында фаза мен ноль ауысқан.",
        ),
        "initial": {
            **CORRECT,
            "ac_l": "grid_n",
            "ac_n": "grid_l",
        },
        "symptoms": _L(
            "Grid fault / wrong phase sequence style alarm — swap L and N.",
            "Grid / фаза дабылы — L мен N-ді дұрыстаңыз.",
        ),
        "focus_parts": ["ac_l", "ac_n"],
    },
    "logger_loose": {
        "id": "logger_loose",
        "title": _L("Fault D — data logger unplugged", "Ақау D — logger суырылған"),
        "story": _L(
            "Wi-Fi / Solarman stick is loose on the COM port. Plant produces power "
            "but EcoPredict live telemetry is offline.",
            "Wi-Fi / Solarman stick COM портында босаң. Зауыт қуат береді, "
            "бірақ EcoPredict live телеметрия жоқ.",
        ),
        "initial": {**CORRECT, "logger": "loose"},
        "symptoms": _L(
            "Local AC power OK; cloud / app shows offline — reseat logger.",
            "Жергілікті AC бар; cloud offline — logger-ді қайта қосыңыз.",
        ),
        "focus_parts": ["logger"],
    },
    "compound": {
        "id": "compound",
        "title": _L("Fault E — compound (exam)", "Ақау E — күрделі (емтихан)"),
        "story": _L(
            "Multiple mistakes after a rushed install: reversed DC, open isolator, "
            "and unseated logger. Fix all ports to restore a healthy plant.",
            "Асығыс монтаждан кейін бірнеше қате: кері DC, ашық ажыратқыш, "
            "босаң logger. Барлық порттарды түзетіңіз.",
        ),
        "initial": {
            "dc_pos": "pv_neg",
            "dc_neg": "pv_pos",
            "pe": "earth",
            "ac_l": "grid_l",
            "ac_n": "grid_n",
            "isolator": "off",
            "logger": "loose",
        },
        "symptoms": _L(
            "No export + no monitoring until all three faults are cleared.",
            "Үш ақау түзетілмейінше экспорт пен мониторинг жоқ.",
        ),
        "focus_parts": ["dc_pos", "dc_neg", "isolator", "logger"],
    },
}


def list_scenarios(lang: str = "en") -> list[dict[str, str]]:
    lang = "kk" if lang == "kk" else "en"
    out = []
    for sid, sc in SCENARIOS.items():
        out.append(
            {
                "id": sid,
                "title": sc["title"][lang],
                "story": sc["story"][lang],
                "symptoms": sc["symptoms"][lang],
            }
        )
    return out


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    return deepcopy(SCENARIOS.get(scenario_id))


def initial_state(scenario_id: str) -> dict[str, str]:
    sc = SCENARIOS.get(scenario_id) or SCENARIOS["healthy"]
    return dict(sc["initial"])


def grade_wiring(state: dict[str, str]) -> dict[str, Any]:
    """
    Compare student wiring board to CORRECT topology.

    Returns per-port ok flags and overall pass.
    """
    details = []
    n_ok = 0
    for port in PORTS:
        got = str(state.get(port) or "")
        exp = CORRECT[port]
        ok = got == exp
        if ok:
            n_ok += 1
        details.append({"port": port, "ok": ok, "got": got, "expected": exp})
    total = len(PORTS)
    return {
        "ok": n_ok == total,
        "score": n_ok,
        "total": total,
        "percent": round(100.0 * n_ok / total, 1) if total else 0.0,
        "details": details,
        "wrong_ports": [d["port"] for d in details if not d["ok"]],
    }


def diagnose_faults(state: dict[str, str]) -> list[str]:
    """Human-readable fault tags still present in ``state``."""
    tags = []
    if state.get("dc_pos") == "pv_neg" or state.get("dc_neg") == "pv_pos":
        tags.append("reversed_dc")
    if state.get("isolator") == "off":
        tags.append("open_isolator")
    if state.get("ac_l") == "grid_n" or state.get("ac_n") == "grid_l":
        tags.append("swapped_ac")
    if state.get("logger") == "loose":
        tags.append("logger_loose")
    if state.get("pe") != "earth":
        tags.append("pe_open")
    if state.get("dc_pos") == "open" or state.get("dc_neg") == "open":
        tags.append("dc_open")
    return tags


def port_label(port: str, lang: str) -> str:
    lang = "kk" if lang == "kk" else "en"
    return PORT_LABELS.get(port, {}).get(lang, port)


def choice_label(port: str, choice_id: str, lang: str) -> str:
    lang = "kk" if lang == "kk" else "en"
    for c in CHOICES.get(port, []):
        if c["id"] == choice_id:
            return c[lang]
    return choice_id
