"""
The 12 education labs in the mobile app.

The same labs as the website (dashboard/views/labs.py), served by the API
(api/labs.py): the list, each lab's theory, a run with its parameters
(computed on the server by src/education/labs/runner.py) and the final test,
graded on the server. Lab 12 is the 3D inverter model: the page from
static/lab3d/ in a WebView, which reports its events through console
messages ("LAB3D {json}").

The screen used to be one microgrid simulation; the other eleven labs and
every test existed only on the website.
"""

import asyncio
import json
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
    data: Dict[str, Any] = {"labs": None, "passed": set(), "loading": False, "open": None}

    def register_back(handler: Optional[Callable[[], bool]]) -> None:
        if set_back_handler:
            set_back_handler(handler)

    # ---- progress (which tests were passed), kept on the phone ------------
    async def load_passed() -> None:
        if prefs is None:
            return
        try:
            raw = await asyncio.wait_for(prefs.get(PREF_PASSED), timeout=3)
            data["passed"] = set(json.loads(raw)) if raw else set()
        except Exception as err:
            print(f"Lab progress not loaded: {err}")

    async def mark_passed(lab_id: str) -> None:
        data["passed"].add(lab_id)
        if prefs is not None:
            try:
                await prefs.set(PREF_PASSED, json.dumps(sorted(data["passed"])))
            except Exception as err:
                print(f"Lab progress not saved: {err}")

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
            status.value = ""
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
                        ],
                        spacing=4,
                    ),
                    ft.Text(_loc(detail.get("objectives")), size=11, color=c["text_secondary"]),
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

                def fmt(v: float, is_int=is_int) -> str:
                    return f"{int(round(v))}" if is_int else f"{v:.2f}".rstrip("0").rstrip(".")

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
        results = ft.Column(spacing=10)
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
            res = await api_client.lab_run(lab_id, dict(values))
            ring.visible = False
            if res is None:
                msg.value, msg.color = t("lab_err_run", reason=_reason()), c["error"]
                results.controls = []
            else:
                msg.value = ""
                render_result(res)
            page.update()

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
                await mark_passed(lab_id)
            else:
                summary.value, summary.color = (
                    f"{text} · {t('test_failed', p=int(res.get('pass_percent', 70)))}",
                    c["warning"],
                )
            page.update()

        panel.controls = [ft.ProgressRing()]
        page.run_task(load)
        return panel

    # ---- lab 12: the 3D model ------------------------------------------------
    def build_3d_panel(detail: Dict[str, Any]) -> ft.Control:
        url = api_client.lab_viewer_url(detail["viewer_path"])
        note = ft.Text("", size=12, color=c["text_secondary"])

        async def open_in_browser(e=None) -> None:
            launcher = next((s for s in page.services if isinstance(s, ft.UrlLauncher)), None)
            if launcher is None:
                launcher = ft.UrlLauncher()
                page.services.append(launcher)
                page.update()
            await launcher.launch_url(url)

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
                if msg.get("passed"):
                    await mark_passed(detail["id"])
                page.update()
            elif msg.get("type") == "check":
                note.value = t("lab3d_checked", score=msg.get("score"), total=msg.get("total"))
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
