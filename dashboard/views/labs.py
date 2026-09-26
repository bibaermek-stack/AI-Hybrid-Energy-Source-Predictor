"""
Streamlit page for the 12 education labs.

Every lab has four tabs: theory, the lab itself, practice tasks and the final
test. The lab tab is generated from the shared engine
(src/education/labs/runner.py) — the same parameters, simulation and results
the mobile app gets from the API — and lab 12 is the interactive 3D inverter
model (dashboard/components/lab3d.py).

Results are kept in session_state. The page used to draw them inside
``if st.button(...)``: they vanished on the next click, and the reflection quiz
under them could never be submitted (its button's rerun removed it). A lab now
counts as completed when its test is passed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st

from dashboard.components.lab_tasks_ui import render_lab_tasks_panel
from dashboard.components.markdown_math import katex_help_caption, render_markdown_math
from dashboard.components.metric_card import metric_row
from dashboard.components.states import empty_state, error_state, loading_state
from dashboard.components.status_badge import render_status_badge
from dashboard.components.ui_kit import section_header
from dashboard.utils.plotly_theme import apply_theme
from src.education.inverter_lab import grade_wiring
from src.education.labs.lab_registry import list_labs, t
from src.education.labs.lab_tests import grade_test, public_test
from src.education.labs.runner import list_params, run_lab
from src.education.progress import ProgressTracker

CONTENT = Path(__file__).resolve().parents[2] / "src" / "education" / "content" / "labs"
LAB_3D = "lab_inverter_wiring"


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def _loc(field: Any, lang: str) -> str:
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or "")
    return str(field or "")


def _read_theory(stem: str, lang: str) -> str:
    for suffix in (lang, "en"):
        path = CONTENT / f"{stem}_{suffix}.md"
        if path.is_file():
            return path.read_text(encoding="utf-8")
    return ""


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    try:
        _render("kk" if lang == "kk" else "en")
    except Exception as e:
        error_state(_t(lang, "Labs view failed.", "Зертхана беті сәтсіз."), detail=e, lang=lang)


def _render(lang: str) -> None:
    theme = str(st.session_state.get("ep_theme") or "Dark")
    progress = ProgressTracker.from_session(st.session_state)

    section_header(
        _t(lang, "Interactive laboratories", "Интерактивті зертханалар"),
        _t(
            lang,
            "12 labs: microgrid, community energy, grid and a 3D inverter model",
            "12 зертхана: микрожелі, қауымдастық энергиясы, желі және 3D инвертор моделі",
        ),
    )
    sm = progress.summary()
    render_status_badge(
        _t(
            lang,
            f"Labs passed: {sm.get('labs_completed', 0)} of 12",
            f"Өтілген зертхана: 12-нің {sm.get('labs_completed', 0)}-і",
        ),
        "accent",
    )

    labs = list_labs()
    labels = [
        f"{i + 1}. {t(L['title'], lang)} · {L['minutes']} min"
        + (" · 3D" if L["id"] == LAB_3D else "")
        for i, L in enumerate(labs)
    ]
    choice = st.selectbox(
        _t(lang, "Select lab", "Зертхана таңдау"),
        range(len(labs)),
        format_func=lambda i: labels[i],
        key="lab_select",
    )
    lab = labs[choice]
    lab_id = lab["id"]
    st.caption(f"{t(lab['level'], lang)} · {t(lab.get('tag', {}), lang)} · {lab['source']}")
    st.info(t(lab["objectives"], lang))
    # Always the same slot: an element appearing above the tabs would shift the
    # 3D component's position, and Streamlit would remount (reload) it.
    done_slot = st.empty()
    if progress.lab_done(lab_id):
        with done_slot:
            render_status_badge(
                _t(lang, "Test passed — lab completed", "Тест өтті — зертхана аяқталды"), "ok"
            )

    is_3d = lab_id == LAB_3D
    tabs = _tabs(
        [
            _t(lang, "Theory", "Теория"),
            _t(lang, "3D lab", "3D зертхана") if is_3d else _t(lang, "Lab", "Зертхана"),
            _t(lang, "Practice tasks", "Жаттығу тапсырмалары"),
            _t(lang, "Test", "Тест"),
        ],
        key=f"lab_tabs_{lab_id}_{lang}",
    )
    with tabs[0]:
        katex_help_caption(lang)
        render_markdown_math(_read_theory(lab.get("theory") or lab_id, lang))
    with tabs[1]:
        if is_3d:
            _lab3d_panel(lang, progress)
        else:
            _run_panel(lab_id, lang, theme, progress)
    with tabs[2]:
        render_lab_tasks_panel(lab_id, lang, progress, expanded=True, require_all_for_lab=False)
    with tabs[3]:
        if is_3d:
            _lab3d_test_note(lang)
        else:
            _test_panel(lab_id, lang, progress)


def _tabs(labels: list[str], key: str):
    """Tabs that keep the open tab across reruns (running a lab, submitting a test)."""
    try:
        return st.tabs(labels, key=key)
    except TypeError:  # Streamlit before stateful tabs
        return st.tabs(labels)


# ------------------------------------------------------------------ lab tab


def _widget_key(lab_id: str, key: str) -> str:
    return f"lp_{lab_id}_{key}"


def _is_int(spec: dict[str, Any]) -> bool:
    return all(float(spec[k]).is_integer() for k in ("min", "max", "step", "default"))


def _param_widget(lab_id: str, spec: dict[str, Any], lang: str) -> None:
    wkey = _widget_key(lab_id, spec["key"])
    label = _loc(spec["label"], lang) + (f", {spec['unit']}" if spec.get("unit") else "")
    if spec["kind"] == "select":
        st.session_state.setdefault(wkey, spec["default"])
        labels = {o["id"]: _loc(o["label"], lang) for o in spec["options"]}
        st.selectbox(label, list(labels), format_func=lambda i: labels[i], key=wkey)
        return
    if _is_int(spec):
        st.session_state.setdefault(wkey, int(spec["default"]))
        st.slider(label, int(spec["min"]), int(spec["max"]), step=int(spec["step"]), key=wkey)
    else:
        st.session_state.setdefault(wkey, float(spec["default"]))
        st.slider(label, float(spec["min"]), float(spec["max"]), step=float(spec["step"]), key=wkey)


def _apply_params(lab_id: str, params: dict[str, Any]) -> None:
    """Button callback: put a test question's settings into the lab form and run it."""
    for spec in list_params(lab_id):
        if spec["key"] in params:
            v = params[spec["key"]]
            st.session_state[_widget_key(lab_id, spec["key"])] = (
                int(v) if spec["kind"] == "slider" and _is_int(spec) else v
            )
    st.session_state[f"lab_autorun_{lab_id}"] = True


