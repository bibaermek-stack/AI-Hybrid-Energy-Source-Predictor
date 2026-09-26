"""
Final test of each lab (website and mobile app).

Question kinds
--------------
choice   pick one option.
number   type a number computed from the theory (absolute or relative tolerance).
run      set the given parameters in the lab, run it and read one result. The
         expected value is computed by the lab engine itself (runner.run_lab),
         so it always matches what the student sees.
part3d   tap a part in the 3D model (lab 12); the answer is the part id from
         static/lab3d/assembly.json.
fix      a faulty board in 3D (lab 12); the answer is the board after the
         student's fixes, graded with inverter_lab.grade_wiring.

``public_test`` gives the client the questions without answers; ``grade_test``
grades a dict {question_id: answer}. A test is passed at PASS_PERCENT.
"""

from __future__ import annotations

import hashlib
import math
import random
from functools import lru_cache
from typing import Any

from src.education.inverter_lab import CONTROLS, CORRECT, grade_wiring
from src.education.labs.runner import list_params, metric_value, run_lab, validate_params

PASS_PERCENT = 70.0


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


def choice(qid: str, prompt, choices: list, correct: int, explain) -> dict[str, Any]:
    return {
        "id": qid,
        "kind": "choice",
        "prompt": prompt,
        "choices": choices,
        "correct": correct,
        "explain": explain,
    }


def number(
    qid: str, prompt, answer: float, tol: float, explain, unit: str = "", rel: bool = False
) -> dict[str, Any]:
    return {
        "id": qid,
        "kind": "number",
        "prompt": prompt,
        "answer": answer,
        "tol": tol,
        "rel": rel,
        "unit": unit,
        "explain": explain,
    }


def run(
    qid: str, prompt, params: dict[str, Any], metric: str, tol: float, explain, rel: bool = True
) -> dict[str, Any]:
    return {
        "id": qid,
        "kind": "run",
        "prompt": prompt,
        "params": params,
        "metric": metric,
        "tol": tol,
        "rel": rel,
        "explain": explain,
    }


def part3d(qid: str, prompt, part: str, explain) -> dict[str, Any]:
    return {"id": qid, "kind": "part3d", "prompt": prompt, "part": part, "explain": explain}


def fix(qid: str, prompt, faults: dict[str, str], explain) -> dict[str, Any]:
    return {"id": qid, "kind": "fix", "prompt": prompt, "faults": faults, "explain": explain}


