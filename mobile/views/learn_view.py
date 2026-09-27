"""
Learn: the six lessons of the website's Learn page, each with its quiz.

Lessons come from the API (api/learn.py) as Markdown with the formulas; the
quiz is graded on the server and the best score is kept on the phone. Each
lesson links to the labs and app screens where it is put into practice. The
four short basics cards the screen used to be are kept under the lessons.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

import flet as ft

try:
    from mobile import api_client as api_client_module
    from mobile.api_client import api_client
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

PREF_BEST = "ecopredict.learn_best"  # {quiz_id: best percent}
PASS_PERCENT = 70
SCREEN_KEYS = {
    "forecast": "nav_forecast",
    "faults": "nav_faults",
    "opt": "nav_opt",
    "training": "nav_training",
    "chat": "nav_chat",
    "sustainability": "nav_sustainability",
    "live": "nav_live",
}


def _loc(field: Any) -> str:
    if isinstance(field, dict):
        return str(field.get(state.lang) or field.get("en") or "")
    return str(field or "")


def _reason() -> str:
    return getattr(api_client_module, "last_http_error", "") or state.text("reason_unknown")


def build_learn_view(
    page: ft.Page,
    navigate: Optional[Callable[[str], None]] = None,
    set_back_handler: Optional[Callable[[Optional[Callable[[], bool]]], None]] = None,
    prefs: Optional[Any] = None,
) -> ft.Control:
    c = state.colors
    t = state.text
    root = ft.Column(expand=True, spacing=0)
    data: Dict[str, Any] = {"lessons": None, "best": {}, "open": None, "loading": False}

    def register_back(handler: Optional[Callable[[], bool]]) -> None:
        if set_back_handler:
            set_back_handler(handler)

    async def load_best() -> None:
        if prefs is None:
            return
        try:
            raw = await asyncio.wait_for(prefs.get(PREF_BEST), timeout=3)
            best = json.loads(raw) if raw else {}
            data["best"] = {k: float(v) for k, v in best.items() if isinstance(v, (int, float))}
        except Exception as err:
            print(f"Quiz scores not loaded: {err}")

    async def record_best(quiz_id: str, percent: float) -> None:
        if percent <= data["best"].get(quiz_id, -1):
            return
        data["best"][quiz_id] = percent
        if prefs is not None:
            try:
                await prefs.set(PREF_BEST, json.dumps(data["best"]))
            except Exception as err:
                print(f"Quiz score not saved: {err}")

    # ---- the list: lessons, then the basics cards ----------------------------
    list_view = ft.ListView(spacing=10, padding=12, expand=True)
    status = ft.Text("", size=12, color=c["text_secondary"], selectable=True)

    def lesson_card(index: int, lesson: Dict[str, Any]) -> ft.Control:
        badges = [
            ft.Text(
                t("lab_minutes", n=lesson.get("minutes", "")), size=11, color=c["text_secondary"]
            ),
            ft.Text(str(lesson.get("level", "")), size=11, color=c["text_secondary"]),
        ]
        best = data["best"].get(lesson.get("related_quiz") or "")
        if best is not None:
            badges.append(
                ft.Text(
                    t("learn_best", p=f"{best:.0f}"),
                    size=11,
                    color=c["success"] if best >= PASS_PERCENT else c["warning"],
                )
            )
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Icon(ft.Icons.MENU_BOOK, color=c["primary"], size=18),
                        width=34,
                        height=34,
                        alignment=ft.Alignment.CENTER,
                        border_radius=17,
                        bgcolor=c["surface_variant"],
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                f"{index}. {lesson.get('title', '')}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=c["text_primary"],
                            ),
                            ft.Row(badges, spacing=10, wrap=True),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=c["text_secondary"]),
                ],
                spacing=12,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
            on_click=lambda e, lesson=lesson: page.run_task(open_lesson, lesson),
            data=f"lesson:{lesson['id']}",
        )

    def basics_cards() -> List[ft.Control]:
        topics = [
            ("learn_pv_title", "learn_pv_body", c["accent"]),
            ("learn_wind_title", "learn_wind_body", c["secondary"]),
            ("learn_bess_title", "learn_bess_body", c["success"]),
            ("learn_dispatch_title", "learn_dispatch_body", c["primary"]),
        ]
        return [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            t(title), size=13, weight=ft.FontWeight.BOLD, color=c["text_primary"]
                        ),
                        ft.Text(t(body), size=12, color=c["text_secondary"]),
                    ],
                    spacing=6,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(1, color),
            )
            for title, body, color in topics
        ]

    def render_list() -> None:
        list_view.controls = [
            ft.Text(t("learn_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("learn_sub"), size=11, color=c["text_secondary"]),
            status,
        ]
        for i, lesson in enumerate(data["lessons"] or [], start=1):
            list_view.controls.append(lesson_card(i, lesson))
        list_view.controls.append(
            ft.Text(t("learn_basics"), size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"])
        )
        list_view.controls.extend(basics_cards())

    def show_list() -> None:
        data["open"] = None
        register_back(None)
        render_list()
        root.controls = [list_view]
        page.update()

    async def load_list() -> None:
        if data["loading"]:
            return
        data["loading"] = True
        status.value, status.color = t("learn_loading"), c["text_secondary"]
        render_list()
        page.update()
        await load_best()
        lessons = await api_client.learn_lessons()
        data["loading"] = False
        if lessons is None:
            status.value, status.color = t("learn_err", reason=_reason()), c["error"]
        else:
            data["lessons"] = lessons
            status.value, status.color = api_client.cache_note("lessons"), c["warning"]
        render_list()
        page.update()

    # ---- one lesson ------------------------------------------------------------
    def back_to_list() -> bool:
        if data["open"] is None:
            return False
        show_list()
        return True

    async def open_lesson(card: Dict[str, Any]) -> None:
        data["open"] = card["id"]
        register_back(back_to_list)
        root.controls = [
            ft.Container(ft.ProgressRing(), alignment=ft.Alignment.CENTER, expand=True)
        ]
        page.update()
        lesson = await api_client.learn_lesson(card["id"])
        if data["open"] != card["id"]:
            return
        if lesson is None:
            root.controls = [
                ft.ListView(
                    [
                        ft.Text(
                            t("learn_err", reason=_reason()), color=c["error"], selectable=True
                        ),
                        ft.Button(
                            t("labs_retry"),
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: page.run_task(open_lesson, card),
                        ),
                    ],
                    padding=12,
                    expand=True,
                )
            ]
        else:
            root.controls = [build_lesson(lesson)]
        page.update()

    def go(target: str) -> None:
        if navigate is not None:
            navigate(target)

    def build_lesson(lesson: Dict[str, Any]) -> ft.Control:
        body = ft.ListView(spacing=10, padding=12, expand=True)
        note = api_client.cache_note(f"lesson:{lesson['id']}")
        items: List[ft.Control] = [
            ft.Row(
                [
                    ft.IconButton(
                        ft.Icons.ARROW_BACK,
                        on_click=lambda e: back_to_list(),
                        icon_color=c["text_primary"],
                        tooltip=t("learn_back"),
                    ),
                    ft.Text(
                        lesson.get("title", ""),
                        size=15,
                        weight=ft.FontWeight.BOLD,
                        color=c["text_primary"],
                        expand=True,
                    ),
                ],
                spacing=4,
            ),
            ft.Text(
                f"{lesson.get('level', '')} · {t('lab_minutes', n=lesson.get('minutes', ''))}",
                size=11,
                color=c["text_secondary"],
            ),
        ]
        if note:
            items.append(ft.Text(note, size=11, color=c["warning"]))
        items.append(
            ft.Markdown(
                lesson.get("markdown", ""),
                selectable=True,
                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
            )
        )
        takeaways = lesson.get("key_takeaways") or []
        if takeaways:
            items.append(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                t("learn_takeaways"),
                                weight=ft.FontWeight.BOLD,
                                color=c["text_primary"],
                            ),
                            ft.Markdown(
                                "\n".join(f"- {k}" for k in takeaways),
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            ),
                        ],
                        spacing=4,
                    ),
                    padding=12,
                    border_radius=12,
                    bgcolor=c["surface_variant"],
                )
            )

        related: List[ft.Control] = []
        for lab in lesson.get("related_labs") or []:
            related.append(
                ft.OutlinedButton(
                    _loc(lab.get("title")),
                    icon=ft.Icons.SCIENCE,
                    on_click=lambda e, lab_id=lab["id"]: go(f"labs:{lab_id}"),
                    data=f"lab:{lab['id']}",
                )
            )
        for screen in lesson.get("related_screens") or []:
            if screen in SCREEN_KEYS:
                related.append(
                    ft.OutlinedButton(
                        t(SCREEN_KEYS[screen]),
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda e, screen=screen: go(screen),
                        data=f"screen:{screen}",
                    )
                )
        if related:
            items.append(
                ft.Text(t("learn_related"), weight=ft.FontWeight.BOLD, color=c["text_primary"])
            )
            items.append(ft.Row(related, wrap=True, spacing=8, run_spacing=8))

        quiz_box = ft.Column(spacing=10)
        if lesson.get("quiz"):
            quiz_id = lesson["quiz"]
            best = data["best"].get(quiz_id)
            quiz_btn = ft.Button(
                t("learn_quiz_btn")
                + (f" · {t('learn_best', p=f'{best:.0f}')}" if best is not None else ""),
                icon=ft.Icons.QUIZ,
                style=ft.ButtonStyle(
                    bgcolor=c["primary"],
                    color="#FFFFFF",
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                on_click=lambda e: page.run_task(load_quiz, quiz_id, quiz_box),
                data="quiz",
            )
            items.append(quiz_btn)
        items.append(quiz_box)
        items.append(ft.Container(height=24))
        body.controls = items
        return body

    # ---- the lesson's quiz ---------------------------------------------------
    async def load_quiz(quiz_id: str, box: ft.Column) -> None:
        box.controls = [ft.ProgressRing()]
        page.update()
        quiz = await api_client.learn_quiz(quiz_id)
        if quiz is None:
            box.controls = [
                ft.Text(t("test_err", reason=_reason()), color=c["error"], selectable=True)
            ]
            page.update()
            return
        groups: Dict[str, ft.RadioGroup] = {}
        feedback: Dict[str, ft.Text] = {}
        controls: List[ft.Control] = []
        note = api_client.cache_note(f"quiz:{quiz_id}")
        if note:
            controls.append(ft.Text(note, size=11, color=c["warning"]))
        for i, q in enumerate(quiz.get("questions") or [], start=1):
            group = ft.RadioGroup(content=ft.Column(spacing=0), data=q["id"])

            def pick(e, group=group) -> None:
                group.value = e.control.data
                group.update()

            # Radio labels do not wrap; long options sit in a Text that does.
            group.content.controls = [
                ft.Row(
                    [
                        ft.Radio(value=str(j)),
                        ft.Container(
                            ft.Text(ch, size=13, color=c["text_primary"]),
                            expand=True,
                            data=str(j),
                            on_click=pick,
                        ),
                    ],
                    spacing=0,
                )
                for j, ch in enumerate(q.get("choices") or [])
            ]
            fb = ft.Text("", size=12, visible=False)
            groups[q["id"]], feedback[q["id"]] = group, fb
            controls.append(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                f"{i}. {q['prompt']}",
                                size=13,
                                weight=ft.FontWeight.BOLD,
                                color=c["text_primary"],
                            ),
                            group,
                            fb,
                        ],
                        spacing=6,
                    ),
                    padding=12,
                    border_radius=14,
                    bgcolor=c["surface"],
                    border=ft.Border.all(1, c["card_border"]),
                )
            )
        summary = ft.Text("", size=14, weight=ft.FontWeight.BOLD, visible=False)

        async def submit(e=None) -> None:
            if any(g.value in (None, "") for g in groups.values()):
                summary.value, summary.color, summary.visible = (
                    t("learn_pick_all"),
                    c["warning"],
                    True,
                )
                page.update()
                return
            answers = {qid: int(g.value) for qid, g in groups.items()}
            res = await api_client.learn_grade(quiz_id, answers)
            summary.visible = True
            if res is None:
                summary.value, summary.color = t("test_grade_err", reason=_reason()), c["error"]
                page.update()
                return
            for d in res.get("details") or []:
                fb = feedback.get(d["id"])
                if fb is not None:
                    fb.visible = True
                    fb.value = f"{t('test_correct') if d['correct'] else t('test_wrong')}. {d.get('explain', '')}"
                    fb.color = c["success"] if d["correct"] else c["error"]
            pct = float(res.get("percent") or 0)
            await record_best(quiz_id, pct)
            text = t("test_score", score=res["score"], total=res["total"], percent=int(round(pct)))
            passed = pct >= PASS_PERCENT
            summary.value = (
                f"{text} · {t('learn_passed') if passed else t('learn_failed', p=PASS_PERCENT)}"
            )
            summary.color = c["success"] if passed else c["warning"]
            page.update()

        controls += [
            summary,
            ft.Button(
                t("learn_quiz_submit"),
                icon=ft.Icons.CHECK,
                style=ft.ButtonStyle(
                    bgcolor=c["primary"],
                    color="#FFFFFF",
                    shape=ft.RoundedRectangleBorder(radius=12),
                ),
                on_click=submit,
                data="quiz_submit",
            ),
        ]
        box.controls = controls
        page.update()

    # ---- entry -------------------------------------------------------------------
    async def ensure_loaded() -> None:
        if data["lessons"] is None and data["open"] is None:
            await load_list()

    render_list()
    root.controls = [list_view]
    view = ft.Container(content=root, expand=True)
    view.data = ensure_loaded
    return view
