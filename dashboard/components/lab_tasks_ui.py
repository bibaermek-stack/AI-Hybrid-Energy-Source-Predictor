"""Streamlit UI: interactive graded lab tasks with correct / wrong / try-again."""

from __future__ import annotations

import streamlit as st

from dashboard.components.markdown_math import render_latex, render_markdown_math
from src.education.lab_tasks import check_task_answer, get_lab_tasks, lab_tasks_progress
from src.education.progress import ProgressTracker


def _t(lang: str, en: str, kk: str) -> str:
    return kk if lang == "kk" else en


def render_lab_tasks_panel(
    lab_id: str,
    lang: str,
    progress: ProgressTracker,
    *,
    expanded: bool = True,
    require_all_for_lab: bool = True,
) -> dict:
    """
    Render graded tasks for a lab.

    Feedback:
      - correct → green success, mark task done
      - wrong → red error + "Try again" + hint (answer not leaked)
      - missing → warning

    When all tasks are correct and ``require_all_for_lab``, marks lab complete.
    Returns progress dict from ``lab_tasks_progress``.
    """
    lang = "kk" if lang == "kk" else "en"
    tasks = get_lab_tasks(lab_id, lang)
    if not tasks:
        return lab_tasks_progress(lab_id, [])

    done_ids = progress.tasks_done_for(lab_id)
    prog = lab_tasks_progress(lab_id, done_ids)

    with st.expander(
        _t(
            lang,
            f"Tasks to complete ({prog['done']}/{prog['total']})",
            f"Орындалатын тапсырмалар ({prog['done']}/{prog['total']})",
        ),
        expanded=expanded,
    ):
        st.caption(
            _t(
                lang,
                "Enter answers and press Check. Wrong answers: error + try again.",
                "Жауапты енгізіп, Тексеру басыңыз. Қате болса: қате + қайтадан көріңіз.",
            )
        )
        st.progress(prog["percent"] / 100.0 if prog["total"] else 0.0)
        st.caption(
            _t(
                lang,
                f"Progress: {prog['done']} of {prog['total']} tasks correct ({prog['percent']}%)",
                f"Прогресс: {prog['done']} / {prog['total']} тапсырма дұрыс ({prog['percent']}%)",
            )
        )

        for i, task in enumerate(tasks, start=1):
            tid = task["id"]
            is_done = progress.task_done(lab_id, tid)
            status_icon = "✅" if is_done else "⬜"
            st.markdown(f"### {status_icon} {_t(lang, 'Task', 'Тапсырма')} {i}")
            render_markdown_math(task["prompt"])
            if task.get("formula"):
                try:
                    st.caption(_t(lang, "Formula", "Формула"))
                    render_latex(str(task["formula"]))
                except Exception:
                    st.code(str(task["formula"]))

            key_base = f"lt_{lab_id}_{tid}"
            if is_done:
                st.success(
                    _t(
                        lang,
                        "Completed ✓",
                        "Орындалды ✓",
                    )
                )
                # Still show explanation
                render_markdown_math(task["explain"])
                continue

            number_val: float | None = None
            choice_idx: int | None = None

            if task["kind"] == "number":
                label = _t(lang, "Your answer", "Сіздің жауабыңыз")
                if task.get("unit"):
                    label = f"{label} ({task['unit']})"
                number_val = st.number_input(
                    label,
                    value=0.0,
                    format="%.4f",
                    key=f"{key_base}_num",
                )
            else:
                choices = list(task.get("choices") or [])
                if not choices:
                    st.warning(_t(lang, "No choices configured.", "Нұсқалар жоқ."))
                    continue
                choice_idx = st.radio(
                    _t(lang, "Select answer", "Жауапты таңдаңыз"),
                    list(range(len(choices))),
                    format_func=lambda j, ch=choices: (
                        ch[j] if isinstance(j, int) and 0 <= j < len(ch) else str(j)
                    ),
                    key=f"{key_base}_ch",
                )

            col_a, col_b = st.columns([1, 2])
            with col_a:
                check = st.button(
                    _t(lang, "Check", "Тексеру"),
                    key=f"{key_base}_btn",
                    type="primary",
                )
            with col_b:
                if st.button(
                    _t(lang, "Show hint", "Кеңес"),
                    key=f"{key_base}_hint",
                ):
                    st.session_state[f"{key_base}_show_hint"] = True

            if st.session_state.get(f"{key_base}_show_hint"):
                st.info(task["hint"])

            if check:
                result = check_task_answer(
                    lab_id,
                    tid,
                    number=float(number_val) if number_val is not None else None,
                    choice_index=int(choice_idx) if choice_idx is not None else None,
                )
                msg = result["message_kk"] if lang == "kk" else result["message_en"]
                exp = result["explain_kk"] if lang == "kk" else result["explain_en"]

                if result["status"] == "correct":
                    progress.mark_task(lab_id, tid)
                    st.success(msg)
                    render_markdown_math(exp)
                    st.balloons()
                    # Rerun so UI shows completed state
                    st.rerun()
                elif result["status"] == "wrong":
                    st.error(msg)
                    st.warning(
                        _t(
                            lang,
                            "Try again — use the hint and the Theory formulas.",
                            "Қайтадан көріңіз — кеңес пен Теория формулаларын қолданыңыз.",
                        )
                    )
                    if exp:
                        st.caption(exp)
                elif result["status"] == "missing":
                    st.warning(msg)
                else:
                    st.error(msg)

            st.divider()

        # Refresh progress after possible marks
        done_ids = progress.tasks_done_for(lab_id)
        prog = lab_tasks_progress(lab_id, done_ids)

        if prog["complete"]:
            st.success(
                _t(
                    lang,
                    "All tasks completed for this lab!",
                    "Осы зертхананың барлық тапсырмалары орындалды!",
                )
            )
            if require_all_for_lab and not progress.lab_done(lab_id):
                progress.mark_lab(lab_id)
                st.info(
                    _t(
                        lang,
                        "Lab marked complete (all tasks passed).",
                        "Зертхана орындалды деп белгіленді (барлық тапсырма дұрыс).",
                    )
                )
        else:
            left = prog["total"] - prog["done"]
            st.warning(
                _t(
                    lang,
                    f"{left} task(s) still incomplete. Lab completes when all are correct.",
                    f"{left} тапсырма әлі орындалмаған. Барлығы дұрыс болғанда зертхана аяқталады.",
                )
            )

    return prog
