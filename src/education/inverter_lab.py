"""
Solar inverter subsystem trainer (3D lab 12).

The 3D model is the CAD assembly «Solar Inverter Subsystem» (static/lab3d/):
a PV array DC isolator, two DC cables with MC4 connectors landing on the
inverter's DC− / DC+ inputs, the inverter, an AC cable to a rotary AC isolator
and a single-phase generation meter. A Wi-Fi data-logger stick, which the CAD
file does not contain, is added by the viewer on the inverter's COM port.

Each item the student can operate in 3D is a *control* with two states. A
scenario starts with some controls in a faulty state; the student finds the
faults from the inverter display, the meter and the monitoring light, fixes
them in 3D, and the board is graded here.

``status()`` is what the viewer shows for a board state. The viewer does not
re-implement it: ``scripts/build_lab3d_assets.py`` writes every state's status
into static/lab3d/lab_state.json and tests/test_lab3d_assets.py fails if that
file drifts from this module.
"""

from __future__ import annotations

import itertools
from copy import deepcopy
from typing import Any


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


# Board controls, in the order the viewer lists them. Value 0 of each is correct.
CONTROLS: dict[str, dict[str, Any]] = {
    "dc_isolator": {
        "label": _L("PV array DC isolator", "PV массивінің DC ажыратқышы"),
        "part": "dc_isolator",
        "states": [
            {"id": "on", **_L("ON (I)", "ҚОСУЛЫ (I)")},
            {"id": "off", **_L("OFF (0)", "АЖЫРАТЫЛҒАН (0)")},
        ],
    },
    "dc_polarity": {
        "label": _L("DC cables on the inverter inputs", "Инвертор кірістеріндегі DC кабельдер"),
        "part": "dc_inputs",
        "states": [
            {"id": "ok", **_L("PV+ → DC+, PV− → DC−", "PV+ → DC+, PV− → DC−")},
            {
                "id": "reversed",
                **_L("PV+ → DC−, PV− → DC+ (reversed)", "PV+ → DC−, PV− → DC+ (кері)"),
            },
        ],
    },
    "ac_isolator": {
        "label": _L("AC isolator", "AC ажыратқыш"),
        "part": "ac_isolator",
        "states": [
            {"id": "on", **_L("ON (I)", "ҚОСУЛЫ (I)")},
            {"id": "off", **_L("OFF (0)", "АЖЫРАТЫЛҒАН (0)")},
        ],
    },
    "ac_ln": {
        "label": _L("AC terminals L / N", "AC клеммалары L / N"),
        "part": "ac_isolator",
        "states": [
            {"id": "ok", **_L("L → grid L, N → grid N", "L → желі L, N → желі N")},
            {"id": "swapped", **_L("L and N swapped", "L мен N ауысқан")},
        ],
    },
    "pe": {
        "label": _L("Protective earth (PE)", "Қорғаныстық жерге қосу (PE)"),
        "part": "ac_isolator",
        "states": [
            {"id": "connected", **_L("Connected to the earth bar", "Жер шинасына қосылған")},
            {"id": "open", **_L("Not connected", "Қосылмаған")},
        ],
    },
    "logger": {
        "label": _L("Wi-Fi data logger (COM port)", "Wi-Fi деректер логгері (COM порт)"),
        "part": "logger",
        "states": [
            {"id": "seated", **_L("Plugged in", "Қосылған")},
            {"id": "loose", **_L("Pulled out", "Суырылған")},
        ],
    },
}

CORRECT: dict[str, str] = {k: v["states"][0]["id"] for k, v in CONTROLS.items()}


