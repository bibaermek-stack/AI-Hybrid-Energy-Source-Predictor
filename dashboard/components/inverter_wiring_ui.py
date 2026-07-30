"""Streamlit wiring board for Solar Inverter Subsystem training lab."""

from __future__ import annotations

from urllib.parse import quote

import streamlit as st

from dashboard.components.inverter_3d import resolve_viewer_base
from dashboard.components.markdown_math import render_markdown_math
from src.education.inverter_lab import (
    CHOICES,
    CORRECT,
    PORTS,
    diagnose_faults,
    get_scenario,
    grade_wiring,
    initial_state,
    list_scenarios,
    port_label,
)
from src.education.progress import ProgressTracker


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def _state_key(scenario_id: str) -> str:
    return f"inv_wire_state_{scenario_id}"


def _loc(field, lang: str, default: str = "") -> str:
    """Safe EN/KK dict or plain string extractor (never raises on None)."""
    if field is None:
        return default
    if isinstance(field, dict):
        return str(field.get(lang) or field.get("en") or field.get("kk") or default)
    return str(field)


def render_inverter_wiring_lab(
    lang: str,
    progress: ProgressTracker,
    *,
    height: int = 480,
) -> None:
    lang = "kk" if lang == "kk" else "en"

    try:
        _render_body(lang, progress, height=height)
    except Exception as e:
        st.error(
            _t(
                lang,
                f"Inverter wiring board error: {type(e).__name__}: {e}",
                f"Инвертор сым тақтасы қатесі: {type(e).__name__}: {e}",
            )
        )
        with st.expander(_t(lang, "Details", "Толығырақ")):
            st.exception(e)


