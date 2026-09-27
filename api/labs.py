"""
The 12 education labs over HTTP, for the mobile app.

The website renders the same labs in Streamlit from src/education/labs; the
phone gets them here: the list, a lab's parameters and theory, a simulation
run, the practice tasks and the final test. Formulas in the theory and the
tasks come as Flet Markdown ($…$ with a space after a closing $). The 3D
inverter lab itself is a static page (static/lab3d/, served under
/static/lab3d/) that calls the test routes below from inside the app's WebView.
"""

from __future__ import annotations

import secrets
import time
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from api.classroom import StudentRef, record

router = APIRouter()

VIEWER_PATH = "/static/lab3d/index.html"
LABS_WITH_3D = {"lab_inverter_wiring"}


def _lab_or_404(lab_id: str) -> dict[str, Any]:
    from src.education.labs.lab_registry import LABS

    lab = LABS.get(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail=f"Unknown lab: {lab_id}")
    return lab


def _md(field: Any) -> Any:
    """A {lang: text} field with its LaTeX made ready for Flet's Markdown."""
    from src.education.labs.theory import to_flet_markdown

    if isinstance(field, dict):
        return {lang: to_flet_markdown(str(text)) for lang, text in field.items()}
    return field


def _summary(lab: dict[str, Any]) -> dict[str, Any]:
    from src.education.lab_tasks import LAB_TASKS

    return {
        "id": lab["id"],
        "title": lab["title"],
        "minutes": lab["minutes"],
        "level": lab["level"],
        "phase": lab.get("phase", ""),
        "tag": lab.get("tag", {}),
        "objectives": lab["objectives"],
        "has_3d": lab["id"] in LABS_WITH_3D,
        "task_count": len(LAB_TASKS.get(lab["id"], [])),
    }


@router.get("/labs")
def list_labs() -> dict[str, Any]:
    from src.education.labs.lab_registry import list_labs as registry

    return {"labs": [_summary(lab) for lab in registry()]}


@router.get("/labs/{lab_id}")
def lab_detail(lab_id: str) -> dict[str, Any]:
    from src.education.lab_tasks import LAB_TASKS
    from src.education.labs.runner import list_params
    from src.education.labs.theory import theory_markdown

    lab = _lab_or_404(lab_id)
    return {
        **_summary(lab),
        "theory": theory_markdown(lab.get("theory") or lab_id),
        "params": list_params(lab_id),
        "tasks": [
            {
                "id": t["id"],
                "kind": t["kind"],
                "prompt": _md(t["prompt"]),
                "choices": t.get("choices") or [],
                "unit": t.get("unit", ""),
                "hint": _md(t.get("hint")),
            }
            for t in LAB_TASKS.get(lab_id, [])
        ],
        "viewer_path": VIEWER_PATH if lab_id in LABS_WITH_3D else None,
    }


class RunRequest(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)


@router.post("/labs/{lab_id}/run")
def run(lab_id: str, req: RunRequest) -> dict[str, Any]:
    from src.education.labs.runner import run_lab

    _lab_or_404(lab_id)
    try:
        return run_lab(lab_id, req.params)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


class TaskAnswer(BaseModel):
    number: Optional[float] = None
    choice_index: Optional[int] = None
    student: Optional[StudentRef] = None  # a class member: the solved task is recorded


@router.post("/labs/{lab_id}/tasks/{task_id}/check")
def check_task(lab_id: str, task_id: str, req: TaskAnswer) -> dict[str, Any]:
    from src.education.lab_tasks import check_task_answer

    _lab_or_404(lab_id)
    result = check_task_answer(lab_id, task_id, number=req.number, choice_index=req.choice_index)
    if result.get("status") == "unknown_task":
        raise HTTPException(status_code=404, detail=f"Unknown task: {task_id}")
    if result.get("ok"):
        record(req.student, "lab_task", lab_id, 100.0, True, sub=task_id)
    for key in ("explain_en", "explain_kk"):
        result[key] = _md({"x": result.get(key) or ""})["x"]
    return result


@router.get("/labs/{lab_id}/test")
def get_test(lab_id: str, lang: str = "kk") -> dict[str, Any]:
    from src.education.labs.lab_tests import public_test

    _lab_or_404(lab_id)
    return public_test(lab_id, lang)


class GradeRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    lang: str = "kk"
    student: Optional[StudentRef] = None  # a class member: the result is recorded


@router.post("/labs/{lab_id}/test/grade")
def grade(lab_id: str, req: GradeRequest) -> dict[str, Any]:
    from src.education.labs.lab_tests import grade_test

    _lab_or_404(lab_id)
    result = grade_test(lab_id, req.answers, req.lang)
    record(req.student, "lab_test", lab_id, result["percent"], result["passed"])
    return result


# ---- the student's report ----------------------------------------------------
# The report is rebuilt here from what the phone sends: the lab is run again
# with the parameters and the test graded again from the answers, so the
# results in it are the server's. The page is kept for an hour under a random
# id, for the phone to open in the browser (print or save as PDF).
REPORT_TTL_S = 3600
REPORTS_KEPT = 300
_reports: dict[str, tuple[float, str]] = {}


class ReportRequest(BaseModel):
    student: str = Field("", max_length=80)
    group: str = Field("", max_length=40)
    lang: str = "kk"
    params: Optional[dict[str, Any]] = None
    answers: Optional[dict[str, Any]] = None
    tasks_done: list[str] = Field(default_factory=list, max_length=60)
    best_test_percent: Optional[float] = Field(None, ge=0, le=100)
    last_3d_check: Optional[dict[str, Any]] = None


def _keep_report(page: str) -> str:
    now = time.time()
    for rid in [k for k, (until, _) in _reports.items() if until < now]:
        del _reports[rid]
    while len(_reports) >= REPORTS_KEPT:
        del _reports[next(iter(_reports))]  # the oldest
    rid = secrets.token_urlsafe(16)
    _reports[rid] = (now + REPORT_TTL_S, page)
    return rid


@router.post("/labs/{lab_id}/report")
def make_report(lab_id: str, req: ReportRequest) -> dict[str, Any]:
    from src.education.labs.lab_tests import grade_test
    from src.education.labs.report import build_report_html, report_filename
    from src.education.labs.runner import run_lab

    _lab_or_404(lab_id)
    lang = "kk" if req.lang == "kk" else "en"
    run_result = None
    if req.params is not None and lab_id not in LABS_WITH_3D:
        try:
            run_result = run_lab(lab_id, req.params)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
    test_result = grade_test(lab_id, req.answers, lang) if req.answers else None
    check = req.last_3d_check or {}
    last_3d_check = (
        {"score": int(check["score"]), "total": int(check["total"])}
        if isinstance(check.get("score"), (int, float))
        and isinstance(check.get("total"), (int, float))
        else None
    )
    page = build_report_html(
        lab_id,
        lang,
        student=req.student.strip(),
        group=req.group.strip(),
        run_result=run_result,
        test_result=test_result,
        best_test_percent=req.best_test_percent,
        tasks_done=[t for t in req.tasks_done if isinstance(t, str) and len(t) <= 80],
        last_3d_check=last_3d_check,
    )
    rid = _keep_report(page)
    return {
        "id": rid,
        "url": f"/lab-reports/{rid}",
        "filename": report_filename(lab_id, req.student),
        "html": page,
    }


@router.get("/lab-reports/{rid}", response_class=HTMLResponse)
def get_report(rid: str) -> HTMLResponse:
    kept = _reports.get(rid)
    if kept is None or kept[0] < time.time():
        raise HTTPException(status_code=404, detail="The report has expired; make it again.")
    return HTMLResponse(kept[1])
