"""
The 12 education labs in the mobile app.

The same labs as the website (dashboard/views/labs.py), served by the API
(api/labs.py): the list, each lab's theory, a run with its parameters
(computed on the server by src/education/labs/runner.py), the practice tasks
checked one by one, and the final test, graded on the server. Lab 12 is the 3D inverter model: the page from
static/lab3d/ in a WebView, which reports its events through console
messages ("LAB3D {json}").

The screen used to be one microgrid simulation; the other eleven labs and
every test existed only on the website.
"""

import asyncio
import json
import math
from typing import Any, Callable, Dict, List, Optional

import flet as ft

try:
    from mobile import api_client as api_client_module
    from mobile.api_client import api_client
    from mobile.components.line_chart import build_line_chart
    from mobile.state import state
except (ImportError, ModuleNotFoundError):
    import api_client as api_client_module  # type: ignore # pyright: ignore[reportMissingImports]
    from api_client import api_client  # type: ignore # pyright: ignore[reportMissingImports]
    from components.line_chart import (
        build_line_chart,  # type: ignore # pyright: ignore[reportMissingImports]
    )
    from state import state  # type: ignore # pyright: ignore[reportMissingImports]

PREF_PASSED = "ecopredict.labs_passed"
PREF_TASKS = "ecopredict.labs_tasks_done"  # {lab_id: [task ids solved]}
PREF_BEST = "ecopredict.labs_best"  # {lab_id: best test percent}
PREF_STUDENT = "ecopredict.student"  # {"name": ..., "group": ...}
WEBVIEW_PLATFORMS = {ft.PagePlatform.ANDROID, ft.PagePlatform.IOS, ft.PagePlatform.MACOS}


def _loc(field: Any) -> str:
    if isinstance(field, dict):
        return str(field.get(state.lang) or field.get("en") or "")
    return str(field or "")


def _reason() -> str:
    return getattr(api_client_module, "last_http_error", "") or state.text("reason_unknown")


def webview_supported(page: ft.Page) -> bool:
    """
    The WebView extension is compiled into the Android/iOS (and macOS) builds.
    The prebuilt web and desktop preview clients lack it and would draw
    "Unknown control: WebView"; they get a link to the page instead.
    """
    return not page.web and page.platform in WEBVIEW_PLATFORMS


def _fmt_metric(m: Dict[str, Any]) -> str:
    if m.get("value") is None:
        return "—"
    value = f"{m['value']:,.{int(m.get('digits', 1))}f}".replace(",", " ")
    return f"{value} {m.get('unit', '')}".strip()