TESTS: dict[str, list[dict[str, Any]]] = {
    "lab_pv_physics": [
        run(
            "q1",
            _L(
                "Run the lab with these settings. What DC power P_DC does the array give?",
                "Зертхананы осы параметрлермен іске қосыңыз. Массив қандай DC қуат P_DC береді?",
            ),
            {"n": 120, "area": 1.6, "eta": 0.18, "gamma": 0.004, "irr": 800, "temp": 45},
            "p_dc_kw",
            0.02,
            _L(
                "η_eff = 0.18·(1 − 0.004·20) = 0.1656; P = 0.1656 · 192 m² · 800 W/m² ≈ 25.4 kW.",
                "η_eff = 0.18·(1 − 0.004·20) = 0.1656; P = 0.1656 · 192 м² · 800 Вт/м² ≈ 25.4 кВт.",
            ),
        ),
        number(
            "q2",
            _L(
                "η₀ = 0.20, γ = 0.005 1/°C, T = 55 °C. Compute η_eff.",
                "η₀ = 0.20, γ = 0.005 1/°C, T = 55 °C. η_eff есептеңіз.",
            ),
            0.17,
            0.002,
            _L(
                "η_eff = 0.20·(1 − 0.005·30) = 0.20·0.85 = 0.17.",
                "η_eff = 0.20·(1 − 0.005·30) = 0.20·0.85 = 0.17.",
            ),
        ),
        choice(
            "q3",
            _L(
                "Why does the array give less power on a hot day at the same irradiance?",
                "Неліктен сәулелену бірдей болса да, ыстық күні массив аз қуат береді?",
            ),
            [
                _L(
                    "Cell efficiency falls as the temperature rises above 25 °C",
                    "Температура 25 °C-тан асқанда ұяшық ПӘК-і төмендейді",
                ),
                _L(
                    "Hot air absorbs the sunlight before it reaches the panel",
                    "Ыстық ауа күн сәулесін панельге жеткізбей сіңіреді",
                ),
                _L("The panel area shrinks in the heat", "Ыстықта панель ауданы кішірейеді"),
                _L("It does not: heat raises the efficiency", "Олай емес: ыстық ПӘК-ті арттырады"),
            ],
            0,
            _L(
                "With γ > 0 the model multiplies η₀ by (1 − γ(T − 25)).",
                "γ > 0 болғанда модель η₀-ді (1 − γ(T − 25))-ке көбейтеді.",
            ),
        ),
        choice(
            "q4",
            _L(
                "Irradiance G doubles, temperature unchanged. P_DC…",
                "Сәулелену G екі есе өсті, температура өзгермеді. P_DC…",
            ),
            [
                _L("stays the same", "өзгермейді"),
                _L("doubles", "екі есе өседі"),
                _L("grows four times", "төрт есе өседі"),
                _L("halves", "екі есе азаяды"),
            ],
            1,
            _L(
                "P_DC = η_eff · A · G is proportional to G.",
                "P_DC = η_eff · A · G, яғни G-ге пропорционал.",
            ),
        ),
        choice(
            "q5",
            _L(
                "In this lab's model, what is η_eff at T = 15 °C?",
                "Осы зертхана моделінде T = 15 °C кезінде η_eff неге тең?",
            ),
            [
                _L(
                    "η₀ — the model gives no gain below 25 °C",
                    "η₀ — модель 25 °C-тан төмен өсім бермейді",
                ),
                _L("η₀ · (1 + 10γ)", "η₀ · (1 + 10γ)"),
                _L("η₀ · (1 − 10γ)", "η₀ · (1 − 10γ)"),
                _L("zero", "нөл"),
            ],
            0,
            _L(
                "The formula uses max(T − 25, 0), so below 25 °C η_eff = η₀.",
                "Формулада max(T − 25, 0) тұр, сондықтан 25 °C-тан төмен η_eff = η₀.",
            ),
        ),
    ],
    "lab_mppt_po": [
        choice(
            "q1",
            _L(
                "The last step was +ΔV and the power went up. P&O's next step is…",
                "Соңғы қадам +ΔV болды, қуат өсті. P&O-ның келесі қадамы…",
            ),
            [
                _L("+ΔV again (same direction)", "тағы +ΔV (сол бағытта)"),
                _L("−ΔV (reverse)", "−ΔV (кері)"),
                _L("jump to 0 V", "0 В-қа секіру"),
                _L("stop tracking", "іздеуді тоқтату"),
            ],
            0,
            _L(
                "P&O keeps the direction that raised power and reverses when power falls.",
                "P&O қуатты өсірген бағытты сақтайды, қуат азайса бағытты өзгертеді.",
            ),
        ),
        choice(
            "q2",
            _L(
                "Compared with a small step ΔV, a large step…",
                "Кіші ΔV қадаммен салыстырғанда үлкен қадам…",
            ),
            [
                _L(
                    "reaches the peak faster but oscillates more around it",
                    "шыңға тезірек жетеді, бірақ айналасында көбірек тербеледі",
                ),
                _L("is slower and oscillates more", "баяу және көбірек тербеледі"),
                _L("removes all oscillation", "тербелісті толық жояды"),
                _L("changes the true maximum power", "нақты максимал қуатты өзгертеді"),
            ],
            0,
            _L(
                "Run the lab with ΔV = 0.1 and 2.0 V and compare the ripple.",
                "Зертханада ΔV = 0.1 және 2.0 В етіп, тербелісті салыстырыңыз.",
            ),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What is the true maximum power P_MPP?",
                "Зертхананы осы параметрлермен іске қосыңыз. Нақты максимал қуат P_MPP қанша?",
            ),
            {"irr": 600, "step": 0.5, "steps": 80},
            "p_mpp_w",
            0.02,
            _L(
                "P_MPP is the peak of the panel's P–V curve at G = 600 W/m².",
                "P_MPP — G = 600 Вт/м² кезіндегі P–V қисығының шыңы.",
            ),
        ),
        choice(
            "q4",
            _L(
                "Irradiance falls from 1000 to 500 W/m². The power at the MPP…",
                "Сәулелену 1000-нан 500 Вт/м²-ге түсті. MPP қуаты…",
            ),
            [
                _L("drops roughly by half", "шамамен екі есе азаяды"),
                _L("stays the same", "өзгермейді"),
                _L("doubles", "екі есе өседі"),
                _L("becomes zero", "нөлге тең болады"),
            ],
            0,
            _L(
                "The photocurrent is proportional to irradiance, so the MPP power roughly is too.",
                "Фототок сәулеленуге пропорционал, сондықтан MPP қуаты да шамамен солай.",
            ),
        ),
        choice(
            "q5",
            _L("What does an MPPT controller adjust?", "MPPT контроллері нені реттейді?"),
            [
                _L("The operating voltage of the PV array", "PV массивінің жұмыс кернеуін"),
                _L("The grid tariff", "Желі тарифін"),
                _L("The panel tilt angle", "Панельдің көлбеу бұрышын"),
                _L("The battery capacity", "Батарея сыйымдылығын"),
            ],
            0,
            _L(
                "It moves the operating point along the I–V curve toward the power peak.",
                "Ол жұмыс нүктесін I–V қисығы бойымен қуат шыңына қарай жылжытады.",
            ),
        ),
    ],
    "lab_bess_soc": [
        number(
            "q1",
            _L(
                "E_cap = 40 kWh, SOC₀ = 0.5. Charge at 10 kW for 1 h with η = 0.95. SOC₁ (fraction)?",
                "E_cap = 40 кВт·сағ, SOC₀ = 0.5. 1 сағат 10 кВт-пен η = 0.95 зарядтау. SOC₁ (үлес)?",
            ),
            0.7375,
            0.005,
            _L(
                "ΔE = 0.95 · 10 = 9.5 kWh; SOC₁ = 0.5 + 9.5/40 = 0.7375.",
                "ΔE = 0.95 · 10 = 9.5 кВт·сағ; SOC₁ = 0.5 + 9.5/40 = 0.7375.",
            ),
        ),
        number(
            "q2",
            _L(
                "DoD = 0.8. The lowest allowed SOC (fraction)?",
                "DoD = 0.8. Рұқсат етілген ең төмен SOC (үлес)?",
            ),
            0.2,
            0.005,
            _L(
                "SOC_min = 1 − DoD = 0.2. The lab's SOC curve stops at this floor.",
                "SOC_min = 1 − DoD = 0.2. Зертханадағы SOC қисығы осы шекте тоқтайды.",
            ),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What is the SOC at the end of the day (%)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Тәулік соңындағы SOC қанша (%)?",
            ),
            {"n": 250, "bat": 80, "load": 6, "dod": 0.8, "weather": "synthetic"},
            "soc_end_pct",
            1.0,
            _L(
                "Read 'SOC at the end of the day' from the results.",
                "Нәтижеден «Тәулік соңындағы SOC» мәнін оқыңыз.",
            ),
            rel=False,
        ),
        choice(
            "q4",
            _L(
                "PV exceeds the load and the battery is not full. The battery…",
                "PV жүктемеден артық, батарея толмаған. Батарея…",
            ),
            [
                _L("charges", "зарядталады"),
                _L("discharges", "разрядталады"),
                _L("stays idle", "бос тұрады"),
                _L("switches off", "өшеді"),
            ],
            0,
            _L(
                "Surplus PV is stored first; only what the battery cannot take is exported.",
                "Артық PV алдымен жинақталады; батарея ала алмағаны ғана экспортталады.",
            ),
        ),
        choice(
            "q5",
            _L("Why keep DoD below 1?", "Неліктен DoD-ны 1-ден төмен ұстайды?"),
            [
                _L(
                    "Deep discharges shorten the battery's life",
                    "Терең разряд батареяның қызмет мерзімін қысқартады",
                ),
                _L("It increases the battery's capacity", "Бұл батарея сыйымдылығын арттырады"),
                _L("It raises the PV output", "Бұл PV өндірісін арттырады"),
                _L("The inverter requires it", "Инвертор соны талап етеді"),
            ],
            0,
            _L(
                "A lower DoD trades usable energy for more cycles.",
                "Кіші DoD пайдалы энергияны азайтып, цикл санын көбейтеді.",
            ),
        ),
    ],
    "lab_microgrid_dispatch": [
        number(
            "q1",
            _L(
                "E_pv = 120 kWh, of which 90 kWh are used on site. Self-consumption (%)?",
                "E_pv = 120 кВт·сағ, оның 90 кВт·сағ-ы орнында тұтынылды. Өзіндік тұтыну (%)?",
            ),
            75.0,
            0.5,
            _L("SC = 90 / 120 = 75 %.", "SC = 90 / 120 = 75 %."),
        ),
        run(
            "q2",
            _L(
                "Run the lab with these settings. How much energy is imported from the grid (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Желіден қанша энергия импортталады (кВт·сағ)?",
            ),
            {"n": 150, "bat": 50, "load": 15, "inv": 40, "dod": 0.8, "weather": "sample"},
            "import_kwh",
            0.02,
            _L("Read 'Grid import' from the results.", "Нәтижеден «Желіден импорт» мәнін оқыңыз."),
        ),
        choice(
            "q3",
            _L(
                "An evening deficit hour, the battery is at its floor. The load is supplied by…",
                "Кешкі тапшылық сағаты, батарея шегінде. Жүктемені не қамтамасыз етеді?",
            ),
            [
                _L("grid import", "желіден импорт"),
                _L("PV", "PV"),
                _L("nothing — the load is cut", "ештеңе — жүктеме ажыратылады"),
                _L("export", "экспорт"),
            ],
            0,
            _L(
                "After PV and the battery, the grid covers what is left.",
                "PV мен батареядан кейін қалғанын желі жабады.",
            ),
        ),
        choice(
            "q4",
            _L(
                "The inverter rating is below the PV peak. At midday…",
                "Инвертор қуаты PV шыңынан аз. Түсте…",
            ),
            [
                _L(
                    "part of the PV power is clipped and lost",
                    "PV қуатының бір бөлігі қиылып, жоғалады",
                ),
                _L("the inverter delivers more than its rating", "инвертор өз қуатынан көп береді"),
                _L("the battery charges from the grid", "батарея желіден зарядталады"),
                _L("nothing changes", "ештеңе өзгермейді"),
            ],
            0,
            _L(
                "Output is capped at the rating; try inv = 10 kW in the lab.",
                "Шығыс номиналмен шектеледі; зертханада inv = 10 кВт қойып көріңіз.",
            ),
        ),
        choice(
            "q5",
            _L(
                "Doubling the battery capacity usually…",
                "Батарея сыйымдылығын екі есе арттыру әдетте…",
            ),
            [
                _L(
                    "lowers import and export and raises self-consumption",
                    "импорт пен экспортты азайтып, өзіндік тұтынуды арттырады",
                ),
                _L("raises import", "импортты арттырады"),
                _L("raises the PV energy", "PV энергиясын арттырады"),
                _L("has no effect", "әсер етпейді"),
            ],
            0,
            _L(
                "More midday surplus is stored and used in the evening.",
                "Түскі артықтық көбірек жинақталып, кешке пайдаланылады.",
            ),
        ),
    ],
    "lab_heuristic_vs_pulp": [
        choice(
            "q1",
            _L(
                "How does the rule-based dispatcher decide what to do?",
                "Ережелік диспетчер шешімді қалай қабылдайды?",
            ),
            [
                _L(
                    "Hour by hour, from the current state only",
                    "Сағат сайын, тек ағымдағы күйге қарап",
                ),
                _L(
                    "By optimising the whole day with prices",
                    "Бағаларды ескеріп, бүкіл тәулікті оңтайландырып",
                ),
                _L("At random", "Кездейсоқ"),
                _L("From yesterday's schedule", "Кешегі кесте бойынша"),
            ],
            0,
            _L(
                "The balancer reacts each step; PuLP plans the whole horizon.",
                "Балансир әр қадамда әрекет етеді; PuLP бүкіл горизонтты жоспарлайды.",
            ),
        ),
        number(
            "q2",
            _L(
                "c_imp = 0.12 $/kWh, c_exp = 0.06 $/kWh, E_imp = 20 kWh, E_exp = 5 kWh. Net cost C = c_imp·E_imp − c_exp·E_exp ($)?",
                "c_imp = 0.12 $/кВт·сағ, c_exp = 0.06 $/кВт·сағ, E_imp = 20, E_exp = 5 кВт·сағ. Таза шығын C ($)?",
            ),
            2.1,
            0.02,
            _L("C = 2.4 − 0.3 = 2.1 $.", "C = 2.4 − 0.3 = 2.1 $."),
        ),
        choice(
            "q3",
            _L("The lab's ΔE_imp is defined as…", "Зертханадағы ΔE_imp қалай анықталады?"),
            [
                _L("E_imp(rules) − E_imp(PuLP)", "E_imp(ереже) − E_imp(PuLP)"),
                _L("E_imp(PuLP) − E_imp(rules)", "E_imp(PuLP) − E_imp(ереже)"),
                _L("E_exp(rules) − E_exp(PuLP)", "E_exp(ереже) − E_exp(PuLP)"),
                _L("E_pv − E_load", "E_pv − E_жүктеме"),
            ],
            0,
            _L("Positive ΔE_imp means PuLP imports less.", "ΔE_imp оң болса, PuLP аз импорттайды."),
        ),
        run(
            "q4",
            _L(
                "Run the lab with these settings. How much does the rule-based dispatcher import (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Ережелік диспетчер қанша импорттайды (кВт·сағ)?",
            ),
            {
                "n": 100,
                "bat": 50,
                "load": 15,
                "mode": "balanced",
                "price_import": 0.12,
                "price_export": 0.06,
                "weather": "sample",
            },
            "heur_import_kwh",
            0.02,
            _L(
                "Read 'Import, rule-based' from the results.",
                "Нәтижеден «Импорт, ережелік» мәнін оқыңыз.",
            ),
        ),
        choice(
            "q5",
            _L("Why can PuLP beat the rules?", "Неліктен PuLP ережелерден озуы мүмкін?"),
            [
                _L(
                    "It sees the whole day's PV, load and prices in advance",
                    "Ол бүкіл тәуліктің PV, жүктеме және бағаларын алдын ала көреді",
                ),
                _L("It has a bigger battery", "Оның батареясы үлкенірек"),
                _L("It produces more PV", "Ол көбірек PV өндіреді"),
                _L("It ignores the battery limits", "Ол батарея шектерін елемейді"),
            ],
            0,
            _L(
                "Same equipment, better timing: it plans with the forecast.",
                "Жабдық бірдей, уақыт тиімдірек: ол болжаммен жоспарлайды.",
            ),
        ),
    ],
    "lab_pv_yield": [
        number(
            "q1",
            _L(
                "Hourly power (kW): 0, 0, 2, 4, 6, 4, 2, 0. Energy over these hours (kWh)?",
                "Сағаттық қуат (кВт): 0, 0, 2, 4, 6, 4, 2, 0. Осы сағаттардағы энергия (кВт·сағ)?",
            ),
            18.0,
            0.1,
            _L("E = Σ P·Δt = 18 kWh.", "E = Σ P·Δt = 18 кВт·сағ."),
        ),
        run(
            "q2",
            _L(
                "Run the lab with these settings. What is the daily yield (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Тәуліктік өндіріс қанша (кВт·сағ)?",
            ),
            {"n": 80, "eta": 0.20, "weather": "sample"},
            "yield_kwh",
            0.02,
            _L(
                "Read 'Daily yield' from the results.",
                "Нәтижеден «Тәуліктік өндіріс» мәнін оқыңыз.",
            ),
        ),
        choice(
            "q3",
            _L(
                "In this model, doubling the number of panels…",
                "Бұл модельде панель санын екі есе арттыру…",
            ),
            [
                _L("doubles the daily yield", "тәуліктік өндірісті екі есе арттырады"),
                _L("does not change it", "оны өзгертпейді"),
                _L("quadruples it", "төрт есе арттырады"),
                _L("halves it", "екі есе азайтады"),
            ],
            0,
            _L("Power is proportional to the total area.", "Қуат жалпы ауданға пропорционал."),
        ),
        number(
            "q4",
            _L(
                "A 5 kWp array produced 30 kWh in a day. Specific yield (kWh/kWp)?",
                "5 кВт-шың массив тәулігіне 30 кВт·сағ өндірді. Меншікті өндіріс (кВт·сағ/кВт-шың)?",
            ),
            6.0,
            0.05,
            _L("30 / 5 = 6 kWh/kWp.", "30 / 5 = 6 кВт·сағ/кВт-шың."),
        ),
        choice(
            "q5",
            _L(
                "What is the specific yield (kWh/kWp) useful for?",
                "Меншікті өндіріс (кВт·сағ/кВт-шың) не үшін пайдалы?",
            ),
            [
                _L(
                    "Comparing sites and systems of different sizes",
                    "Әртүрлі өлшемдегі орындар мен жүйелерді салыстыру",
                ),
                _L("Choosing the cable colour", "Кабель түсін таңдау"),
                _L("Setting the grid tariff", "Желі тарифін белгілеу"),
                _L("Measuring battery SOC", "Батарея SOC-ын өлшеу"),
            ],
            0,
            _L(
                "Dividing by kWp removes the system size from the comparison.",
                "кВт-шыңға бөлу жүйе өлшемін салыстырудан алып тастайды.",
            ),
        ),
    ],
    "lab_load_shape": [
        number(
            "q1",
            _L(
                "Raw peak 3.5 kW, target peak 5.0 kW. Scale factor k = P_target / P_max?",
                "Бастапқы шың 3.5 кВт, мақсатты шың 5.0 кВт. Масштаб коэффициенті k?",
            ),
            1.4286,
            0.01,
            _L("k = 5.0 / 3.5 ≈ 1.43.", "k = 5.0 / 3.5 ≈ 1.43."),
        ),
        number(
            "q2",
            _L(
                "Hourly load (kW): 1, 2, 3, 2, 1. Energy (kWh)?",
                "Сағаттық жүктеме (кВт): 1, 2, 3, 2, 1. Энергия (кВт·сағ)?",
            ),
            9.0,
            0.05,
            _L("E = Σ P·Δt = 9 kWh.", "E = Σ P·Δt = 9 кВт·сағ."),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What is the day's energy (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Тәуліктік энергия қанша (кВт·сағ)?",
            ),
            {
                "base": 0.8,
                "morning": 2.0,
                "evening": 3.5,
                "peak": 5.0,
                "noise": 0,
                "seed": 42,
                "hours": 24,
            },
            "energy_kwh",
            0.02,
            _L("Read 'Energy' from the results.", "Нәтижеден «Энергия» мәнін оқыңыз."),
        ),
        choice(
            "q4",
            _L(
                "A low load factor (mean / peak) means…",
                "Жүктеме коэффициентінің (орташа / шың) төмен болуы нені білдіреді?",
            ),
            [
                _L(
                    "a short, high peak compared with the average",
                    "орташамен салыстырғанда қысқа әрі биік шың",
                ),
                _L("a flat load", "тегіс жүктеме"),
                _L("no load", "жүктеменің болмауы"),
                _L("a large battery", "үлкен батарея"),
            ],
            0,
            _L(
                "The network must be sized for a peak that is rarely reached.",
                "Желіні сирек болатын шыңға есептеу керек болады.",
            ),
        ),
        choice(
            "q5",
            _L("Rescaling the profile to a new peak…", "Профильді жаңа шыңға масштабтау…"),
            [
                _L(
                    "multiplies every hour by the same factor",
                    "әр сағатты бірдей коэффициентке көбейтеді",
                ),
                _L("only changes the peak hour", "тек шың сағатын өзгертеді"),
                _L("shifts the peak to midday", "шыңды түске жылжытады"),
                _L("adds noise", "шу қосады"),
            ],
            0,
            _L(
                "The shape stays the same; only the scale changes.",
                "Пішін өзгермейді, тек масштаб өзгереді.",
            ),
        ),
    ],
    "lab_bess_community": [
        number(
            "q1",
            _L(
                "E_cap = 50 kWh, DoD = 0.8. Energy floor E_min (kWh)?",
                "E_cap = 50 кВт·сағ, DoD = 0.8. Энергия шегі E_min (кВт·сағ)?",
            ),
            10.0,
            0.1,
            _L("E_min = 50 · (1 − 0.8) = 10 kWh.", "E_min = 50 · (1 − 0.8) = 10 кВт·сағ."),
        ),
        choice(
            "q2",
            _L("A higher DoD gives…", "DoD жоғары болса…"),
            [
                _L("a lower E_min and more usable energy", "E_min төмен, пайдалы энергия көп"),
                _L("a higher E_min", "E_min жоғары"),
                _L("a larger capacity", "сыйымдылық үлкен"),
                _L("higher efficiency", "ПӘК жоғары"),
            ],
            0,
            _L(
                "E_min = E_cap(1 − DoD) falls as DoD rises.",
                "E_min = E_cap(1 − DoD), DoD өскенде азаяды.",
            ),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What are the conversion losses over the day (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Тәуліктік түрлендіру шығыны қанша (кВт·сағ)?",
            ),
            {"cap": 50, "dod": 0.8, "eta": 0.95, "amp": 8},
            "loss_kwh",
            0.03,
            _L(
                "Read 'Conversion losses' from the results.",
                "Нәтижеден «Түрлендіру шығындары» мәнін оқыңыз.",
            ),
        ),
        number(
            "q4",
            _L(
                "10 kWh are sent into the battery with η = 0.95 per half-cycle. Energy stored (kWh)?",
                "Батареяға 10 кВт·сағ жіберілді, жарты цикл ПӘК η = 0.95. Жинақталған энергия (кВт·сағ)?",
            ),
            9.5,
            0.05,
            _L("Stored = η · 10 = 9.5 kWh.", "Жинақталғаны = η · 10 = 9.5 кВт·сағ."),
        ),
        choice(
            "q5",
            _L(
                "With η = 0.95 per half-cycle, the round-trip efficiency is about…",
                "Жарты цикл η = 0.95 болса, толық цикл ПӘК шамамен…",
            ),
            [_L("0.90", "0.90"), _L("0.95", "0.95"), _L("1.00", "1.00"), _L("0.50", "0.50")],
            0,
            _L(
                "Charging and discharging each lose 5 %: 0.95² ≈ 0.90.",
                "Зарядта да, разрядта да 5 % жоғалады: 0.95² ≈ 0.90.",
            ),
        ),
    ],
    "lab_shared_energy": [
        choice(
            "q1",
            _L("In this lab, shared energy is…", "Бұл зертханада бөлісілген энергия дегеніміз…"),
            [
                _L(
                    "surplus of some homes used by other homes in the same hour",
                    "кейбір үйлердің артығын сол сағатта басқа үйлер тұтынуы",
                ),
                _L("energy exported to the grid", "желіге экспортталған энергия"),
                _L("energy stored in the battery", "батареяда жинақталған энергия"),
                _L("each home's own PV use", "әр үйдің өз PV-ін тұтынуы"),
            ],
            0,
            _L(
                "Matching is hour by hour, before the battery and the grid.",
                "Сәйкестендіру сағат сайын, батарея мен желіден бұрын жасалады.",
            ),
        ),
        choice(
            "q2",
            _L(
                "Every home has PV and they all have surplus at the same hours. Shared energy is…",
                "Барлық үйде PV бар, бәрінің артығы бір сағаттарда. Бөлісілген энергия…",
            ),
            [
                _L(
                    "close to zero — nobody needs the surplus then",
                    "нөлге жуық — ол кезде артық ешкімге керек емес",
                ),
                _L("at its maximum", "максимал"),
                _L("equal to the export", "экспортқа тең"),
                _L("equal to the import", "импортқа тең"),
            ],
            0,
            _L(
                "Sharing needs a deficit somewhere at the same time: mix prosumers and consumers.",
                "Бөлісу үшін сол уақытта біреуде тапшылық болуы керек: өндірушілер мен тұтынушыларды араластырыңыз.",
            ),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. How much energy is shared (kWh)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Қанша энергия бөлісілді (кВт·сағ)?",
            ),
            {
                "n_users": 4,
                "pv_users": 2,
                "panels": 40,
                "peak": 4,
                "bat": 30,
                "dod": 0.8,
                "price_import": 0.12,
                "price_export": 0.06,
                "weather": "sample",
            },
            "shared_kwh",
            0.02,
            _L(
                "Read 'Shared energy' from the results.",
                "Нәтижеден «Бөлісілген энергия» мәнін оқыңыз.",
            ),
        ),
        number(
            "q4",
            _L(
                "c_imp = 0.12 $/kWh, E_import = 50 kWh, c_exp = 0.06 $/kWh, E_export = 10 kWh. Net bill ($)?",
                "c_imp = 0.12 $/кВт·сағ, E_import = 50, c_exp = 0.06 $/кВт·сағ, E_export = 10 кВт·сағ. Таза төлем ($)?",
            ),
            5.4,
            0.05,
            _L("B = 6.0 − 0.6 = 5.4 $.", "B = 6.0 − 0.6 = 5.4 $."),
        ),
        choice(
            "q5",
            _L("A bigger community battery mostly…", "Қауымдастық батареясын үлкейту негізінен…"),
            [
                _L(
                    "cuts evening import; the pre-battery shared energy stays the same",
                    "кешкі импортты азайтады; батареяға дейінгі бөлісу өзгермейді",
                ),
                _L("raises the shared energy", "бөлісілген энергияны арттырады"),
                _L("raises the PV output", "PV өндірісін арттырады"),
                _L("raises the import", "импортты арттырады"),
            ],
            0,
            _L(
                "Sharing is matched before the battery; compare bat = 0 and bat = 100 in the lab.",
                "Бөлісу батареяға дейін есептеледі; зертханада bat = 0 және 100 салыстырыңыз.",
            ),
        ),
    ],
    "lab_rec_finance": [
        number(
            "q1",
            _L(
                "CAPEX 80 000 $, 120 000 kWh a year at 0.10 $/kWh, no O&M. Simple payback (years)?",
                "CAPEX 80 000 $, жылына 120 000 кВт·сағ, 0.10 $/кВт·сағ, пайдалану шығыны жоқ. Қарапайым өтелу (жыл)?",
            ),
            6.67,
            0.05,
            _L("80 000 / 12 000 = 6.67 years.", "80 000 / 12 000 = 6.67 жыл."),
        ),
        choice(
            "q2",
            _L("Raising the discount rate…", "Дисконт мөлшерлемесін арттыру…"),
            [
                _L("lowers the NPV", "NPV-ні азайтады"),
                _L("raises the NPV", "NPV-ні арттырады"),
                _L("does not change the NPV", "NPV-ні өзгертпейді"),
                _L("changes the payback", "өтелу мерзімін өзгертеді"),
            ],
            0,
            _L("Future savings are worth less today.", "Болашақ үнемнің бүгінгі құны азаяды."),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What is the NPV ($)?",
                "Зертхананы осы параметрлермен іске қосыңыз. NPV қанша ($)?",
            ),
            {"capex": 80000, "gen": 120000, "price": 0.10, "opex": 2000, "life": 20, "rate": 0.05},
            "npv",
            0.01,
            _L("Read 'NPV' from the results.", "Нәтижеден «NPV» мәнін оқыңыз."),
        ),
        choice(
            "q4",
            _L(
                "The IRR is the discount rate at which…",
                "IRR — бұл қандай жағдайдағы дисконт мөлшерлемесі?",
            ),
            [
                _L("NPV = 0", "NPV = 0"),
                _L("payback = 1 year", "өтелу = 1 жыл"),
                _L("LCOE = 0", "LCOE = 0"),
                _L("CAPEX is doubled", "CAPEX екі еселенеді"),
            ],
            0,
            _L(
                "Find where the lab's NPV curve crosses zero.",
                "Зертханадағы NPV қисығы нөлді қиятын нүктені табыңыз.",
            ),
        ),
        choice(
            "q5",
            _L(
                "LCOE is below the energy price. This means…",
                "LCOE энергия бағасынан төмен. Бұл нені білдіреді?",
            ),
            [
                _L(
                    "each kWh costs less to produce than it earns",
                    "әр кВт·сағ-ты өндіру құны табысынан аз",
                ),
                _L("the project loses money", "жоба шығынға батады"),
                _L("the panels are too small", "панельдер тым кішкентай"),
                _L("the IRR is zero", "IRR нөлге тең"),
            ],
            0,
            _L("LCOE is the lifetime cost per kWh.", "LCOE — бір кВт·сағ-тың өмірлік құны."),
        ),
    ],
    "lab_grid_impact": [
        choice(
            "q1",
            _L(
                "High PV export on a long feeder causes…",
                "Ұзын желіде PV-дің жоғары экспорты неге әкеледі?",
            ),
            [
                _L(
                    "voltage rise toward the end of the feeder",
                    "желі соңына қарай кернеудің көтерілуіне",
                ),
                _L("voltage drop at the transformer", "трансформаторда кернеудің түсуіне"),
                _L("lower frequency", "жиіліктің төмендеуіне"),
                _L("no change", "өзгеріссіз"),
            ],
            0,
            _L(
                "Power flowing back through the cable raises the voltage: ΔV ≈ (R·P + X·Q)/V.",
                "Кабель арқылы кері ағатын қуат кернеуді көтереді: ΔV ≈ (R·P + X·Q)/V.",
            ),
        ),
        number(
            "q2",
            _L(
                "|V| = 0.42 kV, V_nom = 0.40 kV. V in per unit?",
                "|V| = 0.42 кВ, V_nom = 0.40 кВ. Кернеу per unit-те?",
            ),
            1.05,
            0.005,
            _L("V_pu = 0.42 / 0.40 = 1.05.", "V_pu = 0.42 / 0.40 = 1.05."),
        ),
        run(
            "q3",
            _L(
                "Run the lab with these settings. What is the highest voltage in the day (pu)?",
                "Зертхананы осы параметрлермен іске қосыңыз. Тәуліктегі ең жоғары кернеу қанша (pu)?",
            ),
            {
                "houses": 12,
                "length": 800,
                "cable": "nayy_4x50",
                "pv_kw": 8,
                "load_kw": 3,
                "pf": 1.0,
                "v_source": 1.02,
            },
            "v_max_pu",
            0.003,
            _L(
                "Read 'Highest voltage in the day'. It exceeds the 1.10 pu limit.",
                "«Тәуліктегі ең жоғары кернеу» мәнін оқыңыз. Ол 1.10 pu шегінен асады.",
            ),
            rel=False,
        ),
        choice(
            "q4",
            _L(
                "The PV inverters absorb reactive power (power factor 0.9). The voltage rise…",
                "PV инверторлары реактивті қуат сіңіреді (қуат коэффициенті 0.9). Кернеудің көтерілуі…",
            ),
            [
                _L("decreases", "азаяды"),
                _L("increases", "артады"),
                _L("does not change", "өзгермейді"),
                _L("becomes a voltage drop at noon", "түсте кернеу түсуіне айналады"),
            ],
            0,
            _L(
                "Q < 0 makes the X·Q term negative and offsets R·P.",
                "Q < 0 болғанда X·Q мүшесі теріс болып, R·P-ны теңгереді.",
            ),
        ),
        choice(
            "q5",
            _L(
                "Which change lowers the voltage rise the most for the same export?",
                "Экспорт бірдей болса, кернеудің көтерілуін қайсы өзгеріс көбірек азайтады?",
            ),
            [
                _L("A thicker cable (lower R)", "Жуанырақ кабель (R аз)"),
                _L("A longer feeder", "Ұзынырақ желі"),
                _L("More houses with PV", "PV-сі бар үйлер көбірек"),
                _L("A higher transformer voltage", "Трансформатор кернеуі жоғарырақ"),
            ],
            0,
            _L(
                "ΔV is proportional to R; compare 4×50 and 4×150 mm² in the lab.",
                "ΔV R-ге пропорционал; зертханада 4×50 және 4×150 мм² салыстырыңыз.",
            ),
        ),
    ],
    "lab_inverter_wiring": [
        part3d(
            "q1",
            _L(
                "Tap the PV array DC isolator in the model.",
                "Модельде PV массивінің DC ажыратқышын басыңыз.",
            ),
            "dc_isolator",
            _L(
                "The grey box on the left, labelled 'PV Array DC Isolator'.",
                "Сол жақтағы 'PV Array DC Isolator' деп жазылған сұр қорап.",
            ),
        ),
        part3d(
            "q2",
            _L(
                "Tap the device that counts the energy delivered to the grid.",
                "Желіге берілген энергияны санайтын құрылғыны басыңыз.",
            ),
            "generation_meter",
            _L(
                "The generation meter on the right-hand rail: 'Single Phase Watt Hour Meter'.",
                "Оң жақ рельстегі генерация есептегіші: 'Single Phase Watt Hour Meter'.",
            ),
        ),
        part3d(
            "q3",
            _L(
                "Before the DC plugs may be pulled, the AC supply must be switched off. Tap the device you switch off.",
                "DC ашаларын суырмас бұрын AC қоректі ажырату керек. Ажырататын құрылғыны басыңыз.",
            ),
            "ac_isolator",
            _L(
                "The rotary AC isolator next to the meter. The inverter's label says: turn off the AC supply first.",
                "Есептегіштің жанындағы айналмалы AC ажыратқыш. Инвертор жапсырмасы: алдымен AC қоректі өшіріңіз.",
            ),
        ),
        choice(
            "q4",
            _L(
                "The inverter display reads 'DC polarity error'. What is wrong?",
                "Инвертор экранында 'DC полярлық қатесі'. Не бұзылған?",
            ),
            [
                _L(
                    "PV+ and PV− are swapped at the inverter's DC inputs",
                    "PV+ пен PV− инвертордың DC кірістерінде ауысқан",
                ),
                _L("The AC isolator is OFF", "AC ажыратқыш ажыратулы"),
                _L("The data logger is unplugged", "Деректер логгері суырылған"),
                _L("The meter is broken", "Есептегіш бұзылған"),
            ],
            0,
            _L(
                "Swap the MC4 plugs so PV+ lands on DC+ (red tag).",
                "PV+ DC+-ке (қызыл белгі) түсетіндей MC4 ашаларын ауыстырыңыз.",
            ),
        ),
        choice(
            "q5",
            _L(
                "The meter is counting but the monitoring app shows the plant offline. Most likely…",
                "Есептегіш санап тұр, бірақ мониторинг қосымшасы станцияны офлайн көрсетеді. Себебі…",
            ),
            [
                _L("the Wi-Fi data logger is unplugged", "Wi-Fi деректер логгері суырылған"),
                _L("the DC isolator is OFF", "DC ажыратқыш ажыратулы"),
                _L("PV polarity is reversed", "PV полярлығы кері"),
                _L("the grid is lost", "желі жоқ"),
            ],
            0,
            _L(
                "Production needs no logger; only the data link does.",
                "Өндіріске логгер қажет емес; ол тек деректер байланысына керек.",
            ),
        ),
        choice(
            "q6",
            _L(
                "Safe order before working on the DC cables:",
                "DC кабельдерінде жұмыс істеу алдындағы қауіпсіз рет:",
            ),
            [
                _L(
                    "AC isolator OFF, then DC isolator OFF, then unplug",
                    "AC ажыратқыш OFF, сосын DC ажыратқыш OFF, сосын ашаны суыру",
                ),
                _L("Unplug the DC cables first", "Алдымен DC кабельдерін суыру"),
                _L("DC isolator OFF only", "Тек DC ажыратқышты OFF ету"),
                _L("No isolation is needed at night", "Түнде ажыратудың қажеті жоқ"),
            ],
            0,
            _L(
                "Stop the current (AC off), isolate the array (DC off), then disconnect.",
                "Токты тоқтату (AC off), массивті ажырату (DC off), сосын ажырату.",
            ),
        ),
        fix(
            "q7",
            _L(
                "This system does not export. Find and fix every fault in the model.",
                "Бұл жүйе желіге қуат бермейді. Модельдегі барлық ақауды тауып, түзетіңіз.",
            ),
            {"dc_isolator": "off", "pe": "open"},
            _L(
                "The DC isolator was OFF and the PE conductor was not connected.",
                "DC ажыратқыш ажыратулы, PE сымы қосылмаған еді.",
            ),
        ),
    ],
}


