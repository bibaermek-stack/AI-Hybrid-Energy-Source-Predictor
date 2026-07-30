"""
Streamlit UI: Learn & Explore educational hub.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.components.markdown_math import (
    katex_help_caption,
    render_latex,
    render_markdown_math,
)
from src.education.exercises import (
    battery_scenario,
    fault_image_teaching_notes,
    forecast_sensitivity_curve,
    forecast_what_if,
    synthetic_day_profiles,
)
from src.education.explainable_ai import (
    explain_prediction_narrative,
    feature_importance_table,
    predict_solar,
    sensitivity_analysis,
)
from src.education.lessons import get_lesson, list_lessons
from src.education.progress import ProgressTracker
from src.education.quiz import get_quiz, grade_quiz, list_quizzes


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    """Main educational dashboard section."""
    lang = "kk" if lang == "kk" else "en"
    progress = ProgressTracker.from_session(st.session_state)

    st.caption(
        _t(
            lang,
            "Interactive lessons · labs · quizzes · explainable AI · Kazakhstan cases",
            "Интерактивті сабақтар · зертхана · квиз · түсіндірілетін AI · ҚР кейстері",
        )
    )

    # Progress strip
    sm = progress.summary()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(_t(lang, "Lessons done", "Сабақтар"), sm["lessons_completed"])
    c2.metric(_t(lang, "Quizzes", "Квиздер"), sm["quizzes_taken"])
    c3.metric(_t(lang, "Best quiz avg %", "Үздік квиз %"), sm["quiz_best_avg"])
    c4.metric(_t(lang, "Labs done", "Зертхана"), sm["exercises_done"])

    with st.expander(_t(lang, "Reset progress", "Прогресті нөлдеу"), expanded=False):
        if st.button(_t(lang, "Clear my learning progress", "Прогресті тазалау")):
            progress.reset()
            st.rerun()

    tab_learn, tab_lab, tab_xai, tab_quiz, tab_case = st.tabs(
        [
            _t(lang, "Learn", "Оқу"),
            _t(lang, "Labs", "Зертхана"),
            _t(lang, "Explainable AI", "Түсіндірілетін AI"),
            _t(lang, "Quizzes", "Квиздер"),
            _t(lang, "Case study", "Кейс"),
        ]
    )

    with tab_learn:
        _render_learn(lang, progress)
    with tab_lab:
        _render_labs(lang, progress)
    with tab_xai:
        _render_xai(lang, progress)
    with tab_quiz:
        _render_quiz(lang, progress)
    with tab_case:
        _render_case(lang, progress)


def _render_learn(lang: str, progress: ProgressTracker) -> None:
    cards = list_lessons(lang)
    titles = {c["id"]: f"{c['title']} ({c['minutes']} min)" for c in cards}
    choice = st.selectbox(
        _t(lang, "Choose a lesson", "Сабақты таңдаңыз"),
        options=list(titles.keys()),
        format_func=lambda i: titles[i],
    )
    lesson = get_lesson(choice, lang)
    if not lesson:
        st.error("Lesson not found")
        return

    st.subheader(lesson["title"])
    st.caption(f"{lesson['level']} · ~{lesson['minutes']} min")
    if progress.lesson_done(choice):
        st.success(_t(lang, "Marked complete", "Аяқталды деп белгіленген"))

    katex_help_caption(lang)

    for sec in lesson["sections"]:
        with st.expander(sec["title"], expanded=sec["type"] in ("text", "case", "formula", "tasks")):
            if sec["type"] == "bullets" or sec["type"] == "tasks":
                for item in sec.get("items", []):
                    render_markdown_math(f"- {item}")
            elif sec["type"] == "formula":
                latex = sec.get("latex")
                if latex:
                    render_latex(latex)
                if sec.get("body"):
                    render_markdown_math(sec["body"])
            elif sec["type"] == "tip":
                st.info(sec.get("body", ""))
            elif sec["type"] == "case":
                st.warning(sec.get("body", ""))
            else:
                render_markdown_math(sec.get("body", ""))

    st.markdown("#### " + _t(lang, "Key takeaways", "Негізгі қорытынды"))
    for k in lesson.get("key_takeaways", []):
        render_markdown_math(f"- {k}")

    # Mini interactive graph for forecasting lesson
    if choice == "lstm_forecasting":
        st.markdown("#### " + _t(lang, "Interactive idea", "Интерактивті идея"))
        hour = st.slider(_t(lang, "Hour of day", "Тәулік сағаты"), 0, 23, 12, key="learn_hour")
        df = forecast_sensitivity_curve(hour=hour)
        fig = px.line(
            df,
            x="irradiation_wm2",
            y="predicted_kw",
            title=_t(
                lang,
                f"Predicted power vs irradiance @ hour={hour}",
                f"Болжалды қуат vs сәуле @ сағат={hour}",
            ),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#c9d1d9",
        )
        st.plotly_chart(fig, width="stretch")

    if st.button(
        _t(lang, "Mark lesson complete", "Сабақты аяқталды деп белгілеу"),
        key=f"done_{choice}",
        width="stretch",
    ):
        progress.mark_lesson(choice)
        st.success("OK")
        st.rerun()


def _render_labs(lang: str, progress: ProgressTracker) -> None:
    lab = st.radio(
        _t(lang, "Pick a lab", "Зертхананы таңдаңыз"),
        [
            _t(lang, "A) Forecast what-if", "A) Болжам what-if"),
            _t(lang, "B) Battery optimization", "B) Батарея оңтайландыруы"),
            _t(lang, "C) Fault image notes", "C) Ақау суреті"),
        ],
        horizontal=True,
    )

    if lab.startswith("A") or "what-if" in lab.lower() or "Болжам" in lab:
        st.subheader(_t(lang, "Change parameters → see forecast", "Параметр → болжам"))
        c1, c2 = st.columns(2)
        with c1:
            irr = st.slider("Irradiation (W/m²)", 0, 1200, 800, 10, key="lab_irr")
            amb = st.slider("Ambient °C", -10, 50, 32, 1, key="lab_amb")
            mod = st.slider("Module °C", -5, 70, 48, 1, key="lab_mod")
        with c2:
            hour = st.slider("Hour", 0, 23, 13, 1, key="lab_h")
            day = st.number_input("Day", 1, 31, 15, key="lab_d")
            month = st.number_input("Month", 1, 12, 7, key="lab_m")
        out = forecast_what_if(irr, amb, mod, hour, int(day), int(month))
        st.metric(_t(lang, "Predicted AC power", "Болжалды AC қуат"), f"{out['predicted_kw']:.2f} kW")
        st.caption(out["note_kk"] if lang == "kk" else out["note_en"])
        progress.mark_exercise("forecast_what_if")

    elif lab.startswith("B") or "Battery" in lab or "Батарея" in lab:
        st.subheader(
            _t(
                lang,
                "Adjust battery size → profit & CO₂",
                "Батарея өлшемі → пайда және CO₂",
            )
        )
        profiles = synthetic_day_profiles(1)
        cap = st.slider(
            _t(lang, "Battery capacity (kWh)", "Батарея сыйымдылығы (кВт·сағ)"),
            20,
            400,
            120,
            10,
            key="lab_cap",
        )
        pmax = st.slider(
            _t(lang, "Max charge/discharge (kW)", "Макс заряд/разряд (кВт)"),
            10,
            100,
            40,
            5,
            key="lab_pmax",
        )
        mode = st.selectbox(
            _t(lang, "Optimizer mode", "Оңтайландыру режимі"),
            ["balanced", "max_profit", "min_co2"],
            key="lab_mode",
        )
        if st.button(_t(lang, "Run optimization", "Оңтайландыруды іске қосу"), width="stretch"):
            with st.spinner("PuLP…"):
                try:
                    res = battery_scenario(
                        profiles["solar"],
                        profiles["wind"],
                        profiles["load"],
                        capacity_kwh=cap,
                        max_power_kw=pmax,
                        mode=mode,
                    )
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Profit $", f"{res['total_profit']:.2f}")
                    m2.metric("CO₂ kg", f"{res['total_co2_kg']:.2f}")
                    m3.metric("Self-cons %", f"{res['self_consumption_rate']:.1f}")
                    st.dataframe(
                        res["schedule"][
                            [
                                "hour",
                                "solar_used",
                                "wind_used",
                                "battery_charge",
                                "battery_discharge",
                                "grid_import",
                                "grid_export",
                                "soc_pct",
                            ]
                        ],
                        width="stretch",
                        height=280,
                    )
                    try:
                        st.plotly_chart(res["plot_fn"](), width="stretch")
                    except Exception as e:
                        st.caption(f"Plot: {e}")
                    progress.mark_exercise("battery_lab")
                except Exception as e:
                    st.error(str(e))
                    st.info(
                        _t(
                            lang,
                            "Install pulp: pip install pulp",
                            "PuLP орнатыңыз: pip install pulp",
                        )
                    )

    else:
        st.subheader(_t(lang, "Fault image lab", "Ақау суреті зертханасы"))
        st.markdown(fault_image_teaching_notes(lang))
        img = st.file_uploader(
            _t(lang, "Upload a panel photo (optional)", "Панель фотосын жүктеңіз (міндетті емес)"),
            type=["jpg", "jpeg", "png"],
            key="lab_img",
        )
        if img is not None:
            st.image(img, caption=img.name, width="stretch")
            st.success(
                _t(
                    lang,
                    "Next: open Fault Detection page to run the model on this image.",
                    "Келесі: Fault Detection бетінде модельді іске қосыңыз.",
                )
            )
            progress.mark_exercise("fault_image")


def _render_xai(lang: str, progress: ProgressTracker) -> None:
    st.subheader(
        _t(lang, "Why did the model predict this?", "Модель неге осылай болжады?")
    )
    st.caption(
        _t(
            lang,
            "Feature importance + sensitivity (teaching XAI). SHAP used if installed.",
            "Feature importance + сезімталдық (оқу XAI). SHAP болса қолданылады.",
        )
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        irr = st.number_input("Irradiation", 0.0, 1200.0, 850.0, 10.0, key="xai_irr")
        hour = st.slider("Hour", 0, 23, 12, key="xai_hour")
    with c2:
        amb = st.number_input("Ambient °C", -10.0, 55.0, 33.0, 0.5, key="xai_amb")
        day = st.number_input("Day", 1, 31, 15, key="xai_day")
    with c3:
        mod = st.number_input("Module °C", -5.0, 75.0, 50.0, 0.5, key="xai_mod")
        month = st.number_input("Month", 1, 12, 7, key="xai_month")

    base = {
        "IRRADIATION": float(irr),
        "AMBIENT_TEMPERATURE": float(amb),
        "MODULE_TEMPERATURE": float(mod),
        "hour": float(hour),
        "day": float(day),
        "month": float(month),
    }
    pred = predict_solar(irr, amb, mod, hour, int(day), int(month))
    st.metric(_t(lang, "Model output", "Модель шығысы"), f"{pred:.2f} kW")

    st.markdown(explain_prediction_narrative(base, pred, lang=lang))

    imp = feature_importance_table()
    fig = px.bar(
        imp,
        x="importance",
        y="feature",
        orientation="h",
        title=_t(lang, "Global feature importance", "Жалпы feature importance"),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#c9d1d9",
        height=320,
    )
    st.plotly_chart(fig, width="stretch")

    sens = sensitivity_analysis(base)
    st.markdown("#### " + _t(lang, "What-if sensitivity", "What-if сезімталдық"))
    st.dataframe(sens, width="stretch")
    progress.mark_exercise("xai_explorer")


def _render_quiz(lang: str, progress: ProgressTracker) -> None:
    quizzes = list_quizzes(lang)
    if not quizzes:
        st.info("No quizzes")
        return
    qmap = {q["id"]: q["title"] for q in quizzes}
    qid = st.selectbox(
        _t(lang, "Select quiz", "Квизді таңдаңыз"),
        options=list(qmap.keys()),
        format_func=lambda i: qmap[i],
    )
    quiz = get_quiz(qid, lang)
    if not quiz:
        return

    st.subheader(quiz["title"])
    answers: dict[str, int] = {}
    for i, q in enumerate(quiz["questions"]):
        st.markdown(f"**{i + 1}. {q['prompt']}**")
        choice = st.radio(
            label=q["id"],
            options=list(range(len(q["choices"]))),
            format_func=lambda j, ch=q["choices"]: ch[j],
            key=f"quiz_{qid}_{q['id']}",
            label_visibility="collapsed",
        )
        answers[q["id"]] = int(choice)

    if st.button(_t(lang, "Submit quiz", "Квизді жіберу"), width="stretch", key=f"sub_{qid}"):
        result = grade_quiz(qid, answers)
        progress.record_quiz(qid, result["percent"])
        st.success(
            _t(
                lang,
                f"Score: {result['score']}/{result['total']} ({result['percent']}%)",
                f"Нәтиже: {result['score']}/{result['total']} ({result['percent']}%)",
            )
        )
        # Instant feedback with explanations
        raw = get_quiz(qid, lang)
        for q, det in zip(raw["questions"], result["details"]):
            if det["correct"]:
                st.markdown(f"✅ **{q['prompt']}**")
            else:
                st.markdown(f"❌ **{q['prompt']}**")
                st.caption(
                    _t(lang, "Correct: ", "Дұрысы: ")
                    + q["choices"][q["correct_index"]]
                )
            st.info(q["explain"])


def _render_case(lang: str, progress: ProgressTracker) -> None:
    lesson = get_lesson("kz_case_study", lang)
    if not lesson:
        return
    st.subheader(lesson["title"])
    for sec in lesson["sections"]:
        st.markdown(f"### {sec['title']}")
        if sec["type"] == "bullets":
            for it in sec.get("items", []):
                st.markdown(f"- {it}")
        else:
            st.markdown(sec.get("body", ""))

    st.markdown("---")
    st.markdown(
        "#### "
        + _t(
            lang,
            "Mini challenge checklist",
            "Мини-тапсырма чек-лист",
        )
    )
    a = st.checkbox(
        _t(lang, "I compared clear vs cloudy forecast", "Ашық/бұлтты болжамды салыстырдым"),
        key="case_a",
    )
    b = st.checkbox(
        _t(lang, "I used XAI explorer once", "XAI explorer-ді қолдандым"),
        key="case_b",
    )
    c = st.checkbox(
        _t(lang, "I changed battery size in the lab", "Зертханада батареяны өзгерттім"),
        key="case_c",
    )
    if a and b and c:
        st.success(
            _t(
                lang,
                "Case study complete — great work!",
                "Кейс аяқталды — жарайсыз!",
            )
        )
        progress.mark_lesson("kz_case_study")
        progress.mark_exercise("kz_case_checklist")