def _render_body(lang: str, progress: ProgressTracker, *, height: int) -> None:
    st.subheader(
        _t(
            lang,
            "Inverter 3D + wiring tasks",
            "Инвертор 3D + сым тапсырмалары",
        )
    )
    st.caption(
        _t(
            lang,
            "Based on CAD assembly «Solar Inverter Subsystem»: replace / reconnect "
            "DC cables, AC L/N, PE, isolator and data logger. Wrong → try again.",
            "CAD «Solar Inverter Subsystem» моделі бойынша: DC кабель, AC L/N, PE, "
            "ажыратқыш және logger-ді ауыстыру / қайтадан қосу. Қате → қайтадан көріңіз.",
        )
    )

    scenarios = list_scenarios(lang) or []
    if not scenarios:
        st.warning(_t(lang, "No scenarios configured.", "Сценарийлер жоқ."))
        return

    ids = [s.get("id") for s in scenarios if s.get("id")]
    if not ids:
        st.warning(_t(lang, "Scenario ids missing.", "Сценарий id жоқ."))
        return

    title_map = {s["id"]: s.get("title") or s["id"] for s in scenarios if s.get("id")}

    sid = st.selectbox(
        _t(lang, "Training scenario", "Оқу сценарийі"),
        ids,
        format_func=lambda i: str(title_map.get(i, i)),
        key="inv_scenario_sel",
    )
    sc = get_scenario(str(sid)) or {}

    st.info(_loc(sc.get("title"), lang, str(sid)))
    story = _loc(sc.get("story"), lang, "")
    if story:
        st.markdown(story)
    symptoms = _loc(sc.get("symptoms"), lang, "")
    if symptoms:
        st.caption(_t(lang, "Symptoms: ", "Белгілері: ") + symptoms)

    # Reset board when scenario changes (+ clear port widget keys)
    prev = st.session_state.get("inv_scenario_prev")
    if prev != sid:
        st.session_state[_state_key(str(sid))] = initial_state(str(sid))
        st.session_state["inv_scenario_prev"] = sid
        # Drop widget state for previous scenario ports to avoid stale values
        if prev:
            for port in PORTS:
                st.session_state.pop(f"inv_port_{prev}_{port}", None)

    sk = _state_key(str(sid))
    raw_state = st.session_state.get(sk)
    if not isinstance(raw_state, dict):
        raw_state = initial_state(str(sid))
        st.session_state[sk] = raw_state
    state: dict[str, str] = {str(k): str(v) for k, v in raw_state.items()}

    focus_raw = sc.get("focus_parts")
    focus: list[str] = [str(x) for x in focus_raw] if isinstance(focus_raw, (list, tuple)) else []

    try:
        from dashboard.static_server import ensure_streamlit_static_assets

        ensure_streamlit_static_assets()
    except Exception:
        pass

    base, src = resolve_viewer_base()
    qs = (
        f"lang={lang}"
        f"&scenario={quote(str(sid))}"
        f"&focus={quote(','.join(focus))}"
    )
    url = f"{str(base).rstrip('/')}/inverter_lab_viewer.html?{qs}" if base else ""

    view_mode = st.radio(
        _t(lang, "3D display mode", "3D көрсету режимі"),
        ["board_only", "fullscreen_first", "embed"],
        horizontal=True,
        format_func=lambda m: {
            "board_only": _t(lang, "Wiring board only (no 3D)", "Тек сым тақтасы (3D жоқ)"),
            "fullscreen_first": _t(
                lang, "Full-screen 3D link (recommended)", "3D толық экран сілтемесі (ұсынылады)"
            ),
            "embed": _t(lang, "Embed 3D in page", "Бетте 3D iframe"),
        }[m],
        key="inv_3d_view_mode",
        index=1,  # fullscreen_first default
    )

    if view_mode == "board_only":
        st.info(
            _t(
                lang,
                "Board-only mode: complete wiring tasks without WebGL. Fast and reliable.",
                "Тек тақта: WebGLсіз сым тапсырмалары. Жылдам және тұрақты.",
            )
        )
    elif view_mode == "fullscreen_first":
        st.markdown("#### " + _t(lang, "3D assembly (full screen)", "3D құрастырма (толық экран)"))
        if url:
            st.caption(_t(lang, f"Viewer source: {src}", f"Көру көзі: {src}"))
            st.link_button(
                _t(lang, "Open 3D full screen", "3D толық экранды ашу"),
                url,
                type="primary",
            )
            st.caption(
                _t(
                    lang,
                    "Open 3D in a new tab, identify parts (DC+, isolator…), then fix the board below.",
                    "3D-ны жаңа tab-та ашып, бөліктерді танып (DC+, ажыратқыш…), төмендегі тақтаны түзетіңіз.",
                )
            )
        else:
            st.warning(
                _t(
                    lang,
                    f"3D unavailable ({src}). Use board-only mode.",
                    f"3D жоқ ({src}). Тек тақта режимін қолданыңыз.",
                )
            )
    else:
        # embed
        st.markdown("#### " + _t(lang, "3D assembly (embedded)", "3D құрастырма (iframe)"))
        if url:
            import streamlit.components.v1 as components

            st.caption(_t(lang, f"Viewer source: {src}", f"Көру көзі: {src}"))
            st.link_button(
                _t(lang, "Also open full screen", "Толық экран да ашу"),
                url,
            )
            components.html(
                f'<iframe src="{url}" style="width:100%;height:{int(height)}px;border:0;'
                f'border-radius:12px;background:#0b0f19;" allow="fullscreen" '
                f'allowfullscreen></iframe>',
                height=int(height) + 8,
                scrolling=False,
            )
        else:
            st.warning(
                _t(
                    lang,
                    f"3D static server unavailable ({src}). Wiring board still works.",
                    f"3D сервер жоқ ({src}). Сым тақтасы жұмыс істейді.",
                )
            )

    st.markdown("---")
    st.markdown(
        "#### " + _t(lang, "Wiring board (fix here)", "Сым тақтасы (мұнда түзетіңіз)")
    )
    if st.button(
        _t(lang, "Reset scenario faults", "Сценарий ақауларын қайта жүктеу"),
        key="inv_reset",
    ):
        st.session_state[sk] = initial_state(str(sid))
        for port in PORTS:
            st.session_state.pop(f"inv_port_{sid}_{port}", None)
        st.rerun()

    new_state: dict[str, str] = {}
    for port in PORTS:
        choices = CHOICES.get(port) or []
        if not choices:
            continue
        option_ids = [str(c.get("id", "")) for c in choices if c.get("id")]
        if not option_ids:
            continue
        labels: dict[str, str] = {}
        for c in choices:
            cid = str(c.get("id") or "")
            if not cid:
                continue
            labels[cid] = str(c.get(lang) or c.get("en") or c.get("kk") or cid)

        cur = str(state.get(port) or CORRECT.get(port) or option_ids[0])
        if cur not in option_ids:
            cur = option_ids[0]
        idx = option_ids.index(cur)

        pick = st.selectbox(
            port_label(port, lang),
            option_ids,
            index=idx,
            format_func=lambda i, lab=labels: lab.get(i, i),
            key=f"inv_port_{sid}_{port}",
        )
        new_state[port] = str(pick)

    st.session_state[sk] = new_state
    state = new_state

    faults = diagnose_faults(state)
    if faults:
        st.error(_t(lang, "Active faults: ", "Белсенді ақаулар: ") + ", ".join(faults))
    else:
        st.success(
            _t(
                lang,
                "No wiring faults detected on the board.",
                "Тақтада сым ақауы анықталмады.",
            )
        )

    if st.button(
        _t(lang, "Check wiring", "Сымды тексеру"),
        type="primary",
        key="inv_check",
    ):
        result = grade_wiring(state)
        if result.get("ok"):
            st.success(
                _t(
                    lang,
                    f"Correct! All {result.get('total', 0)} ports healthy.",
                    f"Дұрыс! Барлық {result.get('total', 0)} порт сау.",
                )
            )
            try:
                progress.mark_task("lab_inverter_wiring", f"scenario_{sid}")
                progress.mark_exercise(f"lab_inverter_wiring_{sid}")
                done = progress.tasks_done_for("lab_inverter_wiring")
                if len(done) >= 3 or sid == "compound":
                    progress.mark_lab("lab_inverter_wiring")
            except Exception as pe:
                st.warning(str(pe))
            st.balloons()
        else:
            st.error(
                _t(
                    lang,
                    f"Incorrect ({result.get('score', 0)}/{result.get('total', 0)}). Try again.",
                    f"Қате ({result.get('score', 0)}/{result.get('total', 0)}). Қайтадан көріңіз.",
                )
            )
            wrong = result.get("wrong_ports") or []
            if wrong:
                st.warning(
                    _t(lang, "Still wrong: ", "Әлі қате: ")
                    + ", ".join(port_label(p, lang) for p in wrong)
                )
            st.caption(
                _t(
                    lang,
                    "Hint: fix DC polarity (PV+→DC+, PV−→DC−), isolator ON, logger seated.",
                    "Кеңес: DC полярлық (PV+→DC+, PV−→DC−), ажыратқыш ON, logger тығыз.",
                )
            )

    with st.expander(
        _t(lang, "Correct topology (reference)", "Дұрыс топология (анықтама)"),
        expanded=False,
    ):
        render_markdown_math(
            _t(
                lang,
                r"""
| Port | Must connect to |
|------|-----------------|
| DC+ | PV string **+** |
| DC− | PV string **−** |
| PE | Site earth |
| AC L | Grid L |
| AC N | Grid N |
| Isolator | **ON** (closed) for export |
| Logger | Seated on COM |

Safety: de-energize before physical work; this lab is a digital trainer only.
""",
                r"""
| Порт | Қосылуы керек |
|------|----------------|
| DC+ | PV тізбек **+** |
| DC− | PV тізбек **−** |
| PE | Жер шинасы |
| AC L | Желі L |
| AC N | Желі N |
| Ажыратқыш | Экспорт үшін **ON** |
| Logger | COM-ға тығыз |

Қауіпсіздік: нақты жұмыста алдымен кернеусіздендіру; бұл тек цифрлық тренажер.
""",
            )
        )