def _loc(field: Any, lang: str) -> str:
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field or "")


@lru_cache(maxsize=None)
def _run_answer(lab_id: str, qid: str) -> float:
    q = _question(lab_id, qid)
    value = metric_value(run_lab(lab_id, q["params"]), q["metric"])
    if value is None:
        raise ValueError(f"{lab_id}/{qid}: metric {q['metric']} has no value")
    return float(value)


def _order(lab_id: str, qid: str, n: int) -> list[int]:
    """Display order of a question's choices: shuffled, but the same on every
    client and every request (the bank lists the correct choice first)."""
    seed = int(hashlib.sha256(f"{lab_id}/{qid}".encode()).hexdigest()[:8], 16)
    order = list(range(n))
    random.Random(seed).shuffle(order)
    return order


def _question(lab_id: str, qid: str) -> dict[str, Any]:
    for q in TESTS[lab_id]:
        if q["id"] == qid:
            return q
    raise KeyError(qid)


def _params_display(lab_id: str, params: dict[str, Any], lang: str) -> list[dict[str, Any]]:
    """The run settings as label / value rows, in the lab's own parameter order."""
    rows = []
    specs = {s["key"]: s for s in list_params(lab_id)}
    for key, value in validate_params(lab_id, params).items():
        spec = specs[key]
        if spec["kind"] == "select":
            label = next(_loc(o["label"], lang) for o in spec["options"] if o["id"] == value)
            shown = label
        else:
            shown = f"{value:g}" + (f" {spec['unit']}" if spec.get("unit") else "")
        rows.append({"key": key, "label": _loc(spec["label"], lang), "value": shown})
    return rows


