"""
Interactive theory lessons for EcoPredict AI (content layer, UI-agnostic).

Each lesson is a dict with:
  id, title_en, title_kk, level, minutes, sections[], key_takeaways[], related_quiz

Sections support types: text | bullets | formula | tip | case | tasks

Formulas: optional ``latex`` field (KaTeX / TeX) rendered via ``st.latex``;
bodies and task items may embed ``$inline$`` or ``$$display$$`` math.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

LESSON_IDS = (
    "lstm_forecasting",
    "yolo_faults",
    "hybrid_optimization",
    "xai_rag",
    "sustainable_management",
    "kz_case_study",
)


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


LESSONS: dict[str, dict[str, Any]] = {
    "lstm_forecasting": {
        "id": "lstm_forecasting",
        "title": _L(
            "How models forecast energy (time series)",
            "Энергияны қалай болжаймыз (уақыт қатары)",
        ),
        "level": _L("Beginner → Intermediate", "Бастауыш → Орта"),
        "minutes": 12,
        "related_quiz": "lstm_basics",
        "sections": [
            {
                "type": "text",
                "title": _L("Why time series?", "Неге уақыт қатары?"),
                "body": _L(
                    "Solar and wind power change every hour with weather and time of day. "
                    "A forecast uses recent history (irradiance, temperature, hour, day, month) "
                    "to estimate future AC power. EcoPredict production uses a RandomForest "
                    "on tabular features; LSTM networks are a classic deep-learning option "
                    "for sequences (24 past hours → next hour).",
                    "Күн мен жел қуаты ауа райы мен тәулік уақытына байланысты өзгереді. "
                    "Болжам соңғы тарихты (сәуле, температура, сағат, күн, ай) қолданып "
                    "келешек AC қуатын бағалайды. EcoPredict production-да RandomForest "
                    "қолданылады; LSTM — 24 сағаттық тізбектен келесі сағатты болжаудың "
                    "классикалық deep-learning нұсқасы.",
                ),
            },
            {
                "type": "bullets",
                "title": _L("LSTM idea (simplified)", "LSTM идеясы (қарапайым)"),
                "items": [
                    _L(
                        "Memory cell: remembers patterns across many hours (sunrise ramp, clouds).",
                        "Жад ұяшығы: көп сағаттық үлгілерді есте сақтайды (таңғы өсу, бұлт).",
                    ),
                    _L(
                        "Gates: decide what to forget, store, and output — useful for long dependencies.",
                        "Қақпалар: не ұмыту, не сақтау, не шығару — ұзақ тәуелділіктер үшін.",
                    ),
                    _L(
                        "Input shape often (batch, 24, 6 features) → one power prediction.",
                        "Кіріс пішіні: (batch, 24, 6 белгі) → бір қуат болжамы.",
                    ),
                ],
            },
            {
                "type": "formula",
                "title": _L("Feature → model", "Белгі → модель"),
                "latex": r"\widehat{P}_{AC} \approx f(G, T_{amb}, T_{mod}, h, d, m)",
                "body": _L(
                    r"RF (production): $\widehat{P}_{AC} \approx f(G, T_{amb}, T_{mod}, h, d, m)$.  "
                    r"LSTM-style: $\widehat{P}_{t} \approx g(X_{t-24},\ldots,X_{t-1})$.",
                    r"RF (production): $\widehat{P}_{AC} \approx f(G, T_{орта}, T_{панель}, h, d, m)$.  "
                    r"LSTM-стиль: $\widehat{P}_{t} \approx g(X_{t-24},\ldots,X_{t-1})$.",
                ),
            },
            {
                "type": "tasks",
                "title": _L("Student tasks", "Студент тапсырмалары"),
                "items": [
                    _L(
                        r"At fixed hour $h=12$, raise $G$ from $400$ to $900\,\mathrm{W/m}^2$ on Forecast — how does $\widehat{P}_{AC}$ change?",
                        r"Сағат $h=12$ тұрақты, Forecast-та $G$: $400 \to 900\,\mathrm{W/m}^2$ — $\widehat{P}_{AC}$ қалай өзгереді?",
                    ),
                    _L(
                        r"Write the relative change $\delta = (\widehat{P}_2-\widehat{P}_1)/\widehat{P}_1$ for your two runs.",
                        r"Екі іске қосу үшін $\delta = (\widehat{P}_2-\widehat{P}_1)/\widehat{P}_1$ есептеңіз.",
                    ),
                ],
            },
            {
                "type": "tip",
                "title": _L("Try it", "Байқап көріңіз"),
                "body": _L(
                    "Open the Forecast lab: raise irradiation and noon hours — predicted power rises. "
                    "Lower module temperature slightly increases efficiency in real PV physics.",
                    "Forecast зертханасында сәулені және түскі сағаттарды көтеріңіз — болжам өседі. "
                    "Панель температурасын төмендету нақты PV-да тиімділікті сәл арттырады.",
                ),
            },
        ],
        "key_takeaways": [
            _L("History + weather features drive forecasts.", "Тарих + ауа райы белгілері болжамды анықтайды."),
            _L("EcoPredict Forecast uses RandomForest in production.", "EcoPredict Forecast production-да RF қолданады."),
            _L("Always validate against real inverter telemetry.", "Әрдайым нақты инвертор телеметриясымен салыстырыңыз."),
        ],
    },
    "yolo_faults": {
        "id": "yolo_faults",
        "title": _L(
            "YOLO & CNN for solar panel faults",
            "YOLO және CNN: панель ақауларын анықтау",
        ),
        "level": _L("Intermediate", "Орта"),
        "minutes": 10,
        "related_quiz": "yolo_basics",
        "sections": [
            {
                "type": "text",
                "title": _L("Computer vision on panels", "Панельде компьютерлік көру"),
                "body": _L(
                    "Photos of PV modules can show cracks, bird droppings, dust, and hotspots. "
                    "CNN classifiers label an image (e.g. clean vs dirty). "
                    "YOLO-style detectors draw boxes around multiple defects in one frame.",
                    "PV фотоларында жарық, құс қалдығы, шаң, hotspot көрінеді. "
                    "CNN классификаторы суретті белгілейді (таза/кір). "
                    "YOLO бір кадрда бірнеше ақауға төртбұрыш салады.",
                ),
            },
            {
                "type": "bullets",
                "title": _L("Pipeline in EcoPredict", "EcoPredict құбыры"),
                "items": [
                    _L("Upload image on Fault Detection page.", "Fault Detection бетінде сурет жүктеңіз."),
                    _L("Model scores classes or boxes.", "Модель класс/бокс баллдарын береді."),
                    _L("Operator verifies on site before cleaning/repair.", "Тазалау/жөндеу алдында оператор растайды."),
                ],
            },
            {
                "type": "case",
                "title": _L("Kazakhstan dust", "Қазақстан шаңы"),
                "body": _L(
                    "Southern Kazakhstan dust storms soiling can cut yield 5–15%+. "
                    "CV helps prioritise which arrays to clean first after a storm.",
                    "Оңтүстік Қазақстандағы шаң өнімділікті 5–15%+ төмендетеді. "
                    "CV дауылдан кейін қай қатарды бірінші тазалау керектігін көрсетеді.",
                ),
            },
        ],
        "key_takeaways": [
            _L("CNN = classify image; YOLO = locate defects.", "CNN = класс; YOLO = ақау орны."),
            _L("Always couple AI with field inspection.", "AI-ды далалық тексерумен толықтырыңыз."),
        ],
    },
    "hybrid_optimization": {
        "id": "hybrid_optimization",
        "title": _L(
            "Hybrid system optimization",
            "Гибридті жүйені оңтайландыру",
        ),
        "level": _L("Intermediate", "Орта"),
        "minutes": 14,
        "related_quiz": "optimization_basics",
        "sections": [
            {
                "type": "text",
                "title": _L("What we optimize", "Нені оңтайландырамыз"),
                "body": _L(
                    "Given solar and wind forecasts, load, battery limits, and grid prices, "
                    "we choose charge/discharge and grid import/export each hour. "
                    "EcoPredict uses PuLP linear programming in HybridEnergyOptimizer "
                    "for multi-hour plans, plus a fast single-step heuristic for /predict.",
                    "Күн/жел болжамы, жүктеме, батарея және тариф бойынша "
                    "әр сағат заряд/разряд және grid import/export таңдалады. "
                    "EcoPredict-та HybridEnergyOptimizer (PuLP) көп сағаттық жоспар жасайды, "
                    "/predict үшін жылдам бір қадамдық heuristic бар.",
                ),
            },
            {
                "type": "formula",
                "title": _L("Energy balance (hourly)", "Энергия балансы (сағаттық)"),
                "latex": (
                    r"P_{pv}+P_{wind}+P_{dis}+P_{imp}"
                    r"=P_{load}+P_{ch}+P_{exp}+P_{curt}"
                ),
                "body": _L(
                    r"All terms in kW (or kWh if $\Delta t=1\,\mathrm{h}$). "
                    r"Battery dynamics: $SOC_{t+1}=SOC_t+( \eta P_{ch}-P_{dis}/\eta)\Delta t / E_{cap}$.",
                    r"Барлық мүшелер кВт (немесе $\Delta t=1\,\mathrm{h}$ болса кВт·сағ). "
                    r"Батарея: $SOC_{t+1}=SOC_t+( \eta P_{ch}-P_{dis}/\eta)\Delta t / E_{cap}$.",
                ),
            },
            {
                "type": "tasks",
                "title": _L("Student tasks", "Студент тапсырмалары"),
                "items": [
                    _L(
                        r"In Labs, compare heuristic vs PuLP and report $\Delta E_{imp}=E_{imp}^{heur}-E_{imp}^{PuLP}$.",
                        r"Labs-та эвристика vs PuLP; $\Delta E_{imp}=E_{imp}^{heur}-E_{imp}^{PuLP}$ жазыңыз.",
                    ),
                    _L(
                        r"If $E_{pv}=100\,\mathrm{kWh}$ and on-site use is $70\,\mathrm{kWh}$, compute $SC\%=100\cdot 70/100$.",
                        r"$E_{pv}=100\,\mathrm{kWh}$, жергілікті $70\,\mathrm{kWh}$ болса, $SC\%=100\cdot 70/100$ есептеңіз.",
                    ),
                ],
            },
            {
                "type": "bullets",
                "title": _L("Objectives", "Мақсаттар"),
                "items": [
                    _L("max_profit: sell when prices high, buy when low.", "max_profit: қымбатта сату, арзанда алу."),
                    _L("min_co2: cut grid import (dirty kWh).", "min_co2: лас grid import-ты азайту."),
                    _L("balanced: weighted sum of both.", "balanced: екеуінің салмақты қосындысы."),
                ],
            },
            {
                "type": "tip",
                "title": _L("Lab", "Зертхана"),
                "body": _L(
                    "In the Battery lab, increase capacity and watch self-consumption and CO₂ change.",
                    "Battery зертханасында сыйымдылықты өсіріп, self-consumption және CO₂ өзгерісін қараңыз.",
                ),
            },
        ],
        "key_takeaways": [
            _L("Battery links hours: charge noon, discharge evening.", "Батарея сағаттарды байланыстырады."),
            _L("Constraints (SOC, rates) keep plans physical.", "SOC/rate шектеулері жоспарды шынайы етеді."),
        ],
    },
    "xai_rag": {
        "id": "xai_rag",
        "title": _L(
            "Explainable AI & RAG in energy",
            "Түсіндірілетін AI және RAG энергияда",
        ),
        "level": _L("Beginner → Intermediate", "Бастауыш → Орта"),
        "minutes": 11,
        "related_quiz": "xai_rag",
        "sections": [
            {
                "type": "text",
                "title": _L("Why explain models?", "Неге модельді түсіндіру?"),
                "body": _L(
                    "Operators must trust forecasts before curtailing load or scheduling cleaning. "
                    "Feature importance shows which inputs pushed the prediction up or down. "
                    "SHAP-style values attribute contribution per feature; EcoPredict starts with "
                    "tree-model importance + simple sensitivity rules.",
                    "Оператор болжамға сенуі керек. Feature importance қай кіріс әсер еткенін көрсетеді. "
                    "SHAP-стиль әр белгінің үлесін береді; EcoPredict-та ағаш маңыздылығы + "
                    "сезімталдық ережелері бар.",
                ),
            },
            {
                "type": "text",
                "title": _L("RAG for operations", "RAG операцияларда"),
                "body": _L(
                    "Retrieval-Augmented Generation searches a knowledge base "
                    "(panel faults, cleaning, Kazakhstan dust) then answers with cited snippets. "
                    "EcoPredict stores docs in knowledge_base/ and indexes them with ChromaDB.",
                    "RAG білім базасынан (ақау, тазалау, ҚР шаңы) үзінді алып жауап береді. "
                    "EcoPredict құжаттарды knowledge_base/ ішінде сақтап, ChromaDB-мен индекстейді.",
                ),
            },
            {
                "type": "tip",
                "title": _L("Safety note", "Қауіпсіздік"),
                "body": _L(
                    "AI advice does not replace electrical safety codes or certified technicians.",
                    "AI кеңесі электр қауіпсіздігі нормаларын немесе сертификатты маманды алмастырмайды.",
                ),
            },
        ],
        "key_takeaways": [
            _L("XAI builds trust for grid decisions.", "XAI желі шешімдеріне сенім береді."),
            _L("RAG grounds answers in your docs.", "RAG жауапты сіздің құжаттарыңызға сүйейді."),
        ],
    },
    "sustainable_management": {
        "id": "sustainable_management",
        "title": _L(
            "Sustainable energy management",
            "Тұрақты энергия менеджменті",
        ),
        "level": _L("Beginner", "Бастауыш"),
        "minutes": 9,
        "related_quiz": "sustainability",
        "sections": [
            {
                "type": "bullets",
                "title": _L("Principles", "Принциптер"),
                "items": [
                    _L("Measure: PR, yield, downtime, CO₂ intensity.", "Өлшеу: PR, yield, downtime, CO₂."),
                    _L("Maintain: cleaning, IR scans, inverter firmware.", "Қызмет: тазалау, IR, firmware."),
                    _L("Optimize: self-consume renewables, smart storage.", "Оңтайландыру: өз тұтыну, сақтау."),
                    _L("Educate: operators understand why AI suggested an action.", "Білім: оператор AI-ды түсінеді."),
                ],
            },
            {
                "type": "text",
                "title": _L("KPIs students should know", "Студент білуі керек KPI"),
                "body": _L(
                    "Performance Ratio (PR), capacity factor, LCOE, payback (years), "
                    "self-consumption %, and avoided CO₂ (kg).",
                    "PR, capacity factor, LCOE, өтелім (жыл), self-consumption %, CO₂ (кг).",
                ),
            },
        ],
        "key_takeaways": [
            _L("Data → decision → action → verify.", "Дерек → шешім → әрекет → тексеру."),
        ],
    },
    "kz_case_study": {
        "id": "kz_case_study",
        "title": _L(
            "Case study: Turkistan solar plant",
            "Кейс: Түркістан күн станциясы",
        ),
        "level": _L("Applied", "Практикалық"),
        "minutes": 15,
        "related_quiz": "kz_case",
        "sections": [
            {
                "type": "case",
                "title": _L("Setting", "Ситуация"),
                "body": _L(
                    "A 25 kW-class inverter (Solarman-connected) in Turkistan region faces "
                    "high summer irradiance, heat derating, and dust. Operators use EcoPredict "
                    "for live telemetry, 24h weather-linked forecast, and cleaning decisions.",
                    "Түркістан өңіріндегі ~25 кВт инвертор (Solarman) жоғары сәуле, ыстық "
                    "және шаңмен жұмыс істейді. EcoPredict live телеметрия, 24сағ болжам "
                    "және тазалау шешімдері үшін қолданылады.",
                ),
            },
            {
                "type": "tasks",
                "title": _L("Student tasks", "Студент тапсырмалары"),
                "items": [
                    _L(
                        r"Forecast: clear vs cloudy — report $\widehat{P}_{noon}$ for both and $\delta=(\widehat{P}_c-\widehat{P}_b)/\widehat{P}_c$.",
                        r"Forecast: ашық/бұлтты — екеуінің $\widehat{P}_{noon}$ және $\delta=(\widehat{P}_c-\widehat{P}_b)/\widehat{P}_c$.",
                    ),
                    _L(
                        r"XAI: for a low-power hour, rank top-3 features by importance $I_j$.",
                        r"XAI: төмен қуат сағатында топ-3 белгіні $I_j$ маңыздылығы бойынша тізіңіз.",
                    ),
                    _L(
                        r"Battery lab: double $E_{cap}$; report change in import $E_{imp}$ and CO₂ $\propto E_{imp}$.",
                        r"Battery зертханасы: $E_{cap}$ екі есе; $E_{imp}$ және CO₂ $\propto E_{imp}$ өзгерісі.",
                    ),
                    _L(
                        r"Dust: if soiling cuts yield by $s=0.08$, recovered energy after clean is $\approx s\cdot E_{day}$.",
                        r"Шаң: yield $s=0.08$ төмендесе, тазалаудан кейін қайтарым $\approx s\cdot E_{day}$.",
                    ),
                ],
            },
            {
                "type": "formula",
                "title": _L("Simple dust loss model", "Қарапайым шаң жоғалту моделі"),
                "latex": r"E_{dirty} \approx (1-s)\,E_{clean},\quad 0\le s < 1",
                "body": _L(
                    r"Discuss O&M: cleaning cost $C$ vs recovered value $c\cdot s\cdot E_{clean}$.",
                    r"O&M: тазалау құны $C$ vs қайтарылған құн $c\cdot s\cdot E_{clean}$.",
                ),
            },
            {
                "type": "tip",
                "title": _L("Discussion", "Талқылау"),
                "body": _L(
                    "Is it better to clean after every dust event or on a fixed schedule? "
                    "Use cost of cleaning vs lost kWh (see knowledge_base/recommendations).",
                    "Әр шаңнан кейін тазалау ма, әлде кесте бойынша ма? "
                    "Тазалау құны vs жоғалған кВт·сағ (knowledge_base/recommendations).",
                ),
            },
        ],
        "key_takeaways": [
            _L("Local climate drives O&M strategy.", "Жергілікті климат O&M-ді анықтайды."),
            _L("Platform + human judgment together.", "Платформа + адам шешімі бірге."),
        ],
    },
}


def list_lessons(lang: str = "en") -> list[dict[str, Any]]:
    """Return lesson cards for a language (metadata only)."""
    lang = "kk" if lang == "kk" else "en"
    cards = []
    for lid in LESSON_IDS:
        lesson = LESSONS[lid]
        cards.append(
            {
                "id": lid,
                "title": lesson["title"][lang],
                "level": lesson["level"][lang],
                "minutes": lesson["minutes"],
                "related_quiz": lesson.get("related_quiz"),
            }
        )
    return cards


def get_lesson(lesson_id: str, lang: str = "en") -> dict[str, Any] | None:
    """
    Fully resolved lesson for rendering (all strings in one language).
    """
    raw = LESSONS.get(lesson_id)
    if not raw:
        return None
    lang = "kk" if lang == "kk" else "en"
    out = deepcopy(raw)
    out["title"] = raw["title"][lang]
    out["level"] = raw["level"][lang]
    sections = []
    for sec in raw["sections"]:
        s = {"type": sec["type"], "title": sec["title"][lang]}
        if "body" in sec:
            body = sec["body"]
            s["body"] = body[lang] if isinstance(body, dict) else body
        if "latex" in sec:
            latex = sec["latex"]
            s["latex"] = latex[lang] if isinstance(latex, dict) else latex
        if "items" in sec:
            s["items"] = [it[lang] for it in sec["items"]]
        sections.append(s)
    out["sections"] = sections
    out["key_takeaways"] = [k[lang] for k in raw["key_takeaways"]]
    return out
