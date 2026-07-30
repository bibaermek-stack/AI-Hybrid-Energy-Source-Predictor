"""Registry of interactive labs (metadata EN/KK)."""

from __future__ import annotations

from typing import Any

LAB_IDS = (
    # P1 / RES
    "lab_pv_physics",
    "lab_mppt_po",
    "lab_bess_soc",
    "lab_microgrid_dispatch",
    # P2
    "lab_heuristic_vs_pulp",
    # P3 / CACER-inspired
    "lab_pv_yield",
    "lab_load_shape",
    "lab_bess_community",
    "lab_shared_energy",
    "lab_rec_finance",
    # P4 optional
    "lab_grid_impact",
    # Hardware / 3D trainer
    "lab_inverter_wiring",
)


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


LABS: dict[str, dict[str, Any]] = {
    "lab_pv_physics": {
        "id": "lab_pv_physics",
        "title": _L("PV power vs weather", "Күн қуаты және ауа райы"),
        "minutes": 15,
        "level": _L("Beginner", "Бастауыш"),
        "phase": "P1",
        "tag": _L("Microgrid", "Микрожелі"),
        "objectives": _L(
            "Relate irradiance and temperature to PV DC power; size an array.",
            "Сәулелену мен температураның PV қуатына әсерін түсіну; массив өлшемін таңдау.",
        ),
        "source": "RenewableEnergySim (MIT) solar model",
        "render": "render_pv_physics",
        "quiz_id": "lab_pv_physics_quiz",
        "theory": "pv_physics",
    },
    "lab_mppt_po": {
        "id": "lab_mppt_po",
        "title": _L("MPPT perturb & observe", "MPPT P&O алгоритмі"),
        "minutes": 15,
        "level": _L("Intermediate", "Орта"),
        "phase": "P1",
        "tag": _L("Microgrid", "Микрожелі"),
        "objectives": _L(
            "Observe how step size affects tracking of the P–V peak.",
            "Қадам өлшемінің P–V шыңын іздеуге әсерін бақылау.",
        ),
        "source": "RenewableEnergySim (MIT) MPPT",
        "render": "render_mppt",
        "quiz_id": "lab_mppt_quiz",
        "theory": "mppt",
    },
    "lab_bess_soc": {
        "id": "lab_bess_soc",
        "title": _L("Battery SOC over a day", "Батарея SOC тәулік бойы"),
        "minutes": 15,
        "level": _L("Beginner", "Бастауыш"),
        "phase": "P1",
        "tag": _L("Microgrid", "Микрожелі"),
        "objectives": _L(
            "Track state of charge under surplus and deficit hours.",
            "Артық/жетіспеу сағаттарында SOC өзгерісін бақылау.",
        ),
        "source": "RenewableEnergySim (MIT) battery + weather",
        "render": "render_bess_soc",
        "quiz_id": "lab_bess_soc_quiz",
        "theory": "bess_soc",
    },
    "lab_microgrid_dispatch": {
        "id": "lab_microgrid_dispatch",
        "title": _L("PV–BESS–grid day dispatch", "Күн–батарея–grid диспетчер"),
        "minutes": 20,
        "level": _L("Intermediate", "Орта"),
        "phase": "P1",
        "tag": _L("Microgrid", "Микрожелі"),
        "objectives": _L(
            "Simulate daily energy balance; quantify import, export, self-consumption.",
            "Тәуліктік энергия балансын модельдеу; импорт/экспорт/өз тұтынуды өлшеу.",
        ),
        "source": "RenewableEnergySim (MIT) engine + balancer",
        "render": "render_microgrid",
        "quiz_id": "lab_microgrid_quiz",
        "theory": "microgrid",
    },
    "lab_heuristic_vs_pulp": {
        "id": "lab_heuristic_vs_pulp",
        "title": _L("Rule-based dispatch vs PuLP", "Эвристика vs PuLP оңтайландыру"),
        "minutes": 25,
        "level": _L("Advanced", "Жоғары"),
        "phase": "P2",
        "tag": _L("Optimization", "Оңтайландыру"),
        "objectives": _L(
            "Compare heuristic microgrid balancer KPIs against EcoPradict PuLP.",
            "Эвристикалық балансир мен EcoPradict PuLP KPI-лерін салыстыру.",
        ),
        "source": "RES balancer + HybridEnergyOptimizer",
        "render": "render_heuristic_vs_pulp",
        "quiz_id": "lab_heuristic_vs_pulp_quiz",
        "theory": "heuristic_vs_pulp",
    },
    "lab_pv_yield": {
        "id": "lab_pv_yield",
        "title": _L("PV production profiles", "PV өндіріс профилдері"),
        "minutes": 15,
        "level": _L("Beginner", "Бастауыш"),
        "phase": "P3",
        "tag": _L("Community", "Қауымдастық"),
        "objectives": _L(
            "Generate a daily PV yield curve from weather and array size.",
            "Ауа райы мен массив өлшемінен тәуліктік PV қисығын алу.",
        ),
        "source": "CACER Tutorial 1 concepts + EcoPradict weather/PV",
        "render": "render_pv_yield",
        "quiz_id": "lab_pv_yield_quiz",
        "theory": "pv_yield",
    },
    "lab_load_shape": {
        "id": "lab_load_shape",
        "title": _L("Domestic load emulation", "Тұрмыстық жүктеме эмуляциясы"),
        "minutes": 15,
        "level": _L("Beginner", "Бастауыш"),
        "phase": "P3",
        "tag": _L("Community", "Қауымдастық"),
        "objectives": _L(
            "Shape morning/evening peaks and rescale to a target kW.",
            "Таңғы/кешкі шыңдарды қалыптастырып, мақсатты кВт-қа масштабтау.",
        ),
        "source": "CACER load-emulator concepts (simplified)",
        "render": "render_load_shape",
        "quiz_id": "lab_load_shape_quiz",
        "theory": "load_shape",
    },
    "lab_bess_community": {
        "id": "lab_bess_community",
        "title": _L("BESS timestep and DoD limits", "BESS қадамы және DoD шектері"),
        "minutes": 15,
        "level": _L("Intermediate", "Орта"),
        "phase": "P3",
        "tag": _L("Community", "Қауымдастық"),
        "objectives": _L(
            "Apply DoD and efficiency to a charge/discharge series.",
            "Заряд/разряд қатарына DoD мен тиімділікті қолдану.",
        ),
        "source": "CACER BESS concept → src/simulation/community/bess_step",
        "render": "render_bess_community",
        "quiz_id": "lab_bess_community_quiz",
        "theory": "bess_community",
    },
    "lab_shared_energy": {
        "id": "lab_shared_energy",
        "title": _L("Shared renewable energy (REC)", "Бөліскен ЖЭК (REC)"),
        "minutes": 25,
        "level": _L("Advanced", "Жоғары"),
        "phase": "P3",
        "tag": _L("Community", "Қауымдастық"),
        "objectives": _L(
            "Compute self-consumption, shared energy, and residual import for N users.",
            "N пайдаланушы үшін өз тұтыну, бөліскен энергия және қалдық импортты есептеу.",
        ),
        "source": "CACER energy-model concepts (simplified REC, not ARERA)",
        "render": "render_shared_energy",
        "quiz_id": "lab_shared_energy_quiz",
        "theory": "shared_energy",
    },
    "lab_rec_finance": {
        "id": "lab_rec_finance",
        "title": _L("Community investment KPIs", "Қауымдастық инвестиция KPI"),
        "minutes": 20,
        "level": _L("Intermediate", "Орта"),
        "phase": "P3",
        "tag": _L("Finance", "Қаржы"),
        "objectives": _L(
            "Compute LCOE, payback, NPV, and IRR for a community PV project.",
            "Қауымдастық PV жобасы үшін LCOE, payback, NPV және IRR есептеу.",
        ),
        "source": "CACER financial ideas + EcoPradict sustainability",
        "render": "render_rec_finance",
        "quiz_id": "lab_rec_finance_quiz",
        "theory": "rec_finance",
    },
    "lab_grid_impact": {
        "id": "lab_grid_impact",
        "title": _L("Power flow intro (offline)", "Қуат ағыны (офлайн)"),
        "minutes": 30,
        "level": _L("Advanced", "Жоғары"),
        "phase": "P4",
        "tag": _L("Grid", "Желі"),
        "objectives": _L(
            "Run offline pandapower notebook; inspect voltage vs PV export.",
            "Офлайн pandapower notebook; кернеу vs PV экспортты бақылау.",
        ),
        "source": "notebooks/labs/power_flow.ipynb + CACER Tutorial 4 (submodule)",
        "render": "render_grid_impact",
        "quiz_id": "lab_grid_impact_quiz",
        "theory": "grid_impact",
        # Streamlit is a hub only; heavy solve stays in Jupyter.
        "available": True,
        "offline": True,
    },
    "lab_inverter_wiring": {
        "id": "lab_inverter_wiring",
        "title": _L(
            "Inverter 3D wiring trainer",
            "Инвертор 3D сым тренажері",
        ),
        "minutes": 25,
        "level": _L("Intermediate", "Орта"),
        "phase": "HW",
        "tag": _L("Hardware / 3D", "Жабдық / 3D"),
        "objectives": _L(
            "On the Solar Inverter Subsystem model: fix reversed DC, open isolator, "
            "swapped AC L/N, and reseat the data logger — graded check with try-again.",
            "Solar Inverter Subsystem моделінде: кері DC, ашық ажыратқыш, ауысқан AC L/N "
            "және logger-ді түзету — тексеру + қайтадан көру.",
        ),
        "source": "dashboard/static/models/solar_inverter_subsystem (CAD assembly)",
        "render": "render_inverter_wiring",
        "quiz_id": "lab_inverter_wiring_quiz",
        "theory": "inverter_wiring",
        "available": True,
    },
}


def list_labs(*, include_unavailable: bool = True) -> list[dict[str, Any]]:
    labs = [LABS[i] for i in LAB_IDS if i in LABS]
    if not include_unavailable:
        labs = [L for L in labs if L.get("available", True)]
    return labs


def get_lab(lab_id: str) -> dict[str, Any]:
    if lab_id not in LABS:
        raise KeyError(lab_id)
    return LABS[lab_id]


def t(field: dict[str, str] | str, lang: str) -> str:
    if isinstance(field, str):
        return field
    return field.get("kk" if lang == "kk" else "en", field.get("en", ""))