def build_labs_view(
    page: ft.Page,
    set_back_handler: Optional[Callable[[Optional[Callable[[], bool]]], None]] = None,
    prefs: Optional[Any] = None,
) -> ft.Control:
    c = state.colors
    t = state.text
    root = ft.Column(expand=True, spacing=0)
    data: Dict[str, Any] = {
        "labs": None,
        "passed": set(),
        "tasks_done": {},
        "best": {},  # lab_id -> best test percent
        "student": {"name": "", "group": ""},
        # this session only, for the report: what the server should rebuild
        "last_params": {},
        "last_answers": {},
        "check3d": {},
        "loading": False,
        "open": None,
    }

    def register_back(handler: Optional[Callable[[], bool]]) -> None:
        if set_back_handler:
            set_back_handler(handler)

    # ---- progress (tests passed, tasks solved), kept on the phone -----------
    async def load_passed() -> None:
        if prefs is None:
            return
        try:
            raw = await asyncio.wait_for(prefs.get(PREF_PASSED), timeout=3)
            data["passed"] = set(json.loads(raw)) if raw else set()
            raw = await asyncio.wait_for(prefs.get(PREF_TASKS), timeout=3)
            done = json.loads(raw) if raw else {}
            data["tasks_done"] = {k: set(v) for k, v in done.items() if isinstance(v, list)}
            raw = await asyncio.wait_for(prefs.get(PREF_BEST), timeout=3)
            best = json.loads(raw) if raw else {}
            data["best"] = {k: float(v) for k, v in best.items() if isinstance(v, (int, float))}
            raw = await asyncio.wait_for(prefs.get(PREF_STUDENT), timeout=3)
            student = json.loads(raw) if raw else {}
            if isinstance(student, dict):
                data["student"] = {
                    "name": str(student.get("name") or ""),
                    "group": str(student.get("group") or ""),
                }
        except Exception as err:
            print(f"Lab progress not loaded: {err}")

    async def save_pref(key: str, value: Any) -> None:
        if prefs is None:
            return
        try:
            await prefs.set(key, json.dumps(value, ensure_ascii=False))
        except Exception as err:
            print(f"{key} not saved: {err}")

    async def record_test(lab_id: str, percent: Any, passed: bool) -> None:
        pct = float(percent or 0)
        if pct > data["best"].get(lab_id, -1):
            data["best"][lab_id] = pct
            await save_pref(PREF_BEST, data["best"])
        if passed:
            await mark_passed(lab_id)

    async def mark_passed(lab_id: str) -> None:
        data["passed"].add(lab_id)
        if prefs is not None:
            try:
                await prefs.set(PREF_PASSED, json.dumps(sorted(data["passed"])))
            except Exception as err:
                print(f"Lab progress not saved: {err}")

    async def mark_task_done(lab_id: str, task_id: str) -> None:
        data["tasks_done"].setdefault(lab_id, set()).add(task_id)
        if prefs is not None:
            try:
                await prefs.set(
                    PREF_TASKS, json.dumps({k: sorted(v) for k, v in data["tasks_done"].items()})
                )
            except Exception as err:
                print(f"Task progress not saved: {err}")

    def service(cls):
        """The page's instance of a Flet service (UrlLauncher, Share), added on first use."""
        found = next((s for s in page.services if isinstance(s, cls)), None)
        if found is None:
            found = cls()
            page.services.append(found)
            page.update()
        return found

    # ---- list of labs --------------------------------------------------------
    list_column = ft.ListView(spacing=10, padding=12, expand=True)
    status = ft.Text("", size=12, color=c["text_secondary"])

    def lab_card(index: int, lab: Dict[str, Any]) -> ft.Control:
        badges = [
            ft.Text(t("lab_minutes", n=lab.get("minutes", "")), size=11, color=c["text_secondary"]),
            ft.Text(_loc(lab.get("level")), size=11, color=c["text_secondary"]),
        ]
        if lab.get("has_3d"):
            badges.append(
                ft.Container(
                    ft.Text("3D", size=10, weight=ft.FontWeight.BOLD, color="#FFFFFF"),
                    bgcolor=c["primary"],
                    border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=1),
                )
            )
        total = int(lab.get("task_count") or 0)
        if total:
            done = len(data["tasks_done"].get(lab["id"], ()))
            badges.append(
                ft.Text(
                    t("lab_tasks_badge", done=done, total=total),
                    size=11,
                    color=c["success"] if done >= total else c["text_secondary"],
                )
            )
        if lab["id"] in data["passed"]:
            badges.append(ft.Text(t("lab_passed"), size=11, color=c["success"]))
        return ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        ft.Text(str(index), weight=ft.FontWeight.BOLD, color=c["primary"]),
                        width=34,
                        height=34,
                        alignment=ft.Alignment.CENTER,
                        border_radius=17,
                        bgcolor=c["surface_variant"],
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                _loc(lab.get("title")),
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
            on_click=lambda e, lab=lab: page.run_task(open_lab, lab),
            data=lab["id"],
        )

    def render_list() -> None:
        list_column.controls = [
            ft.Text(t("labs_title"), size=16, weight=ft.FontWeight.BOLD, color=c["text_primary"]),
            ft.Text(t("labs_sub"), size=11, color=c["text_secondary"]),
            status,
        ]
        for i, lab in enumerate(data["labs"] or [], start=1):
            list_column.controls.append(lab_card(i, lab))

    def show_list() -> None:
        data["open"] = None
        register_back(None)
        render_list()
        root.controls = [list_column]
        page.update()

    async def load_list() -> None:
        if data["loading"]:
            return
        data["loading"] = True
        status.value, status.color = t("labs_loading"), c["text_secondary"]
        render_list()
        page.update()
        await load_passed()
        labs = await api_client.labs_list()
        data["loading"] = False
        if labs is None:
            status.value, status.color = t("labs_err", reason=_reason()), c["error"]
            render_list()
            list_column.controls.append(
                ft.Button(
                    t("labs_retry"),
                    icon=ft.Icons.REFRESH,
                    on_click=lambda e: page.run_task(load_list),
                )
            )
        else:
            data["labs"] = labs
            status.value, status.color = api_client.cache_note("labs"), c["warning"]
            render_list()
        page.update()

    # ---- one lab ---------------------------------------------------------------
    async def open_lab(lab: Dict[str, Any]) -> None:
        data["open"] = lab["id"]
        register_back(back_to_list)
        root.controls = [
            ft.Container(ft.ProgressRing(), alignment=ft.Alignment.CENTER, expand=True)
        ]
        page.update()
        detail = await api_client.lab_detail(lab["id"])
        if data["open"] != lab["id"]:
            return  # the user went back meanwhile
        if detail is None:
            root.controls = [
                ft.ListView(
                    [
                        ft.Text(
                            t("lab_err_run", reason=_reason()), color=c["error"], selectable=True
                        ),
                        ft.Button(
                            t("labs_retry"),
                            icon=ft.Icons.REFRESH,
                            on_click=lambda e: page.run_task(open_lab, lab),
                        ),
                    ],
                    padding=12,
                    expand=True,
                )
            ]
            page.update()
            return
        root.controls = [build_detail(detail)]
        page.update()

    def back_to_list() -> bool:
        if data["open"] is None:
            return False
        show_list()
        return True

    def build_detail(detail: Dict[str, Any]) -> ft.Control:
        lab_id = detail["id"]
        is_3d = bool(detail.get("viewer_path"))
        body = ft.Container(expand=True)
        values: Dict[str, Any] = {p["key"]: p["default"] for p in detail.get("params") or []}
        panels: Dict[str, ft.Control] = {}

        header = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.IconButton(
                                ft.Icons.ARROW_BACK,
                                on_click=lambda e: back_to_list(),
                                icon_color=c["text_primary"],
                                tooltip=t("labs_back"),
                            ),
                            ft.Text(
                                _loc(detail.get("title")),
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=c["text_primary"],
                                expand=True,
                            ),
                            ft.IconButton(
                                ft.Icons.DESCRIPTION_OUTLINED,
                                on_click=lambda e: open_report(detail),
                                icon_color=c["primary"],
                                tooltip=t("report_btn"),
                                data="report",
                            ),
                        ],
                        spacing=4,
                    ),
                    ft.Text(_loc(detail.get("objectives")), size=11, color=c["text_secondary"]),
                    ft.Text(
                        api_client.cache_note(f"lab:{lab_id}"),
                        size=11,
                        color=c["warning"],
                        visible=bool(api_client.cache_note(f"lab:{lab_id}")),
                    ),
                ],
                spacing=2,
            ),
            padding=ft.Padding.only(left=4, right=12, top=4, bottom=6),
        )

        def select(key: str) -> None:
            seg.selected = [key]
            body.content = panels[key]
            page.update()

        seg = ft.SegmentedButton(
            segments=[
                ft.Segment(value="theory", label=ft.Text(t("lab_tab_theory"))),
                ft.Segment(
                    value="lab", label=ft.Text(t("lab_tab_3d") if is_3d else t("lab_tab_lab"))
                ),
                ft.Segment(value="tasks", label=ft.Text(t("lab_tab_tasks"))),
                ft.Segment(value="test", label=ft.Text(t("lab_tab_test"))),
            ],
            selected=["lab"],
            show_selected_icon=False,
            on_change=lambda e: select((e.control.selected or ["lab"])[0]),
        )

        panels["theory"] = ft.ListView(
            [
                ft.Markdown(
                    _loc(detail.get("theory")),
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                )
            ],
            padding=12,
            expand=True,
        )
        if is_3d:
            panels["lab"] = build_3d_panel(detail)
            panels["test"] = build_3d_test_note()
        else:
            lab_panel, apply_and_run = build_run_panel(lab_id, detail, values)
            panels["lab"] = lab_panel

            def apply_from_test(params: Dict[str, Any]) -> None:
                select("lab")
                page.run_task(apply_and_run, params)

            panels["test"] = build_test_panel(lab_id, apply_from_test)
        panels["tasks"] = build_tasks_panel(lab_id, detail.get("tasks") or [])
        body.content = panels["lab"]
        return ft.Column(
            [
                header,
                ft.Container(
                    ft.Row([seg], scroll=ft.ScrollMode.AUTO),
                    padding=ft.Padding.symmetric(horizontal=12),
                ),
                body,
            ],
            expand=True,
            spacing=6,
        )

    # ---- lab tab: parameters, run, results -----------------------------------
    def build_run_panel(lab_id: str, detail: Dict[str, Any], values: Dict[str, Any]):
        inputs: Dict[str, Any] = {}
        controls: List[ft.Control] = []

        for p in detail.get("params") or []:
            key = p["key"]
            label = _loc(p.get("label")) + (f", {p['unit']}" if p.get("unit") else "")
            if p["kind"] == "select":
                dd = ft.Dropdown(
                    label=label,
                    value=str(p["default"]),
                    options=[
                        ft.DropdownOption(key=o["id"], text=_loc(o["label"])) for o in p["options"]
                    ],
                    dense=True,
                    expand=True,
                )

                def on_select(e, key=key):
                    values[key] = e.control.value

                dd.on_select = on_select
                inputs[key] = dd
                controls.append(ft.Row([dd]))
            else:
                lo, hi, step = float(p["min"]), float(p["max"]), float(p["step"])
                is_int = all(float(v).is_integer() for v in (lo, hi, step, p["default"]))
                shown = ft.Text("", size=12, weight=ft.FontWeight.BOLD, color=c["primary"])
                slider = ft.Slider(
                    min=lo,
                    max=hi,
                    value=float(p["default"]),
                    divisions=max(1, round((hi - lo) / step)),
                )

                # As many decimals as the slider step has (γ moves in 0.001s).
                decimals = 0 if is_int else max(0, -math.floor(math.log10(step)))

                def fmt(v: float, is_int=is_int, decimals=decimals) -> str:
                    return f"{int(round(v))}" if is_int else f"{v:.{decimals}f}"

                def on_change(e, key=key, shown=shown, fmt=fmt, is_int=is_int):
                    v = float(e.control.value)
                    values[key] = int(round(v)) if is_int else round(v, 4)
                    shown.value = fmt(v)
                    shown.update()

                slider.on_change = on_change
                shown.value = fmt(float(p["default"]))
                inputs[key] = (slider, shown, fmt, is_int)
                controls.append(
                    ft.Row([ft.Text(label, size=12, color=c["text_primary"], expand=True), shown])
                )
                controls.append(slider)

        msg = ft.Text("", size=12, color=c["text_secondary"], selectable=True)
        ring = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2)
        # Results appear under the parameters, below the fold on a phone: after a
        # run the panel scrolls to them, or the tap looks like it did nothing.
        results = ft.Column(spacing=10, key=ft.ScrollKey("lab-results"))
        run_btn = ft.Button(
            content=ft.Row([ft.Text(t("lab_run")), ring], tight=True, spacing=8),
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                bgcolor=c["primary"], color="#FFFFFF", shape=ft.RoundedRectangleBorder(radius=12)
            ),
        )

        def render_result(res: Dict[str, Any]) -> None:
            cards = []
            for m in res.get("metrics") or []:
                cards.append(
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(_loc(m.get("label")), size=11, color=c["text_secondary"]),
                                ft.Text(
                                    _fmt_metric(m),
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=c["text_primary"],
                                ),
                            ],
                            spacing=2,
                        ),
                        padding=10,
                        border_radius=12,
                        bgcolor=c["surface"],
                        border=ft.Border.all(1, c["card_border"]),
                        col={"xs": 6, "md": 4},
                    )
                )
            items: List[ft.Control] = [ft.ResponsiveRow(cards, spacing=8, run_spacing=8)]
            for note in res.get("notes") or []:
                items.append(ft.Text("⚠️ " + _loc(note), size=12, color=c["warning"]))
            for ch in res.get("charts") or []:
                items.append(build_line_chart(ch))
            results.controls = items

        async def run(e=None) -> None:
            ring.visible = True
            msg.value = ""
            page.update()
            params = dict(values)
            res = await api_client.lab_run(lab_id, params)
            ring.visible = False
            if res is None:
                msg.value, msg.color = t("lab_err_run", reason=_reason()), c["error"]
                results.controls = []
            else:
                msg.value = ""
                data["last_params"][lab_id] = params  # for the report
                render_result(res)
            page.update()
            if res is not None:
                await scroll_to_results()

        async def scroll_to_results() -> None:
            try:
                await asyncio.sleep(0.3)  # let the new results lay out first
                await panel.scroll_to(scroll_key="lab-results", duration=400)
            except Exception as err:  # not mounted (tests) or already unmounted
                print(f"scroll to results skipped: {err}")

        async def apply_and_run(params: Dict[str, Any]) -> None:
            for key, value in params.items():
                if key not in inputs:
                    continue
                values[key] = value
                widget = inputs[key]
                if isinstance(widget, ft.Dropdown):
                    widget.value = str(value)
                else:
                    slider, shown, fmt, is_int = widget
                    slider.value = float(value)
                    shown.value = fmt(float(value))
            msg.value, msg.color = t("lab_applied"), c["success"]
            page.update()
            await run()
            msg.value, msg.color = t("lab_applied"), c["success"]
            page.update()

        run_btn.on_click = run
        panel = ft.ListView(
            [
                ft.Container(
                    ft.Column(controls + [run_btn], spacing=4),
                    padding=12,
                    border_radius=14,
                    bgcolor=c["surface"],
                    border=ft.Border.all(1, c["card_border"]),
                ),
                msg,
                results,
                ft.Container(height=24),
            ],
            spacing=10,
            padding=12,
            expand=True,
        )
        results.controls = [ft.Text(t("lab_no_run"), size=12, color=c["text_secondary"])]
        return panel, apply_and_run

    # ---- test tab --------------------------------------------------------------
    def build_test_panel(lab_id: str, apply_params: Callable[[Dict[str, Any]], None]) -> ft.Control:
        panel = ft.ListView(spacing=10, padding=12, expand=True)
        state_: Dict[str, Any] = {"test": None, "fields": {}, "feedback": {}}

        def build_questions(test: Dict[str, Any]) -> None:
            state_["fields"], state_["feedback"] = {}, {}
            items: List[ft.Control] = [
                ft.Text(
                    t("test_intro", n=len(test["questions"]), p=int(test.get("pass_percent", 70))),
                    size=11,
                    color=c["text_secondary"],
                )
            ]
            for i, q in enumerate(test["questions"], start=1):
                mark = "▶ " if q["kind"] == "run" else ""
                col: List[ft.Control] = [
                    ft.Text(
                        f"{mark}{i}. {q['prompt']}",
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        color=c["text_primary"],
                    )
                ]
                if q["kind"] == "choice":
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
                        for j, ch in enumerate(q["choices"])
                    ]
                    state_["fields"][q["id"]] = group
                    col.append(group)
                else:
                    if q["kind"] == "run":
                        col.append(
                            ft.Text(
                                "\n".join(
                                    f"• {r['label']}: {r['value']}"
                                    for r in q.get("params_display") or []
                                ),
                                size=11,
                                color=c["text_secondary"],
                            )
                        )
                        col.append(
                            ft.TextButton(
                                t("test_apply"),
                                icon=ft.Icons.TUNE,
                                on_click=lambda e, params=q["params"]: apply_params(params),
                            )
                        )
                    unit = q.get("unit") or ""
                    field = ft.TextField(
                        label=t("test_answer") + (f" ({unit})" if unit else ""),
                        keyboard_type=ft.KeyboardType.NUMBER,
                        dense=True,
                        data=q["id"],
                    )
                    state_["fields"][q["id"]] = field
                    col.append(field)
                fb = ft.Text("", size=12, visible=False)
                state_["feedback"][q["id"]] = fb
                col.append(fb)
                items.append(
                    ft.Container(
                        ft.Column(col, spacing=6),
                        padding=12,
                        border_radius=14,
                        bgcolor=c["surface"],
                        border=ft.Border.all(1, c["card_border"]),
                    )
                )
            summary = ft.Text("", size=14, weight=ft.FontWeight.BOLD, visible=False)
            state_["summary"] = summary
            items.append(summary)
            items.append(
                ft.Button(
                    t("test_submit"),
                    icon=ft.Icons.CHECK,
                    style=ft.ButtonStyle(
                        bgcolor=c["primary"],
                        color="#FFFFFF",
                        shape=ft.RoundedRectangleBorder(radius=12),
                    ),
                    on_click=submit,
                )
            )
            items.append(ft.Container(height=24))
            panel.controls = items

        async def load() -> None:
            panel.controls = [ft.ProgressRing()]
            page.update()
            test = await api_client.lab_test(lab_id)
            if test is None:
                panel.controls = [
                    ft.Text(t("test_err", reason=_reason()), color=c["error"], selectable=True),
                    ft.Button(
                        t("labs_retry"),
                        icon=ft.Icons.REFRESH,
                        on_click=lambda e: page.run_task(load),
                    ),
                ]
            else:
                state_["test"] = test
                build_questions(test)
                note = api_client.cache_note(f"test:{lab_id}")
                if note:  # questions readable offline; grading needs the server
                    panel.controls.insert(0, ft.Text(note, size=11, color=c["warning"]))
            page.update()

        async def submit(e=None) -> None:
            answers: Dict[str, Any] = {}
            for qid, field in state_["fields"].items():
                v = field.value
                answers[qid] = (
                    (int(v) if v not in (None, "") else None)
                    if isinstance(field, ft.RadioGroup)
                    else (v or "")
                )
            res = await api_client.lab_grade(lab_id, answers)
            summary = state_["summary"]
            summary.visible = True
            if res is None:
                summary.value, summary.color = t("test_grade_err", reason=_reason()), c["error"]
                page.update()
                return
            data["last_answers"][lab_id] = answers  # for the report
            await record_test(lab_id, res.get("percent"), bool(res.get("passed")))
            for d in res.get("details") or []:
                fb = state_["feedback"].get(d["id"])
                if fb:
                    fb.visible = True
                    fb.value = f"{t('test_correct') if d['correct'] else t('test_wrong')}. {d.get('explain', '')}"
                    fb.color = c["success"] if d["correct"] else c["error"]
            text = t(
                "test_score",
                score=res["score"],
                total=res["total"],
                percent=int(round(res["percent"])),
            )
            if res.get("passed"):
                summary.value, summary.color = f"{text} · {t('test_passed')}", c["success"]
            else:
                summary.value, summary.color = (
                    f"{text} · {t('test_failed', p=int(res.get('pass_percent', 70)))}",
                    c["warning"],
                )
            page.update()

        panel.controls = [ft.ProgressRing()]
        page.run_task(load)
        return panel

    # ---- practice tasks: checked one by one on the server, as on the website ---
    def build_tasks_panel(lab_id: str, tasks: List[Dict[str, Any]]) -> ft.Control:
        panel = ft.ListView(spacing=10, padding=12, expand=True)
        if not tasks:
            panel.controls = [ft.Text(t("tasks_none"), size=12, color=c["text_secondary"])]
            return panel
        progress = ft.Text("", size=12, weight=ft.FontWeight.BOLD)

        def refresh_progress() -> None:
            done = len(data["tasks_done"].get(lab_id, ()))
            if done >= len(tasks):
                progress.value, progress.color = t("tasks_all_done"), c["success"]
            else:
                progress.value = t("tasks_progress", done=done, total=len(tasks))
                progress.color = c["text_secondary"]

        def md(text: str) -> ft.Markdown:
            return ft.Markdown(text, extension_set=ft.MarkdownExtensionSet.GITHUB_WEB)

        def task_card(i: int, task: Dict[str, Any]) -> ft.Control:
            tid, is_choice = task["id"], task["kind"] == "choice"
            done_mark = ft.Text(
                t("task_done"),
                size=11,
                color=c["success"],
                visible=tid in data["tasks_done"].get(lab_id, set()),
            )
            feedback = ft.Text("", size=12, visible=False, selectable=True)
            box = dict(padding=10, border_radius=10, bgcolor=c["surface_variant"])
            hint = ft.Container(md(_loc(task.get("hint"))), visible=False, **box)
            explain = ft.Container(visible=False, **box)
            ring = ft.ProgressRing(visible=False, width=16, height=16, stroke_width=2)

            if is_choice:
                answer: ft.Control = ft.RadioGroup(content=ft.Column(spacing=0), data=tid)

                def pick(e, group=answer) -> None:
                    group.value = e.control.data
                    group.update()

                answer.content.controls = [
                    ft.Row(
                        [
                            ft.Radio(value=str(j)),
                            ft.Container(
                                ft.Text(_loc(ch), size=13, color=c["text_primary"]),
                                expand=True,
                                data=str(j),
                                on_click=pick,
                            ),
                        ],
                        spacing=0,
                    )
                    for j, ch in enumerate(task.get("choices") or [])
                ]
            else:
                unit = task.get("unit") or ""
                answer = ft.TextField(
                    label=t("test_answer") + (f" ({unit})" if unit else ""),
                    keyboard_type=ft.KeyboardType.NUMBER,
                    dense=True,
                    data=tid,
                )

            def show(text: str, color: str) -> None:
                feedback.value, feedback.color, feedback.visible = text, color, True
                page.update()

            async def check(e=None) -> None:
                number, choice = None, None
                if is_choice:
                    if answer.value in (None, ""):
                        show(t("task_pick"), c["warning"])
                        return
                    choice = int(answer.value)
                else:
                    try:
                        number = float(str(answer.value or "").replace(",", ".").strip())
                    except ValueError:
                        show(t("task_enter_number"), c["warning"])
                        return
                ring.visible = True
                page.update()
                res = await api_client.lab_task_check(
                    lab_id, tid, number=number, choice_index=choice
                )
                ring.visible = False
                if res is None:
                    show(t("task_err", reason=_reason()), c["error"])
                    return
                lang = state.lang
                message = res.get(f"message_{lang}") or res.get("message_en") or ""
                if res.get("ok"):
                    explain.content = md(res.get(f"explain_{lang}") or "")
                    explain.visible, hint.visible, done_mark.visible = True, False, True
                    await mark_task_done(lab_id, tid)
                    refresh_progress()
                    show(message, c["success"])
                else:
                    # A wrong answer opens the hint; the solution stays hidden.
                    explain.visible, hint.visible = False, True
                    show(message, c["error"])

            def toggle_hint(e=None) -> None:
                hint.visible = not hint.visible
                page.update()

            return ft.Container(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    f"{i}.", weight=ft.FontWeight.BOLD, color=c["text_primary"]
                                ),
                                done_mark,
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        md(_loc(task.get("prompt"))),
                        answer,
                        ft.Row(
                            [
                                ft.Button(
                                    t("task_check"),
                                    icon=ft.Icons.CHECK,
                                    on_click=check,
                                    data=f"check:{tid}",
                                ),
                                ft.TextButton(
                                    t("task_hint"),
                                    icon=ft.Icons.LIGHTBULB_OUTLINE,
                                    on_click=toggle_hint,
                                ),
                                ring,
                            ],
                            spacing=6,
                            wrap=True,
                        ),
                        feedback,
                        hint,
                        explain,
                    ],
                    spacing=6,
                ),
                padding=12,
                border_radius=14,
                bgcolor=c["surface"],
                border=ft.Border.all(1, c["card_border"]),
            )

        refresh_progress()
        panel.controls = [
            ft.Text(t("tasks_intro"), size=11, color=c["text_secondary"]),
            progress,
            *[task_card(i, task) for i, task in enumerate(tasks, start=1)],
            ft.Container(height=24),
        ]
        return panel

    # ---- the student's report (built on the server) ---------------------------
    def open_report(detail: Dict[str, Any]) -> None:
        lab_id = detail["id"]
        name = ft.TextField(label=t("report_name"), value=data["student"]["name"], dense=True)
        group = ft.TextField(label=t("report_group"), value=data["student"]["group"], dense=True)
        status_text = ft.Text("", size=12, selectable=True)
        best = data["best"].get(lab_id)
        tasks_total = len(detail.get("tasks") or [])
        tasks_done = len(
            [x for x in data["tasks_done"].get(lab_id, ()) if not x.startswith("scenario_")]
        )
        summary = []
        if not detail.get("viewer_path"):
            has_run = lab_id in data["last_params"]
            summary.append(t("report_has_run", v=t("report_yes") if has_run else t("report_no")))
        summary.append(
            t("report_has_test", v=f"{best:.0f} %" if best is not None else t("report_no"))
        )
        summary.append(t("report_has_tasks", done=min(tasks_done, tasks_total), total=tasks_total))

        async def make() -> Optional[Dict[str, Any]]:
            data["student"] = {
                "name": (name.value or "").strip(),
                "group": (group.value or "").strip(),
            }
            await save_pref(PREF_STUDENT, data["student"])
            status_text.value, status_text.color = t("report_making"), c["text_secondary"]
            page.update()
            res = await api_client.lab_report(
                lab_id,
                {
                    "student": data["student"]["name"],
                    "group": data["student"]["group"],
                    "lang": state.lang,
                    "params": data["last_params"].get(lab_id),
                    "answers": data["last_answers"].get(lab_id),
                    "tasks_done": sorted(data["tasks_done"].get(lab_id, ())),
                    "best_test_percent": best,
                    "last_3d_check": data["check3d"].get(lab_id),
                },
            )
            if res is None:
                status_text.value, status_text.color = t("report_err", reason=_reason()), c["error"]
            else:
                status_text.value = t("report_shared", name=res.get("filename", ""))
                status_text.color = c["success"]
            page.update()
            return res

        async def share(e=None) -> None:
            res = await make()
            if res is None:
                return
            try:
                await service(ft.Share).share_files(
                    [
                        ft.ShareFile.from_bytes(
                            res["html"].encode("utf-8"),
                            mime_type="text/html",
                            name=res["filename"],
                        )
                    ],
                    subject=t("report_title") + " · " + _loc(detail.get("title")),
                )
            except Exception as err:  # no share sheet (web/desktop preview): open it instead
                print(f"share failed, opening the report instead: {err}")
                await service(ft.UrlLauncher).launch_url(state.api_base_url + res["url"])

        async def open_in_browser(e=None) -> None:
            res = await make()
            if res is not None:
                await service(ft.UrlLauncher).launch_url(state.api_base_url + res["url"])

        dialog = ft.AlertDialog(
            title=ft.Text(t("report_title")),
            content=ft.Column(
                [
                    ft.Text(t("report_intro"), size=12, color=c["text_secondary"]),
                    name,
                    group,
                    ft.Text("\n".join(summary), size=12, color=c["text_primary"]),
                    status_text,
                ],
                tight=True,
                spacing=8,
            ),
            actions=[
                ft.TextButton(t("report_close"), on_click=lambda e: page.pop_dialog()),
                ft.TextButton(
                    t("report_open"), icon=ft.Icons.OPEN_IN_BROWSER, on_click=open_in_browser
                ),
                ft.Button(t("report_share"), icon=ft.Icons.SHARE, on_click=share, data="share"),
            ],
            data="report_dialog",
        )
        page.show_dialog(dialog)

    # ---- lab 12: the 3D model ------------------------------------------------
    def build_3d_panel(detail: Dict[str, Any]) -> ft.Control:
        url = api_client.lab_viewer_url(detail["viewer_path"])
        note = ft.Text("", size=12, color=c["text_secondary"])

        async def open_in_browser(e=None) -> None:
            await service(ft.UrlLauncher).launch_url(url)

        open_btn = ft.TextButton(
            t("lab3d_open_browser"), icon=ft.Icons.OPEN_IN_BROWSER, on_click=open_in_browser
        )
        if not webview_supported(page):
            return ft.ListView(
                [ft.Text(t("lab3d_unsupported"), size=13, color=c["text_primary"]), open_btn],
                padding=12,
                expand=True,
            )

        import flet_webview as fwv  # compiled into the mobile build only

        async def on_console(e) -> None:
            text = str(getattr(e, "message", "") or "")
            if not text.startswith("LAB3D "):
                return
            print(text[:300])  # the emulator test reads these from logcat
            try:
                msg = json.loads(text[6:])
            except ValueError:
                return
            if msg.get("type") == "test_result":
                data["last3d"] = msg
                note.value = t(
                    "lab3d_last_result",
                    score=msg.get("score"),
                    total=msg.get("total"),
                    percent=int(round(float(msg.get("percent") or 0))),
                )
                await record_test(detail["id"], msg.get("percent"), bool(msg.get("passed")))
                page.update()
            elif msg.get("type") == "check":
                note.value = t("lab3d_checked", score=msg.get("score"), total=msg.get("total"))
                data["check3d"][detail["id"]] = msg
                if msg.get("ok") and msg.get("scenario"):
                    await mark_task_done(detail["id"], f"scenario_{msg['scenario']}")
                page.update()

        viewer = fwv.WebView(url=url, expand=True, bgcolor="#0B1220", on_console_message=on_console)
        return ft.Column(
            [
                ft.Container(
                    ft.Text(t("lab3d_hint"), size=11, color=c["text_secondary"]),
                    padding=ft.Padding.symmetric(horizontal=12),
                ),
                ft.Container(viewer, expand=True),
                ft.Container(
                    ft.Row(
                        [note, open_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True
                    ),
                    padding=ft.Padding.symmetric(horizontal=12),
                ),
            ],
            expand=True,
            spacing=4,
        )

    def build_3d_test_note() -> ft.Control:
        items: List[ft.Control] = [ft.Text(t("lab3d_test_note"), size=13, color=c["text_primary"])]
        last = data.get("last3d")
        if last:
            items.append(
                ft.Text(
                    t(
                        "lab3d_last_result",
                        score=last.get("score"),
                        total=last.get("total"),
                        percent=int(round(float(last.get("percent") or 0))),
                    ),
                    color=c["success"] if last.get("passed") else c["warning"],
                )
            )
        return ft.ListView(items, padding=12, expand=True)

    # ---- start -------------------------------------------------------------
    async def ensure_loaded() -> None:
        if data["labs"] is None and data["open"] is None:
            await load_list()

    render_list()
    root.controls = [list_column]
    view = ft.Container(content=root, expand=True)
    view.data = ensure_loaded
    return view
