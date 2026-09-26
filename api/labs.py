"""
The 12 education labs over HTTP, for the mobile app.

The website renders the same labs in Streamlit from src/education/labs; the
phone gets them here: the list, a lab's parameters and theory, a simulation
run, the practice tasks and the final test. The 3D inverter lab itself is a
static page (static/lab3d/, served under /static/lab3d/) that calls the test
routes below from inside the app's WebView.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

VIEWER_PATH = "/static/lab3d/index.html"
LABS_WITH_3D = {"lab_inverter_wiring"}


def _lab_or_404(lab_id: str) -> dict[str, Any]:
    from src.education.labs.lab_registry import LABS

    lab = LABS.get(lab_id)
    if lab is None:
        raise HTTPException(status_code=404, detail=f"Unknown lab: {lab_id}")
    return lab


def _summary(lab: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": lab["id"],
        "title": lab["title"],
        "minutes": lab["minutes"],
        "level": lab["level"],
        "phase": lab.get("phase", ""),
        "tag": lab.get("tag", {}),
        "objectives": lab["objectives"],
        "has_3d": lab["id"] in LABS_WITH_3D,
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
                "prompt": t["prompt"],
                "choices": t.get("choices") or [],
                "unit": t.get("unit", ""),
                "hint": t.get("hint"),
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


@router.post("/labs/{lab_id}/tasks/{task_id}/check")
def check_task(lab_id: str, task_id: str, req: TaskAnswer) -> dict[str, Any]:
    from src.education.lab_tasks import check_task_answer

    _lab_or_404(lab_id)
    result = check_task_answer(lab_id, task_id, number=req.number, choice_index=req.choice_index)
    if result.get("status") == "unknown_task":
        raise HTTPException(status_code=404, detail=f"Unknown task: {task_id}")
    return result


@router.get("/labs/{lab_id}/test")
def get_test(lab_id: str, lang: str = "kk") -> dict[str, Any]:
    from src.education.labs.lab_tests import public_test

    _lab_or_404(lab_id)
    return public_test(lab_id, lang)


class GradeRequest(BaseModel):
    answers: dict[str, Any] = Field(default_factory=dict)
    lang: str = "kk"


@router.post("/labs/{lab_id}/test/grade")
def grade(lab_id: str, req: GradeRequest) -> dict[str, Any]:
    from src.education.labs.lab_tests import grade_test

    _lab_or_404(lab_id)
    return grade_test(lab_id, req.answers, req.lang)
