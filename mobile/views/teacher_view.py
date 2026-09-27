"""
Teacher: create a class, give its code to the students, follow their results.

The classes and their teacher keys are kept on this phone; the results come
from the server (api/classroom.py), which recorded them when it graded the
students' lab tests, practice tasks and lesson quizzes. A class can also be
added from another device with its code and key, shared as CSV, or opened
on a computer (static/classroom/).
"""

import asyncio
import csv
import io
import json
import time
import urllib.parse
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

PREF_CLASSES = "ecopredict.teacher_classes"  # [{code, name, key}]


def _loc(field: Any) -> str:
    if isinstance(field, dict):
        return str(field.get(state.lang) or field.get("en") or "")
    return str(field or "")


def _reason() -> str:
    return getattr(api_client_module, "last_http_error", "") or state.text("reason_unknown")


def results_csv(res: Dict[str, Any]) -> str:
    """One row per student: summary, then each lab's best test % and tasks solved."""
    labs = res.get("labs") or []
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(
        ["student", "labs_passed", "test_avg", "tasks_done", "last_seen"]
        + [f"{i}. test %" for i in range(1, len(labs) + 1)]
        + [f"{i}. tasks" for i in range(1, len(labs) + 1)]
    )
    for st in res.get("students") or []:
        per = st.get("labs") or {}
        w.writerow(
            [
                st["name"],
                st.get("labs_passed", 0),
                "" if st.get("test_avg") is None else st["test_avg"],
                st.get("tasks_done", 0),
                time.strftime("%Y-%m-%d %H:%M", time.localtime(st.get("last_seen") or 0)),
            ]
            + [
                "" if per.get(lab["id"], {}).get("test") is None else per[lab["id"]]["test"]
                for lab in labs
            ]
            + [len(per.get(lab["id"], {}).get("tasks") or []) for lab in labs]
        )
    return out.getvalue()


