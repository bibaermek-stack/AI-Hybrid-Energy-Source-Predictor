"""
Quizzes for EcoPredict Learn module.

Each quiz: id, title_en/kk, questions[{id, prompt_en/kk, choices_en/kk, correct_index, explain_en/kk}]
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def _t(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


def _q(
    qid: str,
    prompt: dict[str, str],
    choices: list[dict[str, str]],
    correct: int,
    explain: dict[str, str],
) -> dict[str, Any]:
    return {
        "id": qid,
        "prompt": prompt,
        "choices": choices,
        "correct_index": correct,
        "explain": explain,
    }


QUIZ_BANK: dict[str, dict[str, Any]] = {
    "lstm_basics": {
        "id": "lstm_basics",
        "title": _t("Forecasting basics", "Болжау негіздері"),
        "questions": [
            _q(
                "q1",
                _t(
                    "Which features does EcoPredict solar RF commonly use?",
                    "EcoPredict solar RF қандай белгілерді қолданады?",
                ),
                [
                    _t("Only wind speed", "Тек жел жылдамдығы"),
                    _t(
                        "Irradiation, temperatures, hour/day/month",
                        "Сәуле, температуралар, сағат/күн/ай",
                    ),
                    _t("Only battery SOC", "Тек батарея SOC"),
                    _t("Only electricity price", "Тек электр бағасы"),
                ],
                1,
                _t(
                    "Production solar_model.pkl uses irradiance, ambient/module temp, and calendar features.",
                    "solar_model.pkl сәуле, орта/панель температурасы және күнтізбе белгілерін қолданады.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "A sequence model for next-hour power typically looks at:",
                    "Келесі сағат қуаты үшін тізбекті модель әдетте қарайды:",
                ),
                [
                    _t("A single random number", "Бір кездейсоқ сан"),
                    _t("Past hours of weather/features", "Өткен сағаттардың белгілері"),
                    _t("Only the inverter SN", "Тек инвертор SN"),
                    _t("Only CAPEX", "Тек CAPEX"),
                ],
                1,
                _t(
                    "Time-series models consume a window of past observations.",
                    "Уақыт қатары модельдері өткен бақылаулар терезесін алады.",
                ),
            ),
            _q(
                "q3",
                _t(
                    "If module temperature rises a lot at fixed irradiance, PV efficiency usually:",
                    "Сәуле тұрақты, панель ыстығы өссе, PV тиімділігі әдетте:",
                ),
                [
                    _t("Increases sharply", "Күрт өседі"),
                    _t("Stays exactly the same", "Мүлдем өзгермейді"),
                    _t("Decreases slightly", "Сәл төмендейді"),
                    _t("Becomes infinite", "Шексіз болады"),
                ],
                2,
                _t(
                    "Crystalline silicon loses roughly 0.3–0.5% efficiency per °C above 25°C.",
                    "Кристалды кремний 25°C-тан жоғары әр °C сайын ~0.3–0.5% тиімділік жоғалтады.",
                ),
            ),
        ],
    },
    "yolo_basics": {
        "id": "yolo_basics",
        "title": _t("Vision & faults", "Көру және ақаулар"),
        "questions": [
            _q(
                "q1",
                _t("YOLO is mainly used to:", "YOLO негізінен:"),
                [
                    _t("Predict electricity price", "Электр бағасын болжау"),
                    _t("Detect and locate objects/defects in images", "Суретте нысан/ақауды табу"),
                    _t("Size a battery bank", "Батареяны өлшеу"),
                    _t("Replace SCADA forever", "SCADA-ны толық алмастыру"),
                ],
                1,
                _t(
                    "YOLO draws bounding boxes around defects in one pass.",
                    "YOLO бір өтуде ақауларға бокс салады.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "Dust soiling in southern Kazakhstan typically:",
                    "Оңтүстік Қазақстандағы шаң әдетте:",
                ),
                [
                    _t("Increases panel output", "Өнімділікті арттырады"),
                    _t("Can reduce yield several percent or more", "Өнімді бірнеше %+ төмендетеді"),
                    _t("Has zero effect", "Әсері жоқ"),
                    _t("Only affects wind turbines", "Тек жел турбинасына әсер етеді"),
                ],
                1,
                _t(
                    "Soiling blocks irradiance; cleaning recovers energy.",
                    "Шаң сәулені бөгейді; тазалау энергияны қайтарады.",
                ),
            ),
        ],
    },
    "optimization_basics": {
        "id": "optimization_basics",
        "title": _t("Optimization", "Оңтайландыру"),
        "questions": [
            _q(
                "q1",
                _t(
                    "Battery SOC constraint means:",
                    "Батарея SOC шектеуі дегеніміз:",
                ),
                [
                    _t("SOC can be anything", "SOC кез келген бола алады"),
                    _t("Energy stored stays within min/max band", "Жинақталған энергия min/max арасында"),
                    _t("Grid price is fixed", "Grid бағасы тұрақты"),
                    _t("Wind speed is zero", "Жел жылдамдығы нөл"),
                ],
                1,
                _t(
                    "SOC dynamics keep storage physically feasible.",
                    "SOC динамикасы сақтауды физикалық мүмкін етеді.",
                ),
            ),
            _q(
                "q2",
                _t("min_co2 mode mainly tries to:", "min_co2 режимі негізінен:"),
                [
                    _t("Maximize grid import", "Grid import-ты максимумдау"),
                    _t("Reduce dirty grid electricity use", "Лас grid электрін азайту"),
                    _t("Ignore the battery", "Батареяны елемеу"),
                    _t("Turn off solar forever", "Күнді мәңгі өшіру"),
                ],
                1,
                _t(
                    "CO₂ is attributed to grid imports in EcoPredict’s LP.",
                    "EcoPredict LP-да CO₂ grid import-қа байланысты.",
                ),
            ),
        ],
    },
    "xai_rag": {
        "id": "xai_rag",
        "title": _t("XAI & RAG", "XAI және RAG"),
        "questions": [
            _q(
                "q1",
                _t("Feature importance helps you:", "Feature importance көмектеседі:"),
                [
                    _t("See which inputs drive a prediction", "Қай кіріс болжамды қозғайтынын көру"),
                    _t("Delete the dataset", "Датасетті жою"),
                    _t("Increase CAPEX only", "Тек CAPEX өсіру"),
                    _t("Hide model errors", "Модель қателерін жасыру"),
                ],
                0,
                _t(
                    "Importance ranks inputs by contribution to the model.",
                    "Importance кірістерді үлесі бойынша сұрыптайды.",
                ),
            ),
            _q(
                "q2",
                _t("RAG stands for:", "RAG дегеніміз:"),
                [
                    _t("Random Average Guess", "Random Average Guess"),
                    _t(
                        "Retrieval-Augmented Generation (search docs, then answer)",
                        "Retrieval-Augmented Generation (құжат іздеу, сосын жауап)",
                    ),
                    _t("Rapid Auto Grid", "Rapid Auto Grid"),
                    _t("Rusty Analog Gauge", "Rusty Analog Gauge"),
                ],
                1,
                _t(
                    "RAG retrieves knowledge snippets before answering.",
                    "RAG жауаптан бұрын білім үзіндісін алады.",
                ),
            ),
        ],
    },
    "sustainability": {
        "id": "sustainability",
        "title": _t("Sustainability", "Тұрақтылық"),
        "questions": [
            _q(
                "q1",
                _t("Self-consumption rate measures:", "Self-consumption rate өлшейді:"),
                [
                    _t("How much renewable is used on-site", "Жергілікті қолданылған ЖЭК үлесі"),
                    _t("Only inverter SN length", "Тек SN ұзындығы"),
                    _t("Cloud color", "Бұлт түсі"),
                    _t("Wi-Fi password strength", "Wi-Fi құпия сөз күші"),
                ],
                0,
                _t(
                    "It is renewable used locally divided by renewable available.",
                    "Жергілікті қолданылған / қолжетімді ЖЭК.",
                ),
            ),
        ],
    },
    "kz_case": {
        "id": "kz_case",
        "title": _t("Kazakhstan case", "ҚР кейсі"),
        "questions": [
            _q(
                "q1",
                _t(
                    "A practical response to dust in Turkistan is:",
                    "Түркістандағы шаңға практикалық жауап:",
                ),
                [
                    _t("Never clean panels", "Панельді ешқашан тазаламау"),
                    _t(
                        "Monitor yield and schedule cleaning after dust events",
                        "Өнімді қадағалап, шаңнан кейін тазалауды жоспарлау",
                    ),
                    _t("Only increase tariff", "Тек тарифті өсіру"),
                    _t("Disable forecasting", "Болжамды өшіру"),
                ],
                1,
                _t(
                    "O&M balances cleaning cost vs recovered energy.",
                    "O&M тазалау құны мен қайтарылған энергияны теңестіреді.",
                ),
            ),
        ],
    },
    # --- Lab reflection quizzes ---
    "lab_pv_physics_quiz": {
        "id": "lab_pv_physics_quiz",
        "title": _t("Lab: PV physics", "Зертхана: PV физика"),
        "questions": [
            _q(
                "q1",
                _t(
                    "If irradiance doubles at fixed temperature, ideal PV power roughly:",
                    "Температура тұрақты, сәуле екі еселенсе, идеал PV қуаты шамамен:",
                ),
                [
                    _t("Stays the same", "Өзгермейді"),
                    _t("Doubles", "Екі еселенеді"),
                    _t("Halves", "Екі есе азаяды"),
                    _t("Becomes zero", "Нөл болады"),
                ],
                1,
                _t(
                    "P ∝ G · A · η_eff under the simple model.",
                    "Қарапайым модельде P ∝ G · A · η_eff.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "Higher module temperature (γ > 0) typically makes power:",
                    "Жоғары панель температурасы (γ > 0) қуатты:",
                ),
                [
                    _t("Higher", "Жоғарылатады"),
                    _t("Lower", "Төмендетеді"),
                    _t("Undefined", "Анықталмаған"),
                    _t("Infinite", "Шексіз етеді"),
                ],
                1,
                _t(
                    "Temp coefficient reduces effective efficiency above 25°C.",
                    "Темп. коэффициент 25°C-тан жоғары тиімділікті төмендетеді.",
                ),
            ),
        ],
    },
    "lab_mppt_quiz": {
        "id": "lab_mppt_quiz",
        "title": _t("Lab: MPPT", "Зертхана: MPPT"),
        "questions": [
            _q(
                "q1",
                _t("P&O mainly adjusts:", "P&O негізінен реттейді:"),
                [
                    _t("Grid tariff", "Grid тарифін"),
                    _t("Operating voltage toward the power peak", "Қуат шыңына қарай кернеуді"),
                    _t("Battery DoD only", "Тек батарея DoD"),
                    _t("Latitude", "Ендікті"),
                ],
                1,
                _t(
                    "Perturb voltage and keep the direction that raises power.",
                    "Кернеуді ығыстырып, қуат өскен бағытты сақтайды.",
                ),
            ),
        ],
    },
    "lab_bess_soc_quiz": {
        "id": "lab_bess_soc_quiz",
        "title": _t("Lab: BESS SOC", "Зертхана: BESS SOC"),
        "questions": [
            _q(
                "q1",
                _t(
                    "When PV exceeds load, a healthy microgrid usually:",
                    "PV жүктемеден артық болса, сау микрожелі әдетте:",
                ),
                [
                    _t("Only imports more grid power", "Тек grid-тен көбірек импорттайды"),
                    _t("Charges the battery (if room)", "Батареяны зарядтайды (орын болса)"),
                    _t("Sets SOC to zero", "SOC-ты нөлге қояды"),
                    _t("Disables the inverter forever", "Инверторды мәңгі өшіреді"),
                ],
                1,
                _t(
                    "Surplus energy is stored before export.",
                    "Артық энергия экспортқа дейін жинақталады.",
                ),
            ),
        ],
    },
    "lab_microgrid_quiz": {
        "id": "lab_microgrid_quiz",
        "title": _t("Lab: microgrid dispatch", "Зертхана: микрожелі диспетчер"),
        "questions": [
            _q(
                "q1",
                _t(
                    "Self-consumption % mainly reflects:",
                    "Өз тұтыну % негізінен көрсетеді:",
                ),
                [
                    _t("How much PV was used on-site vs available", "Жергілікті қолданылған PV / қолжетімді PV"),
                    _t("Only panel color", "Тек панель түсі"),
                    _t("Wi-Fi strength", "Wi-Fi күші"),
                    _t("GPU temperature", "GPU температурасы"),
                ],
                0,
                _t(
                    "It is local renewable use divided by renewable available.",
                    "Жергілікті ЖЭК / қолжетімді ЖЭК.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "Raising evening load with a small battery tends to:",
                    "Кішкентай батареямен кешкі жүктемені өсіру әдетте:",
                ),
                [
                    _t("Reduce grid import", "Grid импортты азайтады"),
                    _t("Increase evening grid import", "Кешкі grid импортты өсіреді"),
                    _t("Remove the need for PV", "PV қажеттілігін жояды"),
                    _t("Force export forever", "Мәңгі экспортқа мәжбүрлейді"),
                ],
                1,
                _t(
                    "Deficit after battery discharge is covered by the grid.",
                    "Батареядан кейінгі жетіспеуді grid жабады.",
                ),
            ),
        ],
    },
    "lab_heuristic_vs_pulp_quiz": {
        "id": "lab_heuristic_vs_pulp_quiz",
        "title": _t("Lab: heuristic vs PuLP", "Зертхана: эвристика vs PuLP"),
        "questions": [
            _q(
                "q1",
                _t(
                    "A rule-based balancer optimizes mainly:",
                    "Ережелік балансир негізінен оңтайландырады:",
                ),
                [
                    _t("Instant priority rules each step", "Әр қадамда лездегі басымдық ережелері"),
                    _t("Full-horizon LP with prices/CO₂", "Баға/CO₂ бар толық горизонт LP"),
                    _t("Only YOLO boxes", "Тек YOLO бокстары"),
                    _t("Nothing at all", "Ештеңе"),
                ],
                0,
                _t(
                    "PuLP looks ahead; heuristic reacts step-by-step.",
                    "PuLP алға қарайды; эвристика қадам-қадам әрекет етеді.",
                ),
            ),
        ],
    },
    "lab_pv_yield_quiz": {
        "id": "lab_pv_yield_quiz",
        "title": _t("Lab: PV yield", "Зертхана: PV yield"),
        "questions": [
            _q(
                "q1",
                _t("Daily PV yield (kWh) is approximately:", "Тәуліктік PV yield (кВт·сағ) шамамен:"),
                [
                    _t("Peak kW only", "Тек шың кВт"),
                    _t("Integral of power over hours", "Қуаттың сағат бойынша интегралы"),
                    _t("Always equal to CAPEX", "Әрқашан CAPEX-ке тең"),
                    _t("Wind speed squared", "Жел жылдамдығының квадраты"),
                ],
                1,
                _t("Sum of hourly kW × 1 h ≈ kWh for hourly steps.", "Сағаттық кВт қосындысы ≈ кВт·сағ."),
            ),
        ],
    },
    "lab_load_shape_quiz": {
        "id": "lab_load_shape_quiz",
        "title": _t("Lab: load shape", "Зертхана: жүктеме"),
        "questions": [
            _q(
                "q1",
                _t("Domestic load often peaks in:", "Тұрмыстық жүктеме жиі шыңдайды:"),
                [
                    _t("Only at noon solar peak", "Тек түскі күн шыңында"),
                    _t("Morning and/or evening occupancy hours", "Таңғы және/немесе кешкі белсенділікте"),
                    _t("Never at night valley", "Ешқашан түнгі аңғарда емес — әрқашан максимум"),
                    _t("Only on leap years", "Тек кібісе жылда"),
                ],
                1,
                _t("Occupancy-driven peaks often misalign with solar noon.", "Тұтыну шыңдары күн түсімен сәйкес келмеуі мүмкін."),
            ),
        ],
    },
    "lab_bess_community_quiz": {
        "id": "lab_bess_community_quiz",
        "title": _t("Lab: BESS DoD", "Зертхана: BESS DoD"),
        "questions": [
            _q(
                "q1",
                _t("Higher DoD (deeper usable band) means:", "Жоғары DoD (тереңірек диапазон) дегеніміз:"),
                [
                    _t("Higher E_min floor only", "Тек жоғары E_min едені"),
                    _t("Lower minimum SOC floor (more usable energy)", "Төменірек min SOC (көбірек пайдалы энергия)"),
                    _t("Battery is removed", "Батарея алынады"),
                    _t("η becomes zero", "η нөл болады"),
                ],
                1,
                _t("E_min = E_cap · (1 − DoD).", "E_min = E_cap · (1 − DoD)."),
            ),
        ],
    },
    "lab_shared_energy_quiz": {
        "id": "lab_shared_energy_quiz",
        "title": _t("Lab: shared energy", "Зертхана: бөліскен энергия"),
        "questions": [
            _q(
                "q1",
                _t(
                    "In this lab, shared energy is mainly:",
                    "Осы зертханада бөліскен энергия негізінен:",
                ),
                [
                    _t("Matching residual surplus to residual deficit among users", "Пайдаланушылар арасында қалдық артықты жетіспеуге сәйкестендіру"),
                    _t("Only grid import", "Тек grid импорт"),
                    _t("CAPEX depreciation", "CAPEX амортизациясы"),
                    _t("YOLO mAP", "YOLO mAP"),
                ],
                0,
                _t(
                    "After individual self-consumption, the pool match is shared energy.",
                    "Жеке өз тұтынудан кейін пул сәйкестігі — бөліскен энергия.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "If battery DoD increases, pre-battery shared energy usually:",
                    "Батарея DoD өссе, батареяға дейінгі бөліскен энергия әдетте:",
                ),
                [
                    _t("Always doubles automatically", "Әрқашан автоматты екі еселенеді"),
                    _t("Does not change (shared is computed before BESS)", "Өзгермейді (shared BESS-ке дейін есептеледі)"),
                    _t("Becomes negative forever", "Мәңгі теріс болады"),
                    _t("Deletes all users", "Барлық пайдаланушыны жояды"),
                ],
                1,
                _t(
                    "DoD affects residual grid/BESS after the shared match step.",
                    "DoD shared қадамынан кейінгі BESS/grid-ке әсер етеді.",
                ),
            ),
        ],
    },
    "lab_rec_finance_quiz": {
        "id": "lab_rec_finance_quiz",
        "title": _t("Lab: REC finance", "Зертхана: REC қаржы"),
        "questions": [
            _q(
                "q1",
                _t("Raising the discount rate typically:", "Дисконт мөлшерлемесін өсіру әдетте:"),
                [
                    _t("Increases NPV", "NPV-ны өсіреді"),
                    _t("Decreases NPV of future savings", "Болашақ үнемнің NPV-сын төмендетеді"),
                    _t("Sets IRR to 100% always", "IRR-ді әрқашан 100% етеді"),
                    _t("Removes CAPEX", "CAPEX-ті алып тастайды"),
                ],
                1,
                _t(
                    "Future cash flows are discounted more heavily.",
                    "Болашақ ағындар күштірек дисконтталады.",
                ),
            ),
        ],
    },
    "lab_grid_impact_quiz": {
        "id": "lab_grid_impact_quiz",
        "title": _t("Lab: power flow (offline)", "Зертхана: қуат ағыны (офлайн)"),
        "questions": [
            _q(
                "q1",
                _t(
                    "High PV export on a weak feeder often causes:",
                    "Әлсіз фидерде жоғары PV экспорт жиі тудырады:",
                ),
                [
                    _t("Local voltage rise", "Жергілікті кернеудің өсуі"),
                    _t("Negative speed of light", "Жарық жылдамдығының теріс болуы"),
                    _t("CAPEX to become zero", "CAPEX-тің нөл болуы"),
                    _t("Removal of all loads", "Барлық жүктеменің жойылуы"),
                ],
                0,
                _t(
                    "Reverse power flow can push bus voltage above nominal.",
                    "Кері қуат ағыны шина кернеуін номиналдан жоғарылатуы мүмкін.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "In EcoPradict, pandapower should be installed via:",
                    "EcoPradict-та pandapower қалай орнатылады:",
                ),
                [
                    _t("Always in production Docker by default", "Әрқашан production Docker-де әдепкі"),
                    _t("Optional extra [sim-cacer] / offline notebook", "Опционалды [sim-cacer] / офлайн notebook"),
                    _t("Only through xlwings", "Тек xlwings арқылы"),
                    _t("Never, it is banned forever", "Ешқашан, мүлде тыйым салынған"),
                ],
                1,
                _t(
                    "Docker stays lean; advanced course uses pip extra + Jupyter.",
                    "Docker жеңіл қалады; advanced курс pip extra + Jupyter қолданады.",
                ),
            ),
        ],
    },
    "lab_inverter_wiring_quiz": {
        "id": "lab_inverter_wiring_quiz",
        "title": _t("Lab: inverter 3D wiring", "Зертхана: инвертор 3D сым"),
        "questions": [
            _q(
                "q1",
                _t(
                    "Reversed DC polarity on the inverter usually requires:",
                    "Инверторда кері DC полярлық әдетте талап етеді:",
                ),
                [
                    _t("Swapping DC+ and DC− cables to match PV polarity", "DC+ мен DC−-ны PV полярлығына сәйкес ауыстыру"),
                    _t("Deleting Solarman SN", "Solarman SN жою"),
                    _t("Only changing discount rate", "Тек дисконтты өзгерту"),
                    _t("Turning off all PE forever", "PE-ны мәңгі өшіру"),
                ],
                0,
                _t(
                    "Match PV+ → DC+, PV− → DC− per terminal map.",
                    "Терминал картасы бойынша PV+ → DC+, PV− → DC−.",
                ),
            ),
            _q(
                "q2",
                _t(
                    "A seated data logger primarily enables:",
                    "Тығыз қосылған data logger негізінен:",
                ),
                [
                    _t("Monitoring / telemetry to cloud apps", "Cloud қосымшаларына мониторинг / телеметрия"),
                    _t("Changing the speed of light", "Жарық жылдамдығын өзгерту"),
                    _t("Removing the need for PE", "PE қажеттілігін жою"),
                    _t("Infinite CAPEX", "Шексіз CAPEX"),
                ],
                0,
                _t(
                    "COM logger is communications; power path is separate.",
                    "COM logger — байланыс; қуат жолы бөлек.",
                ),
            ),
        ],
    },
}


def list_quizzes(lang: str = "en") -> list[dict[str, str]]:
    lang = "kk" if lang == "kk" else "en"
    return [{"id": qid, "title": q["title"][lang]} for qid, q in QUIZ_BANK.items()]


def get_quiz(quiz_id: str, lang: str = "en") -> dict[str, Any] | None:
    """Resolved quiz strings for UI."""
    raw = QUIZ_BANK.get(quiz_id)
    if not raw:
        return None
    lang = "kk" if lang == "kk" else "en"
    out: dict[str, Any] = {
        "id": raw["id"],
        "title": raw["title"][lang],
        "questions": [],
    }
    for q in raw["questions"]:
        out["questions"].append(
            {
                "id": q["id"],
                "prompt": q["prompt"][lang],
                "choices": [c[lang] for c in q["choices"]],
                "correct_index": q["correct_index"],
                "explain": q["explain"][lang],
            }
        )
    return out


def grade_quiz(quiz_id: str, answers: dict[str, int]) -> dict[str, Any]:
    """
    Grade answers map {question_id: choice_index}.

    Returns score, total, percent, details[].
    """
    raw = QUIZ_BANK.get(quiz_id)
    if not raw:
        return {"score": 0, "total": 0, "percent": 0.0, "details": [], "error": "unknown quiz"}

    details = []
    score = 0
    for q in raw["questions"]:
        qid = q["id"]
        correct = int(q["correct_index"])
        given = answers.get(qid)
        ok = given is not None and int(given) == correct
        if ok:
            score += 1
        details.append(
            {
                "id": qid,
                "correct": ok,
                "correct_index": correct,
                "given_index": given,
            }
        )
    total = len(raw["questions"])
    return {
        "score": score,
        "total": total,
        "percent": round(100.0 * score / total, 1) if total else 0.0,
        "details": details,
    }