def _run_panel(lab_id: str, lang: str, theme: str, progress: ProgressTracker) -> None:
    specs = list_params(lab_id)
    with st.form(f"lab_form_{lab_id}"):
        cols = st.columns(3)
        for i, spec in enumerate(specs):
            with cols[i % 3]:
                _param_widget(lab_id, spec, lang)
        submitted = st.form_submit_button(
            _t(lang, "Run the lab", "Зертхананы іске қосу"), type="primary"
        )
    autorun = st.session_state.pop(f"lab_autorun_{lab_id}", False)

    res_key = f"lab_result_{lab_id}"
    if submitted or autorun:
        params = {s["key"]: st.session_state[_widget_key(lab_id, s["key"])] for s in specs}
        with loading_state(_t(lang, "Simulating…", "Есептелуде…")):
            try:
                st.session_state[res_key] = run_lab(lab_id, params)
                progress.mark_exercise(f"sim:{lab_id}")
            except Exception as e:  # show the reason instead of a blank tab
                st.session_state.pop(res_key, None)
                error_state(str(e), detail=e, lang=lang)
                return
        if autorun:
            st.success(
                _t(
                    lang,
                    "The test question's settings were applied and the lab was run.",
                    "Тест сұрағының параметрлері қойылып, зертхана іске қосылды.",
                )
            )

    result = st.session_state.get(res_key)
    if not result:
        empty_state(
            _t(lang, "No run yet", "Әлі іске қосылмаған"),
            _t(
                lang,
                "Set the parameters and press Run.",
                "Параметрлерді қойып, «Іске қосу» басыңыз.",
            ),
            icon="⚙",
        )
        return
    _render_result(result, lang, theme)