def public_test(lab_id: str, lang: str = "kk") -> dict[str, Any]:
    """Questions for the client, without answers."""
    lang = "kk" if lang == "kk" else "en"
    if lab_id not in TESTS:
        raise KeyError(lab_id)
    out = []
    for q in TESTS[lab_id]:
        item: dict[str, Any] = {"id": q["id"], "kind": q["kind"], "prompt": _loc(q["prompt"], lang)}
        if q["kind"] == "choice":
            item["choices"] = [
                _loc(q["choices"][i], lang) for i in _order(lab_id, q["id"], len(q["choices"]))
            ]
        elif q["kind"] == "number":
            item["unit"] = q.get("unit", "")
        elif q["kind"] == "run":
            item["params"] = validate_params(lab_id, q["params"])
            item["params_display"] = _params_display(lab_id, q["params"], lang)
            item["metric"] = q["metric"]
        elif q["kind"] == "fix":
            item["initial"] = {**CORRECT, **q["faults"]}
        out.append(item)
    return {"lab_id": lab_id, "lang": lang, "pass_percent": PASS_PERCENT, "questions": out}


def _num(value: Any) -> float | None:
    try:
        f = float(str(value).replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _check(lab_id: str, q: dict[str, Any], answer: Any) -> tuple[bool, str]:
    """(correct, expected answer shown after grading)."""
    kind = q["kind"]
    if kind == "choice":
        order = _order(lab_id, q["id"], len(q["choices"]))
        try:
            shown = int(answer)
            picked = order[shown] if 0 <= shown < len(order) else -1
        except (TypeError, ValueError):
            picked = -1
        return picked == q["correct"], str(order.index(q["correct"]))
    if kind in ("number", "run"):
        expected = q["answer"] if kind == "number" else _run_answer(lab_id, q["id"])
        got = _num(answer)
        tol = q["tol"] * abs(expected) if q.get("rel") else q["tol"]
        return got is not None and abs(got - expected) <= max(tol, 1e-9), f"{expected:.4g}"
    if kind == "part3d":
        return str(answer or "") == q["part"], q["part"]
    if kind == "fix":
        board = answer if isinstance(answer, dict) else {}
        return bool(grade_wiring(board)["ok"]) and set(board) >= set(CONTROLS), "all_fixed"
    raise ValueError(f"unknown question kind {kind}")


def grade_test(lab_id: str, answers: dict[str, Any], lang: str = "kk") -> dict[str, Any]:
    lang = "kk" if lang == "kk" else "en"
    if lab_id not in TESTS:
        raise KeyError(lab_id)
    details = []
    for q in TESTS[lab_id]:
        ok, expected = _check(lab_id, q, (answers or {}).get(q["id"]))
        details.append(
            {
                "id": q["id"],
                "correct": ok,
                "expected": expected,
                "explain": _loc(q["explain"], lang),
            }
        )
    score = sum(1 for d in details if d["correct"])
    total = len(details)
    percent = round(100.0 * score / total, 1)
    return {
        "lab_id": lab_id,
        "score": score,
        "total": total,
        "percent": percent,
        "passed": percent >= PASS_PERCENT,
        "pass_percent": PASS_PERCENT,
        "details": details,
    }


def correct_answers(lab_id: str) -> dict[str, Any]:
    """A full-marks answer sheet (tests and the UI self-check use it)."""
    out: dict[str, Any] = {}
    for q in TESTS[lab_id]:
        k = q["kind"]
        if k == "choice":
            out[q["id"]] = _order(lab_id, q["id"], len(q["choices"])).index(q["correct"])
        elif k == "number":
            out[q["id"]] = q["answer"]
        elif k == "run":
            out[q["id"]] = _run_answer(lab_id, q["id"])
        elif k == "part3d":
            out[q["id"]] = q["part"]
        elif k == "fix":
            out[q["id"]] = dict(CORRECT)
    return out
