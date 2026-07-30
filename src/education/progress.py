"""
Simple learning progress tracker backed by Streamlit session_state
(or a plain dict for unit tests / notebooks).
"""

from __future__ import annotations

from typing import Any, MutableMapping


class ProgressTracker:
    """
    Track completed lessons, quiz scores, exercise flags, and lab completions.

    Usage with Streamlit::

        from src.education.progress import ProgressTracker
        progress = ProgressTracker.from_session(st.session_state)
        progress.mark_lesson("lstm_forecasting")
        progress.mark_lab("lab_microgrid_dispatch")
        st.write(progress.summary())
    """

    STATE_KEY = "ep_edu_progress"

    def __init__(self, store: MutableMapping[str, Any] | None = None) -> None:
        self._store = store if store is not None else {}
        if self.STATE_KEY not in self._store:
            self._store[self.STATE_KEY] = self._empty()
        else:
            # Migrate older sessions that lack labs_done / lab_tasks
            data = self._store[self.STATE_KEY]
            data.setdefault("lessons_done", [])
            data.setdefault("quizzes", {})
            data.setdefault("exercises", {})
            data.setdefault("labs_done", [])
            data.setdefault("lab_tasks", {})  # lab_id -> [task_id, ...]
            # Back-fill labs_done from exercises already marked as lab_*
            for eid, ok in list(data["exercises"].items()):
                if ok and str(eid).startswith("lab_") and eid not in data["labs_done"]:
                    data["labs_done"].append(eid)

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "lessons_done": [],
            "quizzes": {},  # quiz_id -> best percent
            "exercises": {},  # exercise_id -> True
            "labs_done": [],  # lab_id list
            "lab_tasks": {},  # lab_id -> list of completed task ids
        }

    @classmethod
    def from_session(cls, session_state) -> "ProgressTracker":
        return cls(session_state)

    @property
    def data(self) -> dict[str, Any]:
        return self._store[self.STATE_KEY]

    def mark_lesson(self, lesson_id: str) -> None:
        done = self.data["lessons_done"]
        if lesson_id not in done:
            done.append(lesson_id)

    def mark_exercise(self, exercise_id: str) -> None:
        self.data["exercises"][exercise_id] = True

    def mark_lab(self, lab_id: str) -> None:
        """Mark a laboratory complete (also sets exercises[lab_id])."""
        self.mark_exercise(lab_id)
        done = self.data.setdefault("labs_done", [])
        if lab_id not in done:
            done.append(lab_id)

    def _lab_tasks_map(self) -> dict:
        """Always return a real dict for lab_tasks (fix None / bad types)."""
        data = self.data
        tasks = data.get("lab_tasks")
        if not isinstance(tasks, dict):
            tasks = {}
            data["lab_tasks"] = tasks
        return tasks

    def mark_task(self, lab_id: str, task_id: str) -> None:
        """Mark one graded task complete for a lab."""
        tasks = self._lab_tasks_map()
        done = list(tasks.get(lab_id) or [])
        if task_id not in done:
            done.append(task_id)
            tasks[lab_id] = done

    def tasks_done_for(self, lab_id: str) -> list[str]:
        tasks = self._lab_tasks_map()
        raw = tasks.get(lab_id) or []
        if not isinstance(raw, (list, tuple, set)):
            return []
        return [str(x) for x in raw]

    def task_done(self, lab_id: str, task_id: str) -> bool:
        return task_id in self.tasks_done_for(lab_id)

    def record_quiz(self, quiz_id: str, percent: float) -> None:
        prev = float(self.data["quizzes"].get(quiz_id, 0.0))
        self.data["quizzes"][quiz_id] = max(prev, float(percent))

    def lesson_done(self, lesson_id: str) -> bool:
        return lesson_id in self.data["lessons_done"]

    def lab_done(self, lab_id: str) -> bool:
        return lab_id in self.data.get("labs_done", []) or bool(
            self.data.get("exercises", {}).get(lab_id)
        )

    def summary(self) -> dict[str, Any]:
        quizzes = self.data["quizzes"]
        avg = sum(quizzes.values()) / len(quizzes) if quizzes else 0.0
        labs = list(self.data.get("labs_done") or [])
        lab_tasks = self._lab_tasks_map()
        n_tasks = 0
        lab_tasks_out: dict[str, list] = {}
        for k, v in lab_tasks.items():
            if isinstance(v, (list, tuple, set)):
                lab_tasks_out[str(k)] = list(v)
                n_tasks += len(v)
        return {
            "lessons_completed": len(self.data.get("lessons_done") or []),
            "lessons_list": list(self.data.get("lessons_done") or []),
            "quizzes_taken": len(quizzes),
            "quiz_best_avg": round(avg, 1),
            "exercises_done": len(self.data.get("exercises") or {}),
            "labs_completed": len(labs),
            "labs_list": labs,
            "tasks_completed": n_tasks,
            "lab_tasks": lab_tasks_out,
            "quiz_scores": dict(quizzes),
        }

    def reset(self) -> None:
        self._store[self.STATE_KEY] = self._empty()