def _fmt(m: dict[str, Any]) -> str:
    if m["value"] is None:
        return "—"
    value = f"{m['value']:,.{m['digits']}f}".replace(",", " ")
    return f"{value} {m['unit']}".strip()


def _render_result(result: dict[str, Any], lang: str, theme: str) -> None:
    metrics = result["metrics"]
    for start in range(0, len(metrics), 4):
        metric_row(
            [
                {"label": _loc(m["label"], lang), "value": _fmt(m), "icon": "◆"}
                for m in metrics[start : start + 4]
            ]
        )
    for note in result.get("notes") or []:
        st.warning(_loc(note, lang))
    for ch in result["charts"]:
        fig = go.Figure()
        for s in ch["series"]:
            fig.add_trace(
                go.Scatter(x=ch["x"], y=s["values"], mode="lines", name=_loc(s["name"], lang))
            )
        for lim in ch.get("limits") or []:
            fig.add_hline(
                y=lim["value"],
                line_dash="dash",
                line_color="#f87171",
                annotation_text=_loc(lim["label"], lang),
                annotation_position="top left",
            )
        apply_theme(
            fig,
            theme,
            title=_loc(ch["title"], lang),
            xaxis_title=_loc(ch["x_label"], lang),
            yaxis_title=ch["y_label"],
            height=380,
        )
        st.plotly_chart(fig, width="stretch")


# ------------------------------------------------------------------ test tab


def _test_panel(lab_id: str, lang: str, progress: ProgressTracker) -> None:
    test = public_test(lab_id, lang)
    res_key = f"lab_test_result_{lab_id}"
    result = st.session_state.get(res_key)
    st.caption(
        _t(
            lang,
            f"{len(test['questions'])} questions · pass mark {test['pass_percent']:.0f} %. "
            "Questions marked ▶ are answered by running the lab with the given settings.",
            f"{len(test['questions'])} сұрақ · өту шегі {test['pass_percent']:.0f} %. "
            "▶ белгісі бар сұраққа зертхананы берілген параметрлермен іске қосып жауап бересіз.",
        )
    )

    for q in test["questions"]:
        if q["kind"] == "run":
            with st.expander(
                f"▶ {q['id'].upper()} — " + _t(lang, "settings to use", "қолданылатын параметрлер")
            ):
                st.markdown(
                    "\n".join(f"- {r['label']}: **{r['value']}**" for r in q["params_display"])
                )
                st.button(
                    _t(
                        lang,
                        "Put these settings into the Lab tab and run it",
                        "Осы параметрлерді «Зертхана» бөліміне қойып, іске қосу",
                    ),
                    key=f"apply_{lab_id}_{q['id']}",
                    on_click=_apply_params,
                    args=(lab_id, q["params"]),
                )

    details = {d["id"]: d for d in (result or {}).get("details", [])}
    with st.form(f"lab_test_form_{lab_id}"):
        for i, q in enumerate(test["questions"], start=1):
            mark = "▶ " if q["kind"] == "run" else ""
            st.markdown(f"**{mark}{i}. {q['prompt']}**")
            key = f"ltest_{lab_id}_{q['id']}"
            if q["kind"] == "choice":
                st.radio(
                    q["prompt"],
                    list(range(len(q["choices"]))),
                    index=None,
                    format_func=lambda j, ch=q["choices"]: ch[j],
                    key=key,
                    label_visibility="collapsed",
                )
            else:
                unit = q.get("unit") or ""
                st.text_input(
                    _t(lang, "Your answer", "Жауабыңыз") + (f" ({unit})" if unit else ""), key=key
                )
            d = details.get(q["id"])
            if d:
                if d["correct"]:
                    st.success(_t(lang, "Correct. ", "Дұрыс. ") + d["explain"])
                else:
                    st.error(_t(lang, "Wrong. ", "Қате. ") + d["explain"])
        st.form_submit_button(
            _t(lang, "Submit the test", "Тестті тапсыру"),
            type="primary",
            on_click=_submit_test,
            args=(lab_id, [q["id"] for q in test["questions"]], lang),
        )

    if result:
        _test_summary(result, lang)


