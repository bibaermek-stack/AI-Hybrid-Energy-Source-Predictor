"""Streamlit hub: interactive education laboratories (RES + CACER-inspired)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from dashboard.components.buttons import primary_button
from dashboard.components.inverter_wiring_ui import render_inverter_wiring_lab
from dashboard.components.lab_tasks_ui import render_lab_tasks_panel
from dashboard.components.markdown_math import katex_help_caption, render_markdown_math
from dashboard.components.metric_card import metric_row
from dashboard.components.states import empty_state, error_state, loading_state
from dashboard.components.status_badge import render_status_badge
from dashboard.components.ui_kit import section_header
from dashboard.utils.plotly_theme import themed_line
from src.education.lab_tasks import lab_tasks_progress
from src.education.labs.lab_registry import get_lab, list_labs, t
from src.education.progress import ProgressTracker
from src.education.quiz import get_quiz, grade_quiz
from src.simulation.adapters.weather_profile import load_weather_profile, synthetic_day_profile
from src.simulation.community.bess_step import simulate_bess_series
from src.simulation.community.financial_kpis import community_project_kpis
from src.simulation.community.load_profile import scale_profile, synthetic_load_profile
from src.simulation.community.shared_energy import run_shared_energy_day
from src.simulation.microgrid.compare_pulp import compare_heuristic_vs_pulp
from src.simulation.microgrid.engine import run_day_simulation, run_mppt_trace, summarize_day
from src.simulation.microgrid.solar_panel import SolarArray, SolarPanelConfig

CONTENT = Path(__file__).resolve().parents[2] / "src" / "education" / "content" / "labs"

RENDERERS = {
    "render_pv_physics": "_lab_pv_physics",
    "render_mppt": "_lab_mppt",
    "render_bess_soc": "_lab_bess_soc",
    "render_microgrid": "_lab_microgrid",
    "render_heuristic_vs_pulp": "_lab_heuristic_vs_pulp",
    "render_pv_yield": "_lab_pv_yield",
    "render_load_shape": "_lab_load_shape",
    "render_bess_community": "_lab_bess_community",
    "render_shared_energy": "_lab_shared_energy",
    "render_rec_finance": "_lab_rec_finance",
    "render_grid_impact": "_lab_grid_impact",
}


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def _read_theory(stem: str, lang: str) -> str:
    suffix = "kk" if lang == "kk" else "en"
    path = CONTENT / f"{stem}_{suffix}.md"
    if not path.is_file():
        path = CONTENT / f"{stem}_en.md"
    if path.is_file():
        return path.read_text(encoding="utf-8")
    return ""


def _weather(src: str, site: dict):
    if src == "synthetic":
        return synthetic_day_profile()
    if src == "open-meteo":
        return load_weather_profile(
            lat=float(site.get("lat") or 43.2973),
            lon=float(site.get("lon") or 68.2517),
            prefer="open-meteo",
        )
    return load_weather_profile(prefer="sample")


def _weather_select(lang: str, key: str = "lab_weather") -> str:
    return st.selectbox(
        _t(lang, "Weather source", "Ауа райы көзі"),
        ["sample", "synthetic", "open-meteo"],
        format_func=lambda x: {
            "sample": _t(lang, "Sample CSV", "Үлгі CSV"),
            "synthetic": _t(lang, "Synthetic day", "Синтетикалық күн"),
            "open-meteo": "Open-Meteo",
        }[x],
        key=key,
    )


def _complete(lang: str, progress: ProgressTracker, lab_id: str, quiz_id: str | None = None) -> None:
    """Mark simulation run; full lab completion requires graded tasks."""
    progress.mark_exercise(f"{lab_id}_sim")
    tp = lab_tasks_progress(lab_id, progress.tasks_done_for(lab_id))
    if tp["total"] and not tp["complete"]:
        st.info(
            _t(
                lang,
                f"Simulation done. Complete tasks below ({tp['done']}/{tp['total']}) to finish the lab.",
                f"Симуляция дайын. Зертхананы аяқтау үшін төмендегі тапсырмаларды орындаңыз ({tp['done']}/{tp['total']}).",
            )
        )
    elif tp["complete"] or tp["total"] == 0:
        progress.mark_lab(lab_id)
        st.success(
            _t(
                lang,
                "Lab complete (tasks passed).",
                "Зертхана аяқталды (тапсырмалар орындалды).",
            )
        )
    if quiz_id:
        _mini_quiz(lang, progress, quiz_id)


def _mini_quiz(lang: str, progress: ProgressTracker, quiz_id: str) -> None:
    quiz = get_quiz(quiz_id, lang)
    if not quiz or not quiz.get("questions"):
        return
    with st.expander(_t(lang, "Reflection quiz", "Рефлексия викторинасы"), expanded=False):
        st.caption(quiz["title"])
        answers: dict[str, int] = {}
        for q in quiz["questions"]:
            choice = st.radio(
                q["prompt"],
                range(len(q["choices"])),
                format_func=lambda i, choices=q["choices"]: choices[i],
                key=f"labquiz_{quiz_id}_{q['id']}",
            )
            answers[q["id"]] = int(choice)
        if st.button(
            _t(lang, "Submit quiz", "Викторинаны жіберу"),
            key=f"labquiz_submit_{quiz_id}",
        ):
            result = grade_quiz(quiz_id, answers)
            progress.record_quiz(quiz_id, float(result["percent"]))
            st.info(
                _t(
                    lang,
                    f"Score: {result['score']}/{result['total']} ({result['percent']}%)",
                    f"Нәтиже: {result['score']}/{result['total']} ({result['percent']}%)",
                )
            )
            for q, d in zip(quiz["questions"], result["details"]):
                if not d["correct"]:
                    st.caption(f"• {q['explain']}")


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    try:
        _render(lang)
    except Exception as e:
        error_state(
            _t(lang, "Labs view failed.", "Зертхана беті сәтсіз."),
            detail=e,
            lang=lang,
        )


def _render(lang: str) -> None:
    lang = "kk" if lang == "kk" else "en"
    theme = str(st.session_state.get("ep_theme") or "Dark")
    progress = ProgressTracker.from_session(st.session_state)

    section_header(
        _t(lang, "Interactive laboratories", "Интерактивті зертханалар"),
        _t(
            lang,
            "Microgrid (RenewableEnergySim) + community (CACER-inspired) labs",
            "Микрожелі (RenewableEnergySim) + қауымдастық (CACER) зертханалары",
        ),
    )

    sm = progress.summary()
    render_status_badge(
        (
            f"Labs: {sm.get('labs_completed', 0)} · tasks: {sm.get('tasks_completed', 0)}"
            if lang != "kk"
            else f"Зертхана: {sm.get('labs_completed', 0)} · тапсырма: {sm.get('tasks_completed', 0)}"
        ),
        "accent",
    )

    labs = list_labs()
    labels = [
        f"{L.get('phase', '')} · {t(L['title'], lang)} ({L['minutes']} min)"
        + ("" if L.get("available", True) else " 🔒")
        for L in labs
    ]
    choice = st.selectbox(
        _t(lang, "Select lab", "Зертхана таңдау"),
        range(len(labs)),
        format_func=lambda i: labels[i],
    )
    lab = labs[choice]
    st.caption(f"{t(lab['level'], lang)} · {t(lab.get('tag', {}), lang)} · {lab['source']}")
    st.info(t(lab["objectives"], lang))
    if progress.lab_done(lab["id"]):
        render_status_badge(_t(lang, "Completed", "Орындалды"), "ok")

    rid = lab["render"]
    dispatch = {
        "render_pv_physics": _lab_pv_physics,
        "render_mppt": _lab_mppt,
        "render_bess_soc": _lab_bess_soc,
        "render_microgrid": _lab_microgrid,
        "render_heuristic_vs_pulp": _lab_heuristic_vs_pulp,
        "render_pv_yield": _lab_pv_yield,
        "render_load_shape": _lab_load_shape,
        "render_bess_community": _lab_bess_community,
        "render_shared_energy": _lab_shared_energy,
        "render_rec_finance": _lab_rec_finance,
        "render_grid_impact": _lab_grid_impact,
        "render_inverter_wiring": _lab_inverter_wiring,
    }
    fn = dispatch.get(rid)
    if fn is None:
        empty_state("Unknown lab", lab["id"])
        return
    fn(lang, theme, progress, lab)

    # Graded tasks: correct / wrong / try again — lab finishes when all pass
    st.markdown("---")
    render_lab_tasks_panel(
        lab["id"],
        lang,
        progress,
        expanded=True,
        require_all_for_lab=True,
    )


def _lab_pv_physics(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "pv_physics", lang))

    c1, c2, c3 = st.columns(3)
    with c1:
        n = st.slider(_t(lang, "Number of panels", "Панель саны"), 10, 400, 100, 10)
        eta = st.slider(_t(lang, "Efficiency η", "ПӘК η"), 0.10, 0.25, 0.20, 0.01)
    with c2:
        gamma = st.slider(
            _t(lang, "Temp coefficient γ", "Темп. коэффициент γ"),
            0.001,
            0.008,
            0.004,
            0.001,
        )
        area = st.number_input(_t(lang, "Panel area m²", "Панель ауданы м²"), 1.0, 3.0, 1.6, 0.1)
    with c3:
        irr = st.slider(_t(lang, "Irradiance W/m²", "Сәулелену Вт/м²"), 0, 1200, 900, 50)
        temp = st.slider(_t(lang, "Temperature °C", "Температура °C"), -10, 50, 35, 1)

    if primary_button(_t(lang, "Compute power", "Қуатты есептеу"), key="lab_pv_run"):
        cfg = SolarPanelConfig(area=float(area), efficiency=float(eta), temp_coefficient=float(gamma))
        arr = SolarArray(cfg, num_panels=int(n))
        p_w = arr.calculate_power(float(irr), float(temp))
        p_kw = p_w / 1000.0
        metric_row(
            [
                {"label": "P_DC", "value": f"{p_kw:.2f} kW", "icon": "☀", "variant": "solar"},
                {
                    "label": "Array area",
                    "value": f"{arr.total_area:.1f} m²",
                    "icon": "▣",
                    "variant": "default",
                },
                {
                    "label": "η_eff",
                    "value": f"{cfg.efficiency * (1 - max(0, (temp - 25) * gamma)):.3f}",
                    "icon": "η",
                    "variant": "total",
                },
            ]
        )
        import numpy as np

        gs = np.linspace(0, 1100, 50)
        ps = [arr.calculate_power(g, temp) / 1000.0 for g in gs]
        fig = themed_line(
            gs.tolist(),
            {"P_DC kW": ps},
            title=_t(lang, "Power vs irradiance", "Қуат vs сәулелену"),
            y_title="kW",
            theme=theme,
        )
        st.plotly_chart(fig, width="stretch")
        _complete(lang, progress, "lab_pv_physics", lab.get("quiz_id"))


def _lab_mppt(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "mppt", lang))
    c1, c2 = st.columns(2)
    with c1:
        irr = st.slider(_t(lang, "Irradiance W/m²", "Сәулелену"), 200, 1000, 800, 50, key="mppt_irr")
        step = st.slider(_t(lang, "Step size V", "Қадам V"), 0.1, 2.0, 0.5, 0.1, key="mppt_step")
    with c2:
        steps = st.slider(_t(lang, "Iterations", "Итерация"), 20, 150, 80, 10, key="mppt_n")

    if primary_button(_t(lang, "Run MPPT trace", "MPPT ізін іске қосу"), key="lab_mppt_run"):
        with loading_state(_t(lang, "Simulating…", "Симуляция…")):
            df = run_mppt_trace(float(irr), step_size=float(step), steps=int(steps))
        metric_row(
            [
                {
                    "label": "P_max on trace",
                    "value": f"{df['p'].max():.1f} W",
                    "icon": "⚡",
                    "variant": "solar",
                },
                {
                    "label": "Final V_ref",
                    "value": f"{df['v_ref'].iloc[-1]:.2f} V",
                    "icon": "V",
                    "variant": "default",
                },
            ]
        )
        st.plotly_chart(
            themed_line(
                df["step"].tolist(),
                {"P (W)": df["p"].tolist(), "V_ref": df["v_ref"].tolist()},
                title="MPPT trace",
                theme=theme,
            ),
            width="stretch",
        )
        _complete(lang, progress, "lab_mppt_po", lab.get("quiz_id"))


def _lab_bess_soc(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "bess_soc", lang))

    site = st.session_state.get("ep_site") or {}
    c1, c2, c3 = st.columns(3)
    with c1:
        n = st.slider(_t(lang, "Panels", "Панель"), 20, 400, 100, 10, key="bess_n")
        bat = st.number_input(_t(lang, "Battery kWh", "Батарея кВт·сағ"), 5.0, 300.0, 40.0, 5.0, key="bess_kwh")
    with c2:
        load = st.slider(_t(lang, "Load kW", "Жүктеме кВт"), 1.0, 40.0, 12.0, 1.0, key="bess_load")
    with c3:
        weather_src = _weather_select(lang, "bess_weather")

    if not primary_button(_t(lang, "Simulate SOC day", "SOC тәулігін іске қосу"), key="lab_bess_soc_run"):
        empty_state(
            _t(lang, "No run yet", "Әлі іске қосылмаған"),
            _t(lang, "Set parameters and run.", "Параметрлерді қойып, іске қосыңыз."),
            icon="🔋",
        )
        return

    with loading_state(_t(lang, "Running…", "Есептелуде…")):
        try:
            weather = _weather(weather_src, site)
            df = run_day_simulation(
                weather,
                num_panels=int(n),
                battery_kwh=float(bat),
                load_kw=float(load),
            )
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    metric_row(
        [
            {
                "label": "SOC min %",
                "value": f"{df['soc'].min() * 100:.1f}",
                "icon": "↓",
                "variant": "warn",
            },
            {
                "label": "SOC max %",
                "value": f"{df['soc'].max() * 100:.1f}",
                "icon": "↑",
                "variant": "total",
            },
            {
                "label": "SOC end %",
                "value": f"{df['soc'].iloc[-1] * 100:.1f}",
                "icon": "%",
                "variant": "default",
            },
        ]
    )
    x = list(range(len(df)))
    st.plotly_chart(
        themed_line(
            x,
            {
                "PV kW": df["pv_kw"].tolist(),
                "Load kW": df["load_kw"].tolist(),
                "SOC %": (df["soc"] * 100).tolist(),
            },
            title=_t(lang, "Power and SOC", "Қуат және SOC"),
            theme=theme,
        ),
        width="stretch",
    )
    _complete(lang, progress, "lab_bess_soc", lab.get("quiz_id"))


def _lab_microgrid(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "microgrid", lang))

    site = st.session_state.get("ep_site") or {}
    c1, c2, c3 = st.columns(3)
    with c1:
        n = st.slider(_t(lang, "Panels", "Панель"), 20, 400, 100, 10, key="mg_n")
        bat = st.number_input(_t(lang, "Battery kWh", "Батарея кВт·сағ"), 5.0, 300.0, 50.0, 5.0)
    with c2:
        load = st.slider(_t(lang, "Load kW", "Жүктеме кВт"), 1.0, 50.0, 15.0, 1.0, key="mg_load")
        inv = st.number_input(_t(lang, "Inverter kW", "Инвертор кВт"), 5.0, 100.0, 40.0, 5.0)
    with c3:
        weather_src = _weather_select(lang, "mg_weather")

    if not primary_button(_t(lang, "Run 24h simulation", "24сағ симуляция"), key="lab_mg_run"):
        empty_state(
            _t(lang, "No run yet", "Әлі іске қосылмаған"),
            _t(lang, "Set parameters and run the simulation.", "Параметрлерді қойып, симуляцияны іске қосыңыз."),
            icon="⚙",
        )
        return

    with loading_state(_t(lang, "Running microgrid…", "Микрожелі есептелуде…")):
        try:
            weather = _weather(weather_src, site)
            df = run_day_simulation(
                weather,
                num_panels=int(n),
                battery_kwh=float(bat),
                load_kw=float(load),
                inverter_kw=float(inv),
            )
            summary = summarize_day(df)
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    metric_row(
        [
            {"label": "PV kWh", "value": f"{summary['pv_kwh']:.1f}", "icon": "☀", "variant": "solar"},
            {"label": "Import kWh", "value": f"{summary['import_kwh']:.1f}", "icon": "↓", "variant": "warn"},
            {"label": "Export kWh", "value": f"{summary['export_kwh']:.1f}", "icon": "↑", "variant": "wind"},
            {
                "label": "Self-cons %",
                "value": f"{summary['self_consumption_pct']:.1f}",
                "icon": "%",
                "variant": "total",
            },
        ]
    )

    x = list(range(len(df)))
    st.plotly_chart(
        themed_line(
            x,
            {
                "PV kW": df["pv_kw"].tolist(),
                "Load kW": df["load_kw"].tolist(),
                "Import kW": df["grid_import_kw"].tolist(),
                "Export kW": df["grid_export_kw"].tolist(),
            },
            title=_t(lang, "Power balance", "Қуат балансы"),
            y_title="kW",
            theme=theme,
        ),
        width="stretch",
    )
    st.plotly_chart(
        themed_line(
            x,
            {"SOC %": (df["soc"] * 100).tolist()},
            title="Battery SOC",
            y_title="%",
            theme=theme,
        ),
        width="stretch",
    )
    st.dataframe(df.round(3), width="stretch", hide_index=True)
    _complete(lang, progress, "lab_microgrid_dispatch", lab.get("quiz_id"))


def _lab_heuristic_vs_pulp(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "heuristic_vs_pulp", lang))

    site = st.session_state.get("ep_site") or {}
    c1, c2, c3 = st.columns(3)
    with c1:
        n = st.slider(_t(lang, "Panels", "Панель"), 20, 300, 100, 10, key="cmp_n")
        bat = st.number_input(_t(lang, "Battery kWh", "Батарея кВт·сағ"), 10.0, 200.0, 50.0, 5.0, key="cmp_bat")
    with c2:
        load = st.slider(_t(lang, "Load kW", "Жүктеме кВт"), 5.0, 40.0, 15.0, 1.0, key="cmp_load")
        mode = st.selectbox(
            _t(lang, "PuLP mode", "PuLP режимі"),
            ["balanced", "max_profit", "min_co2"],
            key="cmp_mode",
        )
    with c3:
        price_i = st.number_input(_t(lang, "Import $/kWh", "Импорт $/кВт·сағ"), 0.01, 1.0, 0.12, 0.01)
        price_e = st.number_input(_t(lang, "Export $/kWh", "Экспорт $/кВт·сағ"), 0.0, 1.0, 0.06, 0.01)
        weather_src = _weather_select(lang, "cmp_weather")

    if not primary_button(_t(lang, "Compare engines", "Қозғалтқыштарды салыстыру"), key="lab_cmp_run"):
        empty_state(
            _t(lang, "No comparison yet", "Салыстыру жоқ"),
            _t(lang, "Run to contrast heuristic vs PuLP.", "Эвристика vs PuLP салыстыру үшін іске қосыңыз."),
            icon="⚖",
        )
        return

    with loading_state(_t(lang, "Optimizing…", "Оңтайландыру…")):
        try:
            weather = _weather(weather_src, site)
            res = compare_heuristic_vs_pulp(
                weather,
                num_panels=int(n),
                battery_kwh=float(bat),
                load_kw=float(load),
                price_import=float(price_i),
                price_export=float(price_e),
                mode=str(mode),
            )
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    h = res["heuristic_summary"]
    metric_row(
        [
            {
                "label": "Heur import",
                "value": f"{h['import_kwh']:.1f} kWh",
                "icon": "H",
                "variant": "warn",
            },
            {
                "label": "PuLP import",
                "value": f"{res['pulp_import_kwh']:.1f} kWh",
                "icon": "P",
                "variant": "total",
            },
            {
                "label": "Δ import",
                "value": f"{res['delta_import_kwh']:.1f}",
                "icon": "Δ",
                "variant": "default",
            },
            {
                "label": "PuLP profit",
                "value": f"{res['pulp_profit']:.2f}",
                "icon": "$",
                "variant": "solar",
            },
        ]
    )
    hdf = res["heuristic_df"]
    pdf = res["pulp_schedule"]
    x = list(range(len(hdf)))
    series = {
        "Heur import": hdf["grid_import_kw"].tolist(),
        "Heur export": hdf["grid_export_kw"].tolist(),
    }
    # HybridEnergyOptimizer schedule uses grid_import / grid_export (kW)
    for col, label in (
        ("grid_import", "PuLP import"),
        ("grid_import_kw", "PuLP import"),
        ("grid_export", "PuLP export"),
        ("grid_export_kw", "PuLP export"),
    ):
        if col in pdf.columns and label not in series:
            series[label] = pdf[col].tolist()[: len(x)]
    st.plotly_chart(
        themed_line(x, series, title=_t(lang, "Import/export comparison", "Импорт/экспорт салыстыру"), theme=theme),
        width="stretch",
    )
    _complete(lang, progress, "lab_heuristic_vs_pulp", lab.get("quiz_id"))


def _lab_pv_yield(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "pv_yield", lang))

    site = st.session_state.get("ep_site") or {}
    c1, c2 = st.columns(2)
    with c1:
        n = st.slider(_t(lang, "Panels", "Панель"), 10, 500, 80, 10, key="yield_n")
        eta = st.slider(_t(lang, "Efficiency η", "ПӘК η"), 0.12, 0.24, 0.20, 0.01, key="yield_eta")
    with c2:
        weather_src = _weather_select(lang, "yield_weather")

    if not primary_button(_t(lang, "Build PV profile", "PV профилін құру"), key="lab_yield_run"):
        empty_state(_t(lang, "No profile yet", "Профиль жоқ"), icon="☀")
        return

    with loading_state(_t(lang, "Building…", "Құрылуда…")):
        try:
            weather = _weather(weather_src, site)
            cfg = SolarPanelConfig(efficiency=float(eta))
            arr = SolarArray(cfg, num_panels=int(n))
            p_kw = [
                arr.calculate_power(float(r["irradiance_w_m2"]), float(r["temperature_c"])) / 1000.0
                for _, r in weather.iterrows()
            ]
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    total = float(sum(p_kw))
    metric_row(
        [
            {"label": "Daily yield", "value": f"{total:.1f} kWh", "icon": "☀", "variant": "solar"},
            {"label": "Peak kW", "value": f"{max(p_kw) if p_kw else 0:.2f}", "icon": "⚡", "variant": "total"},
            {"label": "Hours", "value": str(len(p_kw)), "icon": "h", "variant": "default"},
        ]
    )
    st.plotly_chart(
        themed_line(
            list(range(len(p_kw))),
            {"PV kW": p_kw},
            title=_t(lang, "PV production profile", "PV өндіріс профилі"),
            y_title="kW",
            theme=theme,
        ),
        width="stretch",
    )
    _complete(lang, progress, "lab_pv_yield", lab.get("quiz_id"))


def _lab_load_shape(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "load_shape", lang))

    c1, c2, c3 = st.columns(3)
    with c1:
        base = st.slider(_t(lang, "Base kW", "Негіз кВт"), 0.2, 3.0, 0.8, 0.1, key="ld_base")
        morning = st.slider(_t(lang, "Morning peak kW", "Таңғы шың"), 0.5, 8.0, 2.0, 0.1, key="ld_m")
    with c2:
        evening = st.slider(_t(lang, "Evening peak kW", "Кешкі шың"), 0.5, 10.0, 3.5, 0.1, key="ld_e")
        peak = st.number_input(_t(lang, "Rescale peak kW", "Масштаб шың кВт"), 0.5, 20.0, 5.0, 0.5, key="ld_pk")
    with c3:
        noise = st.slider(_t(lang, "Noise %", "Шум %"), 0.0, 20.0, 5.0, 1.0, key="ld_n")
        seed = st.number_input(_t(lang, "Seed", "Seed"), 0, 9999, 42, 1, key="ld_seed")
        hours = st.slider(_t(lang, "Hours", "Сағат"), 24, 168, 24, 24, key="ld_h")

    if not primary_button(_t(lang, "Generate load", "Жүктеме жасау"), key="lab_load_run"):
        empty_state(_t(lang, "No load yet", "Жүктеме жоқ"), icon="⌂")
        return

    df = synthetic_load_profile(
        int(hours),
        base_kw=float(base),
        morning_peak_kw=float(morning),
        evening_peak_kw=float(evening),
        noise_pct=float(noise),
        seed=int(seed),
    )
    df = scale_profile(df, float(peak))
    energy = float(df["load_kw"].sum())
    metric_row(
        [
            {"label": "Energy", "value": f"{energy:.1f} kWh", "icon": "E", "variant": "total"},
            {"label": "Peak", "value": f"{df['load_kw'].max():.2f} kW", "icon": "↑", "variant": "warn"},
            {"label": "Mean", "value": f"{df['load_kw'].mean():.2f} kW", "icon": "μ", "variant": "default"},
        ]
    )
    st.plotly_chart(
        themed_line(
            df["hour"].tolist(),
            {"Load kW": df["load_kw"].tolist()},
            title=_t(lang, "Domestic load shape", "Тұрмыстық жүктеме"),
            y_title="kW",
            theme=theme,
        ),
        width="stretch",
    )
    _complete(lang, progress, "lab_load_shape", lab.get("quiz_id"))


def _lab_bess_community(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "bess_community", lang))

    c1, c2 = st.columns(2)
    with c1:
        cap = st.number_input(_t(lang, "Capacity kWh", "Сыйымдылық кВт·сағ"), 5.0, 200.0, 50.0, 5.0, key="bc_cap")
        dod = st.slider(_t(lang, "DoD", "DoD"), 0.3, 1.0, 0.8, 0.05, key="bc_dod")
        eta = st.slider(_t(lang, "η half-cycle", "η жартылай цикл"), 0.85, 1.0, 0.95, 0.01, key="bc_eta")
    with c2:
        st.caption(
            _t(
                lang,
                "Demo net series: morning surplus, midday surplus, evening deficit.",
                "Демо қатар: таңғы/түскі артық, кешкі жетіспеу.",
            )
        )
        amp = st.slider(_t(lang, "Surplus amplitude kWh", "Артық амплитуда"), 1.0, 20.0, 8.0, 1.0, key="bc_amp")

    if not primary_button(_t(lang, "Run BESS series", "BESS қатарын іске қосу"), key="lab_bc_run"):
        empty_state(_t(lang, "No run yet", "Әлі іске қосылмаған"), icon="🔋")
        return

    # 24h toy intent: charge midday, discharge evening
    net = []
    for h in range(24):
        if 9 <= h <= 15:
            net.append(float(amp) * (1.0 - abs(h - 12) / 6.0))
        elif 17 <= h <= 22:
            net.append(-float(amp) * 0.7)
        else:
            net.append(0.0)

    steps = simulate_bess_series(
        net,
        capacity_kwh=float(cap),
        dod=float(dod),
        eta_halfcycle=float(eta),
        initial_soc_frac=0.5,
    )
    soc = [s.soc_frac * 100 for s in steps]
    loss = sum(s.e_loss_kwh for s in steps)
    metric_row(
        [
            {"label": "Final SOC %", "value": f"{soc[-1]:.1f}", "icon": "%", "variant": "total"},
            {"label": "Min SOC %", "value": f"{min(soc):.1f}", "icon": "↓", "variant": "warn"},
            {"label": "Loss kWh", "value": f"{loss:.2f}", "icon": "L", "variant": "default"},
            {"label": "E_min floor", "value": f"{cap * (1 - dod):.1f}", "icon": "⊥", "variant": "solar"},
        ]
    )
    st.plotly_chart(
        themed_line(
            list(range(24)),
            {"Intent kWh": net, "SOC %": soc},
            title=_t(lang, "BESS intent vs SOC", "BESS ниет vs SOC"),
            theme=theme,
        ),
        width="stretch",
    )
    _complete(lang, progress, "lab_bess_community", lab.get("quiz_id"))


def _lab_shared_energy(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "shared_energy", lang))

    site = st.session_state.get("ep_site") or {}
    c1, c2, c3 = st.columns(3)
    with c1:
        n_users = st.slider(_t(lang, "Users N", "Пайдаланушы N"), 2, 8, 3, 1, key="se_n")
        panels = st.slider(_t(lang, "Panels / user", "Панель / пайд."), 10, 100, 40, 5, key="se_p")
    with c2:
        peak = st.slider(_t(lang, "Peak load kW", "Шың жүктеме кВт"), 1.0, 12.0, 4.0, 0.5, key="se_pk")
        bat = st.number_input(_t(lang, "Community BESS kWh", "Қауым BESS кВт·сағ"), 0.0, 200.0, 30.0, 5.0, key="se_b")
        dod = st.slider(_t(lang, "DoD", "DoD"), 0.4, 1.0, 0.8, 0.05, key="se_dod")
    with c3:
        pi = st.number_input(_t(lang, "Import $/kWh", "Импорт $/кВт·сағ"), 0.01, 1.0, 0.12, 0.01, key="se_pi")
        pe = st.number_input(_t(lang, "Export $/kWh", "Экспорт $/кВт·сағ"), 0.0, 1.0, 0.06, 0.01, key="se_pe")
        weather_src = _weather_select(lang, "se_weather")

    if not primary_button(_t(lang, "Run shared-energy day", "Бөліскен энергия күні"), key="lab_se_run"):
        empty_state(
            _t(lang, "No community run yet", "Қауымдастық іске қосылмаған"),
            _t(lang, "Set N users and run the 24h loop.", "N пайдаланушыны қойып, 24сағ циклді іске қосыңыз."),
            icon="🏘️",
        )
        return

    with loading_state(_t(lang, "Simulating community…", "Қауымдастық есептелуде…")):
        try:
            weather = _weather(weather_src, site)
            out = run_shared_energy_day(
                weather,
                n_users=int(n_users),
                panels_per_user=int(panels),
                peak_load_kw=float(peak),
                community_battery_kwh=float(bat),
                dod=float(dod),
                price_import=float(pi),
                price_export=float(pe),
                seed=42,
            )
        except Exception as e:
            error_state(str(e), detail=e, lang=lang)
            return

    metric_row(
        [
            {
                "label": "Shared kWh",
                "value": f"{out['shared_kwh']:.1f}",
                "icon": "↔",
                "variant": "total",
            },
            {
                "label": "Self-cons %",
                "value": f"{out['self_consumption_pct']:.1f}",
                "icon": "%",
                "variant": "solar",
            },
            {
                "label": "Import kWh",
                "value": f"{out['import_kwh']:.1f}",
                "icon": "↓",
                "variant": "warn",
            },
            {
                "label": "Net bill $",
                "value": f"{out['net_bill_proxy']:.2f}",
                "icon": "$",
                "variant": "default",
            },
        ]
    )
    ts = out["timeseries"]
    st.plotly_chart(
        themed_line(
            ts["hour"].tolist(),
            {
                "PV": ts["pv_kw"].tolist(),
                "Load": ts["load_kw"].tolist(),
                "Shared": ts["shared_kw"].tolist(),
                "Import": ts["import_kw"].tolist(),
            },
            title=_t(lang, "Community energy flows", "Қауымдастық энергия ағындары"),
            y_title="kW",
            theme=theme,
        ),
        width="stretch",
    )
    st.plotly_chart(
        themed_line(
            ts["hour"].tolist(),
            {"SOC %": (ts["soc"] * 100).tolist()},
            title="Community BESS SOC",
            theme=theme,
        ),
        width="stretch",
    )
    _complete(lang, progress, "lab_shared_energy", lab.get("quiz_id"))


def _lab_rec_finance(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "rec_finance", lang))

    c1, c2, c3 = st.columns(3)
    with c1:
        capex = st.number_input(_t(lang, "CAPEX $", "CAPEX $"), 10_000.0, 5_000_000.0, 80_000.0, 5_000.0)
        gen = st.number_input(
            _t(lang, "Annual gen kWh", "Жылдық өндіріс кВт·сағ"),
            1_000.0,
            5_000_000.0,
            120_000.0,
            1_000.0,
        )
    with c2:
        price = st.number_input(_t(lang, "Price $/kWh", "Баға $/кВт·сағ"), 0.01, 0.5, 0.10, 0.01)
        opex = st.number_input(_t(lang, "OPEX $/yr", "OPEX $/жыл"), 0.0, 100_000.0, 2_000.0, 100.0)
    with c3:
        life = st.slider(_t(lang, "Lifetime years", "Мерзім жыл"), 5, 30, 20, 1)
        rate = st.slider(_t(lang, "Discount rate", "Дисконт"), 0.0, 0.15, 0.05, 0.01)

    if not primary_button(_t(lang, "Compute KPIs", "KPI есептеу"), key="lab_fin_run"):
        empty_state(_t(lang, "No KPIs yet", "KPI жоқ"), icon="$")
        return

    k = community_project_kpis(
        capex=float(capex),
        annual_generation_kwh=float(gen),
        price_per_kwh=float(price),
        opex_annual=float(opex),
        lifetime_years=int(life),
        discount_rate=float(rate),
    )
    irr_v = k.get("irr")
    irr_s = f"{irr_v * 100:.1f}%" if irr_v == irr_v else "n/a"
    metric_row(
        [
            {"label": "LCOE", "value": f"{k.get('lcoe', k.get('lcoe_check', 0)):.4f}", "icon": "L", "variant": "solar"},
            {"label": "Payback yr", "value": f"{k.get('payback_years', 0):.1f}", "icon": "y", "variant": "warn"},
            {"label": "NPV $", "value": f"{k.get('npv', 0):.0f}", "icon": "N", "variant": "total"},
            {"label": "IRR", "value": irr_s, "icon": "r", "variant": "default"},
        ]
    )
    # Simple NPV sensitivity to discount rate
    rates = [i / 100.0 for i in range(0, 16)]
    npvs = [
        community_project_kpis(
            capex=float(capex),
            annual_generation_kwh=float(gen),
            price_per_kwh=float(price),
            opex_annual=float(opex),
            lifetime_years=int(life),
            discount_rate=r,
        )["npv"]
        for r in rates
    ]
    st.plotly_chart(
        themed_line(
            [r * 100 for r in rates],
            {"NPV $": npvs},
            title=_t(lang, "NPV vs discount rate %", "NPV vs дисконт %"),
            y_title="$",
            theme=theme,
        ),
        width="stretch",
    )
    with st.expander(_t(lang, "Full KPI dict", "Толық KPI")):
        st.json({kk: (None if isinstance(vv, float) and vv != vv else vv) for kk, vv in k.items()})
    _complete(lang, progress, "lab_rec_finance", lab.get("quiz_id"))


def _lab_grid_impact(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    from src.simulation.community.cacer_path import sim_cacer_status

    with st.expander(_t(lang, "Theory", "Теория"), expanded=True):
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or "grid_impact", lang))

    status = sim_cacer_status()
    empty_state(
        _t(
            lang,
            "P4 elective — run offline (not in Docker image)",
            "P4 қосымша — офлайн іске қосыңыз (Docker-де жоқ)",
        ),
        _t(
            lang,
            "Open the notebook locally after installing [sim-cacer]. Production image stays lean.",
            "Жергілікті [sim-cacer] орнатып, notebook ашыңыз. Production бейнесі жеңіл қалады.",
        ),
        icon="🔌",
    )

    st.subheader(_t(lang, "Environment status", "Орта күйі"))
    c1, c2, c3 = st.columns(3)
    c1.metric("CACER submodule", "OK" if status["cacer_present"] else "missing")
    c2.metric("pandapower", "OK" if status["pandapower"] else "missing")
    c3.metric("pvlib", "OK" if status["pvlib"] else "missing")

    st.markdown(
        _t(
            lang,
            """
