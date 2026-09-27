"""
The Learn lessons and quizzes over HTTP, for the mobile app.

The website shows the six lessons of src/education/lessons.py and their
quizzes (src/education/quiz.py) on its Learn page; the app showed four short
cards. Here each lesson comes as one Flet Markdown document (formulas with a
space after a closing $), with the labs and app screens it leads to, and its
quiz comes without the answers; grading happens here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# Where each lesson leads in the app: labs by id, screens by the app's keys.
RELATED: dict[str, dict[str, list[str]]] = {
    "lstm_forecasting": {"labs": ["lab_pv_physics", "lab_pv_yield"], "screens": ["forecast"]},
    "yolo_faults": {"labs": ["lab_inverter_wiring"], "screens": ["faults"]},
    "hybrid_optimization": {
        "labs": ["lab_microgrid_dispatch", "lab_heuristic_vs_pulp", "lab_bess_soc"],
        "screens": ["opt"],
    },
    "xai_rag": {"labs": [], "screens": ["training", "chat"]},
    "sustainable_management": {
        "labs": ["lab_shared_energy", "lab_rec_finance"],
        "screens": ["sustainability"],
    },
    "kz_case_study": {"labs": ["lab_pv_yield", "lab_grid_impact"], "screens": ["live"]},
}


def _lang(lang: str) -> str:
    return "kk" if lang == "kk" else "en"


def lesson_markdown(lesson: dict[str, Any]) -> str:
    """One resolved lesson (get_lesson) as Markdown for Flet."""
    from src.education.labs.theory import to_flet_markdown

    out: list[str] = []
    for sec in lesson["sections"]:
        kind, title = sec["type"], sec.get("title", "")
        if kind == "tip":
            out.append(f"> 💡 **{title}**  \n> {sec.get('body', '')}")
            continue
        if kind == "case":
            out.append(f"### 📍 {title}\n\n{sec.get('body', '')}")
            continue
        out.append(f"### {title}")
        if kind == "formula":
            out.append(f"$$\n{sec['latex']}\n$$")
        if sec.get("body"):
            out.append(sec["body"])
        items = sec.get("items") or []
        if kind == "tasks":
            out.append("\n".join(f"{i}. {item}" for i, item in enumerate(items, start=1)))
        elif items:
            out.append("\n".join(f"- {item}" for item in items))
    return to_flet_markdown("\n\n".join(out))


@router.get("/learn/lessons")
def lessons(lang: str = "kk") -> dict[str, Any]:
    from src.education.lessons import list_lessons

    return {"lessons": list_lessons(_lang(lang))}


@router.get("/learn/lessons/{lesson_id}")
def lesson(lesson_id: str, lang: str = "kk") -> dict[str, Any]:
    from src.education.labs.lab_registry import LABS
    from src.education.labs.theory import to_flet_markdown
    from src.education.lessons import get_lesson

    got = get_lesson(lesson_id, _lang(lang))
    if got is None:
        raise HTTPException(status_code=404, detail=f"Unknown lesson: {lesson_id}")
    return {
        "id": got["id"],
        "title": got["title"],
        "level": got["level"],
        "minutes": got["minutes"],
        "markdown": lesson_markdown(got),
        "key_takeaways": [to_flet_markdown(k) for k in got["key_takeaways"]],
        "quiz": got.get("related_quiz"),
        "related_labs": [
            {"id": lab_id, "title": LABS[lab_id]["title"]}
            for lab_id in RELATED.get(lesson_id, {}).get("labs", [])
            if lab_id in LABS
        ],
        "related_screens": RELATED.get(lesson_id, {}).get("screens", []),
    }


@router.get("/learn/quizzes/{quiz_id}")
def quiz(quiz_id: str, lang: str = "kk") -> dict[str, Any]:
    from src.education.quiz import get_quiz

    got = get_quiz(quiz_id, _lang(lang))
    if got is None:
        raise HTTPException(status_code=404, detail=f"Unknown quiz: {quiz_id}")
    return {
        "id": got["id"],
        "title": got["title"],
        "questions": [
            {"id": q["id"], "prompt": q["prompt"], "choices": q["choices"]}
            for q in got["questions"]
        ],
    }


class QuizAnswers(BaseModel):
    answers: dict[str, int] = Field(default_factory=dict)
    lang: str = "kk"


@router.post("/learn/quizzes/{quiz_id}/grade")
def grade(quiz_id: str, req: QuizAnswers) -> dict[str, Any]:
    from src.education.quiz import get_quiz, grade_quiz

    got = get_quiz(quiz_id, _lang(req.lang))
    if got is None:
        raise HTTPException(status_code=404, detail=f"Unknown quiz: {quiz_id}")
    result = grade_quiz(quiz_id, req.answers)
    explain = {q["id"]: q["explain"] for q in got["questions"]}
    for d in result["details"]:
        d["explain"] = explain.get(d["id"], "")
    return result