SCENARIOS: dict[str, dict[str, Any]] = {
    "reversed_dc": {
        "title": _L("Fault A — reversed DC polarity", "Ақау A — DC полярлығы кері"),
        "story": _L(
            "After the panels were cleaned the DC plugs went back the wrong way round: "
            "PV+ now lands on the inverter's DC− input.",
            "Панельдерді тазалағаннан кейін DC ашалары кері қосылған: "
            "PV+ инвертордың DC− кірісіне түскен.",
        ),
        "faults": {"dc_polarity": "reversed"},
    },
    "dc_isolator_off": {
        "title": _L("Fault B — DC isolator left OFF", "Ақау B — DC ажыратқыш ажыратулы қалған"),
        "story": _L(
            "A technician isolated the array for an inspection and forgot to switch it back.",
            "Техник тексеру үшін массивті ажыратып, қайта қосуды ұмытқан.",
        ),
        "faults": {"dc_isolator": "off"},
    },
    "ac_isolator_off": {
        "title": _L("Fault C — AC isolator left OFF", "Ақау C — AC ажыратқыш ажыратулы қалған"),
        "story": _L(
            "The panels produce, the inverter screen is lit, but the meter does not count.",
            "Панельдер өндіреді, инвертор экраны жанып тұр, бірақ есептегіш санамайды.",
        ),
        "faults": {"ac_isolator": "off"},
    },
    "swapped_ac": {
        "title": _L("Fault D — AC L and N swapped", "Ақау D — AC L мен N ауысқан"),
        "story": _L(
            "An electrician replaced the AC isolator and landed line and neutral on the wrong terminals.",
            "Электрик AC ажыратқышты ауыстырып, фаза мен нөлді қате клеммаларға қосқан.",
        ),
        "faults": {"ac_ln": "swapped"},
    },
    "pe_open": {
        "title": _L("Fault E — earth not connected", "Ақау E — жерге қосу жоқ"),
        "story": _L(
            "The PE conductor was left off the earth bar after the AC isolator was replaced.",
            "AC ажыратқышты ауыстырғаннан кейін PE сымы жер шинасына қосылмай қалған.",
        ),
        "faults": {"pe": "open"},
    },
    "logger_loose": {
        "title": _L("Fault F — monitoring offline", "Ақау F — мониторинг офлайн"),
        "story": _L(
            "The plant owner says the app shows no data since yesterday. The meter is counting.",
            "Иесі кешеден бері қосымшада дерек жоқ дейді. Есептегіш санап тұр.",
        ),
        "faults": {"logger": "loose"},
    },
    "compound": {
        "title": _L("Exam — several faults at once", "Емтихан — бірнеше ақау бірден"),
        "story": _L(
            "A rushed installation: find and fix every fault before the plant can export.",
            "Асығыс монтаж: станция желіге қуат беруі үшін барлық ақауды тауып, түзетіңіз.",
        ),
        "faults": {
            "dc_polarity": "reversed",
            "dc_isolator": "off",
            "ac_ln": "swapped",
            "logger": "loose",
        },
    },
    "healthy": {
        "title": _L("Reference — healthy system", "Үлгі — сау жүйе"),
        "story": _L(
            "Everything is connected correctly. Look at what a working plant shows.",
            "Барлығы дұрыс қосылған. Жұмыс істеп тұрған станция не көрсететінін қараңыз.",
        ),
        "faults": {},
    },
}

# Inverter output in the healthy state, for the display and the meter.
_HEALTHY_PAC_KW = 3.2
_HEALTHY_VPV = 412
_GRID_VAC = 230


def list_scenarios(lang: str = "en") -> list[dict[str, str]]:
    lang = "kk" if lang == "kk" else "en"
    return [
        {"id": sid, "title": sc["title"][lang], "story": sc["story"][lang]}
        for sid, sc in SCENARIOS.items()
    ]


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    sc = SCENARIOS.get(scenario_id)
    return {"id": scenario_id, **deepcopy(sc)} if sc else None


def initial_state(scenario_id: str) -> dict[str, str]:
    sc = SCENARIOS.get(scenario_id) or SCENARIOS["healthy"]
    return {**CORRECT, **sc["faults"]}


def normalize_state(state: dict[str, Any] | None) -> dict[str, str]:
    """Board state with every control present; unknown values fall back to correct."""
    out: dict[str, str] = {}
    for key, ctl in CONTROLS.items():
        allowed = {s["id"] for s in ctl["states"]}
        value = str((state or {}).get(key) or CORRECT[key])
        out[key] = value if value in allowed else CORRECT[key]
    return out