**Install (local / advanced course only)**

```bash
pip install -e ".[sim-cacer]"
# or: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

**Run offline**

| Resource | Path |
|----------|------|
| EcoPradict notebook | `notebooks/labs/power_flow.ipynb` |
| CACER Tutorial 4 | `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb` |
| Upstream | [RSE-CoLabs/CACER_Simulator](https://github.com/RSE-CoLabs/CACER_Simulator) (BSD-3) |

Optional override: set env `ECOPREDICT_CACER_ROOT` to a local checkout.
""",
            """
**Орнату (тек жергілікті / advanced курс)**

```bash
pip install -e ".[sim-cacer]"
# немесе: pip install -r requirements-sim-cacer.txt
git submodule update --init --recursive third_party/CACER_Simulator
```

**Офлайн іске қосу**

| Ресурс | Жол |
|--------|-----|
| EcoPradict notebook | `notebooks/labs/power_flow.ipynb` |
| CACER Tutorial 4 | `third_party/CACER_Simulator/4. Tutorial_power_flow_simulator.ipynb` |
| Upstream | [RSE-CoLabs/CACER_Simulator](https://github.com/RSE-CoLabs/CACER_Simulator) (BSD-3) |

Қосымша: `ECOPREDICT_CACER_ROOT` орта айнымалысы.
""",
        )
    )

    if status.get("ecopredict_notebook"):
        st.code(str(status["ecopredict_notebook"]), language="text")
    if status.get("tutorial_power_flow"):
        st.caption(f"CACER tutorial: {status['tutorial_power_flow']}")
    elif status["cacer_present"]:
        st.warning(
            _t(
                lang,
                "Submodule present but Tutorial 4 filename not found.",
                "Submodule бар, бірақ Tutorial 4 файлы табылмады.",
            )
        )
    else:
        st.warning(
            _t(
                lang,
                "Submodule not checked out. Run git submodule update --init.",
                "Submodule жүктелмеген. git submodule update --init орындаңыз.",
            )
        )

    st.info(
        _t(
            lang,
            "xlwings / Excel / full Italian CACER dashboard are intentionally excluded.",
            "xlwings / Excel / толық итальяндық CACER dashboard әдейі кірмейді.",
        )
    )

    if primary_button(
        _t(lang, "Mark offline lab reviewed", "Офлайн зертхананы оқыдым деп белгілеу"),
        key="lab_grid_offline_done",
    ):
        _complete(lang, progress, "lab_grid_impact", lab.get("quiz_id"))


def _lab_inverter_wiring(lang: str, theme: str, progress: ProgressTracker, lab: dict) -> None:
    """3D Solar Inverter Subsystem + interactive wiring board tasks."""
    try:
        with st.expander(_t(lang, "Theory", "Теория"), expanded=False):
            katex_help_caption(lang)
            theory = _read_theory(lab.get("theory") or "inverter_wiring", lang)
            if theory:
                render_markdown_math(theory)
            else:
                st.caption(_t(lang, "Theory file missing.", "Теория файлы жоқ."))

        render_inverter_wiring_lab(lang, progress, height=500)
        st.caption(
            _t(
                lang,
                "Tip: open Fault A–E, set DC+ = PV+, DC− = PV−, press Check. Then theory tasks below.",
                "Кеңес: A–E ақауын ашыңыз, DC+ = PV+, DC− = PV− қойып Тексеру басыңыз. Сосын төмендегі тапсырмалар.",
            )
        )
    except Exception as e:
        error_state(
            _t(lang, "Inverter lab failed.", "Инвертор зертханасы сәтсіз."),
            detail=e,
            lang=lang,
        )