def _submit_test(lab_id: str, qids: list[str], lang: str) -> None:
    """Form callback: runs before the page is redrawn, so the feedback shows at once."""
    answers = {qid: st.session_state.get(f"ltest_{lab_id}_{qid}") for qid in qids}
    r = grade_test(lab_id, answers, lang)
    st.session_state[f"lab_test_result_{lab_id}"] = r
    _record_test(ProgressTracker.from_session(st.session_state), lab_id, r)


def _record_test(progress: ProgressTracker, lab_id: str, r: dict[str, Any]) -> None:
    progress.record_quiz(f"{lab_id}_test", float(r["percent"]))
    if r["passed"]:
        progress.mark_lab(lab_id)


def _test_summary(r: dict[str, Any], lang: str) -> None:
    text = _t(
        lang,
        f"Score {r['score']} of {r['total']} ({r['percent']:.0f} %).",
        f"Нәтиже: {r['total']}-тің {r['score']}-і ({r['percent']:.0f} %).",
    )
    if r["passed"]:
        st.success(
            text + " " + _t(lang, "Passed — the lab is completed.", "Өтті — зертхана аяқталды.")
        )
    else:
        st.warning(
            text
            + " "
            + _t(
                lang,
                f"Pass mark is {r['pass_percent']:.0f} %. Review and try again.",
                f"Өту шегі {r['pass_percent']:.0f} %. Қайталап, қайта тапсырыңыз.",
            )
        )


# ------------------------------------------------------------------ 3D lab


def _lab3d_panel(lang: str, progress: ProgressTracker) -> None:
    from dashboard.components.lab3d import lab3d_viewer

    st.caption(
        _t(
            lang,
            "CAD model «Solar Inverter Subsystem». Explore: tap a part to learn what it is. Fix faults: pick a scenario, "
            "inspect the parts, operate them and check the system. Test: 7 questions, some answered in the model.",
            "«Solar Inverter Subsystem» CAD моделі. Зерттеу: бөлікті басып, не екенін біліңіз. Ақауды түзету: сценарий "
            "таңдап, бөліктерді тексеріп, басқарып, жүйені тексеріңіз. Тест: 7 сұрақ, кейбіріне модельде жауап бересіз.",
        )
    )
    test = public_test(LAB_3D, lang)
    test["version"] = lang
    result = st.session_state.get("lab3d_test_result")
    event = lab3d_viewer(lang=lang, test=test, test_result=result, height=680, key=f"lab3d_{lang}")
    if event and event.get("type") == "check":
        g = grade_wiring(event.get("state") or {})
        st.session_state["lab3d_last_check"] = {
            "scenario": event.get("scenario"),
            "ok": g["ok"],
            "score": g["score"],
            "total": g["total"],
        }
        if g["ok"] and event.get("scenario"):
            progress.mark_task(LAB_3D, f"scenario_{event['scenario']}")
    elif event and event.get("type") == "test_submit":
        r = grade_test(LAB_3D, event.get("answers") or {}, lang)
        r["nonce"] = event.get("nonce")
        st.session_state["lab3d_test_result"] = r
        _record_test(progress, LAB_3D, r)
        st.rerun()  # hand the result to the viewer

    fixed = [
        tid.removeprefix("scenario_")
        for tid in progress.tasks_done_for(LAB_3D)
        if tid.startswith("scenario_")
    ]
    if fixed:
        st.caption(
            _t(lang, "Scenarios fixed: ", "Түзетілген сценарийлер: ") + ", ".join(sorted(fixed))
        )
    last = st.session_state.get("lab3d_last_check")
    if last and not last["ok"]:
        st.caption(
            _t(
                lang,
                f"Last check: {last['score']} of {last['total']} items right.",
                f"Соңғы тексеру: {last['total']} тармақтың {last['score']}-і дұрыс.",
            )
        )


def _lab3d_test_note(lang: str) -> None:
    st.info(
        _t(
            lang,
            "This lab's test runs inside the 3D model: open the «3D lab» tab and choose «Test».",
            "Бұл зертхананың тесті 3D модельдің ішінде: «3D зертхана» бөлімін ашып, «Тест» таңдаңыз.",
        )
    )
    result = st.session_state.get("lab3d_test_result")
    if result:
        _test_summary(result, lang)