def status(state: dict[str, Any]) -> dict[str, Any]:
    """
    What the plant shows for a board state: inverter display, output, meter and
    monitoring light. The display reports the first problem an inverter would
    check at start-up (DC input, insulation/earth, grid), as real ones do.
    """
    s = normalize_state(state)
    dc_on = s["dc_isolator"] == "on"
    powered = dc_on  # the control board runs from the PV side
    if not dc_on:
        code, display = "NO_PV", _L("No PV input · Vpv 0 V", "PV кірісі жоқ · Vpv 0 V")
    elif s["dc_polarity"] == "reversed":
        code, display = "DC_POLARITY", _L("DC polarity error", "DC полярлық қатесі")
    elif s["pe"] == "open":
        code, display = "EARTH_FAULT", _L("Insulation / earth fault", "Оқшаулау / жерге қосу ақауы")
    elif s["ac_isolator"] == "off":
        code, display = "GRID_LOST", _L("Grid lost · Vac 0 V", "Желі жоқ · Vac 0 V")
    elif s["ac_ln"] == "swapped":
        code, display = "GRID_LN", _L("Grid fault: L/N", "Желі ақауы: L/N")
    else:
        code = "OK"
        display = _L(
            f"Exporting · Pac {_HEALTHY_PAC_KW} kW", f"Желіге беруде · Pac {_HEALTHY_PAC_KW} kW"
        )
    exporting = code == "OK"
    return {
        "code": code,
        "display": display,
        "inverter_on": powered,
        "exporting": exporting,
        "pac_kw": _HEALTHY_PAC_KW if exporting else 0.0,
        "vpv": _HEALTHY_VPV if dc_on else 0,
        "vac": _GRID_VAC if s["ac_isolator"] == "on" else 0,
        "meter_running": exporting,
        "cloud_online": powered and s["logger"] == "seated",
    }


def state_key(state: dict[str, Any]) -> str:
    s = normalize_state(state)
    return ",".join(f"{k}={s[k]}" for k in CONTROLS)


def status_table() -> dict[str, dict[str, Any]]:
    """status() for every combination of control states (64 boards)."""
    keys = list(CONTROLS)
    table = {}
    for combo in itertools.product(*[[st["id"] for st in CONTROLS[k]["states"]] for k in keys]):
        board = dict(zip(keys, combo))
        table[state_key(board)] = status(board)
    return table


def diagnose_faults(state: dict[str, Any]) -> list[str]:
    """Controls still in a faulty state."""
    s = normalize_state(state)
    return [k for k in CONTROLS if s[k] != CORRECT[k]]


def grade_wiring(state: dict[str, Any]) -> dict[str, Any]:
    """Compare the student's board with the healthy system."""
    s = normalize_state(state)
    details = [
        {"control": k, "ok": s[k] == CORRECT[k], "got": s[k], "expected": CORRECT[k]}
        for k in CONTROLS
    ]
    n_ok = sum(1 for d in details if d["ok"])
    total = len(details)
    return {
        "ok": n_ok == total,
        "score": n_ok,
        "total": total,
        "percent": round(100.0 * n_ok / total, 1),
        "details": details,
        "wrong": [d["control"] for d in details if not d["ok"]],
        "status": status(s),
    }


def control_label(control: str, lang: str) -> str:
    lang = "kk" if lang == "kk" else "en"
    return CONTROLS.get(control, {}).get("label", {}).get(lang, control)


def viewer_config() -> dict[str, Any]:
    """Everything the 3D viewer needs about the board (written to lab_state.json)."""
    return {
        # Key order of the status table (JSON object order is not relied on).
        "order": list(CONTROLS),
        "controls": CONTROLS,
        "correct": CORRECT,
        "scenarios": {
            sid: {"title": sc["title"], "story": sc["story"], "initial": initial_state(sid)}
            for sid, sc in SCENARIOS.items()
        },
        "status": status_table(),
    }