def build_teacher_view(
    page: ft.Page,
    set_back_handler: Optional[Callable[[Optional[Callable[[], bool]]], None]] = None,
    prefs: Optional[Any] = None,
) -> ft.Control:
    c = state.colors
    t = state.text
    root = ft.Column(expand=True, spacing=0)
    data: Dict[str, Any] = {"classes": [], "loaded": False, "open": None}

    def register_back(handler: Optional[Callable[[], bool]]) -> None:
        if set_back_handler:
            set_back_handler(handler)

    def service(cls):
        found = next((s for s in page.services if isinstance(s, cls)), None)
        if found is None:
            found = cls()
            page.services.append(found)
            page.update()
        return found

    async def load_classes() -> None:
        if prefs is None:
            return
        try:
            raw = await asyncio.wait_for(prefs.get(PREF_CLASSES), timeout=3)
            got = json.loads(raw) if raw else []
            data["classes"] = [
                x for x in got if isinstance(x, dict) and x.get("code") and x.get("key")
            ]
        except Exception as err:
            print(f"Classes not loaded: {err}")

    async def save_classes() -> None:
        if prefs is None:
            return
        try:
            await prefs.set(PREF_CLASSES, json.dumps(data["classes"], ensure_ascii=False))
        except Exception as err:
            print(f"Classes not saved: {err}")

    def remember(code: str, name: str, key: str) -> None:
        data["classes"] = [x for x in data["classes"] if x["code"] != code]
        data["classes"].insert(0, {"code": code, "name": name, "key": key})

    # ---- the list of my classes --------------------------------------------------
    list_view = ft.ListView(spacing=10, padding=12, expand=True)
    msg = ft.Text("", size=12, selectable=True)
    new_name = ft.TextField(
        label=t("teacher_class_name"),
        hint_text=t("teacher_class_hint"),
        dense=True,
        max_length=60,
        expand=True,
    )
    add_code = ft.TextField(
        label=t("class_code"),
        dense=True,
        capitalization=ft.TextCapitalization.CHARACTERS,
        width=150,
    )
    add_key = ft.TextField(
        label=t("teacher_key"), dense=True, password=True, can_reveal_password=True, expand=True
    )

    async def create(e=None) -> None:
        name = (new_name.value or "").strip()
        if not name:
            return
        res = await api_client.classroom_create(name)
        if res is None:
            msg.value, msg.color = t("teacher_err", reason=_reason()), c["error"]
            page.update()
            return
        remember(res["code"], res["name"], res["teacher_key"])
        await save_classes()
        new_name.value = ""
        msg.value = ""
        render_list()
        show_created(res)
        page.update()

    async def add_existing(e=None) -> None:
        code, key = (add_code.value or "").strip().upper(), (add_key.value or "").strip()
        if not code or not key:
            return
        res = await api_client.classroom_results(code, key)
        if res is None:
            msg.value, msg.color = t("teacher_err", reason=_reason()), c["error"]
            page.update()
            return
        remember(res["code"], res["name"], key)
        await save_classes()
        add_code.value = add_key.value = ""
        msg.value = ""
        render_list()
        page.update()

    async def share_code(cls: Dict[str, Any]) -> None:
        text = t("teacher_share_text", cls=cls["name"], code=cls["code"])
        try:
            await service(ft.Share).share_text(text, subject=cls["name"])
        except Exception as err:  # no share sheet in a preview
            print(f"share failed: {err}")
            msg.value, msg.color = text, c["text_primary"]
            page.update()

    def show_created(res: Dict[str, Any]) -> None:
        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(t("teacher_created") + f": {res['name']}"),
                content=ft.Column(
                    [
                        ft.Text(
                            res["code"],
                            size=34,
                            weight=ft.FontWeight.BOLD,
                            color=c["primary"],
                            selectable=True,
                        ),
                        ft.Text(t("teacher_code_note", code=res["code"]), size=12),
                        ft.Text(
                            t("teacher_key_note", secret=res["teacher_key"]),
                            size=12,
                            color=c["warning"],
                            selectable=True,
                        ),
                    ],
                    tight=True,
                    spacing=8,
                ),
                actions=[
                    ft.TextButton(t("report_close"), on_click=lambda e: page.pop_dialog()),
                    ft.Button(
                        t("teacher_share_code"),
                        icon=ft.Icons.SHARE,
                        on_click=lambda e: page.run_task(
                            share_code, {"code": res["code"], "name": res["name"]}
                        ),
                    ),
                ],
                data="created_dialog",
            )
        )

    def class_tile(cls: Dict[str, Any]) -> ft.Control:
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.GROUPS, color=c["primary"]),
                    ft.Column(
                        [
                            ft.Text(
                                cls["name"],
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=c["text_primary"],
                            ),
                            ft.Text(
                                t("class_code") + f": {cls['code']}",
                                size=11,
                                color=c["text_secondary"],
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        ft.Icons.SHARE,
                        icon_color=c["text_secondary"],
                        tooltip=t("teacher_share_code"),
                        on_click=lambda e, cls=cls: page.run_task(share_code, cls),
                    ),
                    ft.Icon(ft.Icons.CHEVRON_RIGHT, color=c["text_secondary"]),
                ],
                spacing=10,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
            on_click=lambda e, cls=cls: page.run_task(open_class, cls),
            data=f"class:{cls['code']}",
        )

    def section(title: str, controls: List[ft.Control]) -> ft.Control:
        return ft.Container(
            ft.Column(
                [ft.Text(title, weight=ft.FontWeight.BOLD, color=c["text_primary"]), *controls],
                spacing=8,
            ),
            padding=12,
            border_radius=14,
            bgcolor=c["surface"],
            border=ft.Border.all(1, c["card_border"]),
        )

    def render_list() -> None:
        list_view.controls = [
            ft.Text(
                t("teacher_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]
            ),
            ft.Text(t("teacher_intro"), size=11, color=c["text_secondary"]),
            msg,
            section(
                t("teacher_new"),
                [
                    ft.Row(
                        [
                            new_name,
                            ft.Button(
                                t("teacher_create"),
                                icon=ft.Icons.ADD,
                                on_click=create,
                                data="create",
                            ),
                        ]
                    )
                ],
            ),
            ft.Text(t("teacher_mine"), weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            *(
                [class_tile(x) for x in data["classes"]]
                or [ft.Text(t("teacher_none"), size=12, color=c["text_secondary"])]
            ),
            section(
                t("teacher_add"),
                [
                    ft.Row([add_code, add_key], spacing=8),
                    ft.Button(t("teacher_add_btn"), on_click=add_existing),
                ],
            ),
            ft.Container(height=24),
        ]

    def show_list() -> None:
        data["open"] = None
        register_back(None)
        render_list()
        root.controls = [list_view]
        page.update()

    # ---- one class ------------------------------------------------------------
    def back_to_list() -> bool:
        if data["open"] is None:
            return False
        show_list()
        return True

    async def open_class(cls: Dict[str, Any]) -> None:
        data["open"] = cls["code"]
        register_back(back_to_list)
        root.controls = [
            ft.Container(ft.ProgressRing(), alignment=ft.Alignment.CENTER, expand=True)
        ]
        page.update()
        res = await api_client.classroom_results(cls["code"], cls["key"])
        if data["open"] != cls["code"]:
            return
        root.controls = [build_class(cls, res)]
        page.update()

    def build_class(cls: Dict[str, Any], res: Optional[Dict[str, Any]]) -> ft.Control:
        body = ft.ListView(spacing=10, padding=12, expand=True)
        header = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.ARROW_BACK,
                    on_click=lambda e: back_to_list(),
                    icon_color=c["text_primary"],
                    tooltip=t("teacher_back"),
                ),
                ft.Text(
                    f"{cls['name']} · {cls['code']}",
                    size=15,
                    weight=ft.FontWeight.BOLD,
                    color=c["text_primary"],
                    expand=True,
                ),
                ft.IconButton(
                    ft.Icons.REFRESH,
                    tooltip=t("teacher_refresh"),
                    on_click=lambda e: page.run_task(open_class, cls),
                ),
            ],
            spacing=4,
        )
        if res is None:
            body.controls = [
                header,
                ft.Text(t("teacher_err", reason=_reason()), color=c["error"], selectable=True),
            ]
            return body
        students = res.get("students") or []
        labs = res.get("labs") or []

        async def share_csv(e=None) -> None:
            name = f"class_{cls['code']}.csv"
            try:
                await service(ft.Share).share_files(
                    [
                        ft.ShareFile.from_bytes(
                            results_csv(res).encode("utf-8-sig"), mime_type="text/csv", name=name
                        )
                    ],
                    subject=cls["name"],
                )
            except Exception as err:
                print(f"share failed: {err}")

        async def open_web(e=None) -> None:
            url = f"{state.api_base_url}/static/classroom/index.html#code={urllib.parse.quote(cls['code'])}"
            await service(ft.UrlLauncher).launch_url(url)

        def student_card(st: Dict[str, Any]) -> ft.Control:
            avg = "—" if st.get("test_avg") is None else f"{st['test_avg']:.0f}%"
            seen = time.strftime("%d.%m %H:%M", time.localtime(st.get("last_seen") or 0))
            return ft.Container(
                ft.Column(
                    [
                        ft.Text(
                            st["name"], size=14, weight=ft.FontWeight.BOLD, color=c["text_primary"]
                        ),
                        ft.Text(
                            t(
                                "teacher_row",
                                passed=st.get("labs_passed", 0),
                                avg=avg,
                                tasks=st.get("tasks_done", 0),
                                quizzes=len(st.get("quizzes") or {}),
                            ),
                            size=12,
                            color=c["text_secondary"],
                        ),
                        ft.Text(t("teacher_seen", when=seen), size=11, color=c["text_secondary"]),
                    ],
                    spacing=3,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(
                    1, c["success"] if st.get("labs_passed") else c["card_border"]
                ),
                on_click=lambda e, st=st: show_student(cls, st, labs),
                data=f"student:{st['id']}",
            )

        body.controls = [
            header,
            ft.Text(t("teacher_students", n=len(students)), size=12, color=c["text_secondary"]),
            ft.Row(
                [
                    ft.OutlinedButton(
                        t("teacher_csv"), icon=ft.Icons.TABLE_VIEW, on_click=share_csv
                    ),
                    ft.OutlinedButton(t("teacher_web"), icon=ft.Icons.COMPUTER, on_click=open_web),
                ],
                wrap=True,
                spacing=8,
            ),
            *(
                [student_card(st) for st in students]
                or [
                    ft.Text(
                        t("teacher_no_students", code=cls["code"]),
                        size=12,
                        color=c["text_secondary"],
                    )
                ]
            ),
            ft.Container(height=24),
        ]
        return body

    def show_student(cls: Dict[str, Any], st: Dict[str, Any], labs: List[Dict[str, Any]]) -> None:
        per = st.get("labs") or {}
        lines = []
        for i, lab in enumerate(labs, start=1):
            got = per.get(lab["id"]) or {}
            test = "—" if got.get("test") is None else f"{got['test']:.0f}%"
            lines.append(
                t(
                    "teacher_lab_line",
                    title=f"{i}. {_loc(lab['title'])}",
                    test=test,
                    passed=" ✅" if got.get("passed") else "",
                    tasks=len(got.get("tasks") or []),
                    total=lab.get("tasks", 0),
                )
            )

        async def remove(e=None) -> None:
            await api_client.classroom_remove(cls["code"], cls["key"], st["id"])
            page.pop_dialog()
            await open_class(cls)

        page.show_dialog(
            ft.AlertDialog(
                title=ft.Text(st["name"]),
                content=ft.Column(
                    [ft.Text(line, size=12) for line in lines],
                    tight=True,
                    spacing=4,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton(t("teacher_remove"), on_click=remove),
                    ft.TextButton(t("report_close"), on_click=lambda e: page.pop_dialog()),
                ],
            )
        )

    # ---- entry -------------------------------------------------------------------
    async def ensure_loaded() -> None:
        if not data["loaded"]:
            data["loaded"] = True
            await load_classes()
            if data["open"] is None:
                render_list()
                page.update()

    render_list()
    root.controls = [list_view]
    view = ft.Container(content=root, expand=True)
    view.data = ensure_loaded
    return view
