"""
Classes: a teacher sees how each student is doing in the labs and lessons.

A teacher creates a class and gets a short code for the students and a
secret teacher key (only its hash is stored). A student joins from the app
with the code and a name and gets a random token. From then on the grading
routes (lab test, practice task, lesson quiz) record the result they compute
here under that student, so a score cannot be sent from the phone, only
earned. The teacher reads the class table with the key, in the app or on the
web page static/classroom/.

Storage is SQLite at $CLASSROOM_DB (default data/classroom.sqlite3). On
Railway that path must be on a volume, or every deploy starts empty;
/classes/status says whether it is.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I
CODE_LEN = 6
MAX_CLASSES = 2000
MAX_STUDENTS_PER_CLASS = 300
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS classes (
    code TEXT PRIMARY KEY, name TEXT NOT NULL, key_salt TEXT NOT NULL,
    key_hash TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT, class_code TEXT NOT NULL,
    token TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
    joined_at REAL NOT NULL, last_seen REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS students_by_class ON students (class_code);
CREATE TABLE IF NOT EXISTS results (
    student_id INTEGER NOT NULL, kind TEXT NOT NULL, item TEXT NOT NULL,
    sub TEXT NOT NULL DEFAULT '', best REAL NOT NULL, passed INTEGER NOT NULL,
    attempts INTEGER NOT NULL, updated_at REAL NOT NULL,
    PRIMARY KEY (student_id, kind, item, sub)
);
"""


def db_path() -> Path:
    return Path(os.environ.get("CLASSROOM_DB") or "data/classroom.sqlite3")


@contextmanager
def _db() -> Iterator[sqlite3.Connection]:
    """One connection, one transaction (committed unless it raises), closed after."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        conn = sqlite3.connect(path, timeout=10)
        try:
            conn.row_factory = sqlite3.Row
            conn.executescript(SCHEMA)
            with conn:
                yield conn
        finally:
            conn.close()


def _hash_key(key: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", key.encode(), bytes.fromhex(salt), 100_000).hex()


def _class_or_404(conn: sqlite3.Connection, code: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM classes WHERE code = ?", (code.upper(),)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="No class with this code.")
    return row


def _check_key(row: sqlite3.Row, key: Optional[str]) -> None:
    if not key or not hmac.compare_digest(_hash_key(key, row["key_salt"]), row["key_hash"]):
        raise HTTPException(status_code=403, detail="Wrong teacher key.")


# ---- recording (called by the grading routes) --------------------------------
class StudentRef(BaseModel):
    class_code: str = Field(..., max_length=12)
    token: str = Field(..., max_length=64)


def record(
    student: Optional[StudentRef], kind: str, item: str, percent: float, passed: bool, sub: str = ""
) -> None:
    """Keep a student's best result for an item; never fails the grading."""
    if student is None:
        return
    try:
        now = time.time()
        with _db() as conn:
            row = conn.execute(
                "SELECT id FROM students WHERE token = ? AND class_code = ?",
                (student.token, student.class_code.upper()),
            ).fetchone()
            if row is None:
                return
            conn.execute("UPDATE students SET last_seen = ? WHERE id = ?", (now, row["id"]))
            conn.execute(
                """
                INSERT INTO results (student_id, kind, item, sub, best, passed, attempts, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT (student_id, kind, item, sub) DO UPDATE SET
                    best = MAX(best, excluded.best),
                    passed = MAX(passed, excluded.passed),
                    attempts = attempts + 1,
                    updated_at = excluded.updated_at
                """,
                (row["id"], kind, item, sub, float(percent), int(bool(passed)), now),
            )
    except Exception as err:  # the student still gets the grade
        print(f"classroom: result not recorded: {err}")


# ---- routes ------------------------------------------------------------------
class NewClass(BaseModel):
    name: str = Field(..., min_length=1, max_length=60)


@router.post("/classes")
def create_class(req: NewClass) -> dict[str, Any]:
    key = secrets.token_urlsafe(12)
    salt = secrets.token_hex(16)
    with _db() as conn:
        if conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0] >= MAX_CLASSES:
            raise HTTPException(status_code=429, detail="Too many classes on this server.")
        for _ in range(20):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            if conn.execute("SELECT 1 FROM classes WHERE code = ?", (code,)).fetchone() is None:
                break
        conn.execute(
            "INSERT INTO classes VALUES (?, ?, ?, ?, ?)",
            (code, req.name.strip(), salt, _hash_key(key, salt), time.time()),
        )
    return {"code": code, "name": req.name.strip(), "teacher_key": key}


class Join(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@router.post("/classes/{code}/join")
def join_class(code: str, req: Join) -> dict[str, Any]:
    now = time.time()
    token = secrets.token_urlsafe(18)
    with _db() as conn:
        row = _class_or_404(conn, code)
        count = conn.execute(
            "SELECT COUNT(*) FROM students WHERE class_code = ?", (row["code"],)
        ).fetchone()[0]
        if count >= MAX_STUDENTS_PER_CLASS:
            raise HTTPException(status_code=429, detail="The class is full.")
        conn.execute(
            "INSERT INTO students (class_code, token, name, joined_at, last_seen) VALUES (?, ?, ?, ?, ?)",
            (row["code"], token, req.name.strip(), now, now),
        )
    return {"code": row["code"], "class_name": row["name"], "token": token}


@router.get("/classes/{code}/results")
def class_results(code: str, x_teacher_key: Optional[str] = Header(None)) -> dict[str, Any]:
    """Every student with their best result per lab test, task and lesson quiz."""
    from src.education.lab_tasks import LAB_TASKS
    from src.education.labs.lab_registry import list_labs

    with _db() as conn:
        row = _class_or_404(conn, code)
        _check_key(row, x_teacher_key)
        students = conn.execute(
            "SELECT id, name, joined_at, last_seen FROM students WHERE class_code = ? ORDER BY name",
            (row["code"],),
        ).fetchall()
        results = conn.execute(
            """
            SELECT r.* FROM results r JOIN students s ON s.id = r.student_id
            WHERE s.class_code = ?
            """,
            (row["code"],),
        ).fetchall()

    by_student: dict[int, dict[str, Any]] = {
        s["id"]: {
            "id": s["id"],
            "name": s["name"],
            "joined_at": s["joined_at"],
            "last_seen": s["last_seen"],
            "labs": {},
            "quizzes": {},
        }
        for s in students
    }
    for r in results:
        st = by_student.get(r["student_id"])
        if st is None:
            continue
        if r["kind"] == "quiz":
            st["quizzes"][r["item"]] = {"best": r["best"], "passed": bool(r["passed"])}
            continue
        lab = st["labs"].setdefault(
            r["item"], {"test": None, "passed": False, "attempts": 0, "tasks": []}
        )
        if r["kind"] == "lab_test":
            lab["test"], lab["passed"], lab["attempts"] = (
                r["best"],
                bool(r["passed"]),
                r["attempts"],
            )
        elif r["kind"] == "lab_task":
            lab["tasks"].append(r["sub"])
    for st in by_student.values():
        st["labs_passed"] = sum(1 for lab in st["labs"].values() if lab["passed"])
        st["tasks_done"] = sum(len(lab["tasks"]) for lab in st["labs"].values())
        tests = [lab["test"] for lab in st["labs"].values() if lab["test"] is not None]
        st["test_avg"] = round(sum(tests) / len(tests), 1) if tests else None
    return {
        "code": row["code"],
        "name": row["name"],
        "labs": [
            {"id": lab["id"], "title": lab["title"], "tasks": len(LAB_TASKS.get(lab["id"], []))}
            for lab in list_labs()
        ],
        "students": list(by_student.values()),
    }


@router.delete("/classes/{code}/students/{student_id}")
def remove_student(
    code: str, student_id: int, x_teacher_key: Optional[str] = Header(None)
) -> dict[str, Any]:
    with _db() as conn:
        row = _class_or_404(conn, code)
        _check_key(row, x_teacher_key)
        found = conn.execute(
            "SELECT id FROM students WHERE id = ? AND class_code = ?", (student_id, row["code"])
        ).fetchone()
        if found is None:
            raise HTTPException(status_code=404, detail="No such student in this class.")
        conn.execute("DELETE FROM results WHERE student_id = ?", (student_id,))
        conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    return {"removed": student_id}


@router.get("/classes/status")
def status() -> dict[str, Any]:
    """Whether class data survives a redeploy (CLASSROOM_DB set to a volume)."""
    return {"db": str(db_path()), "configured": bool(os.environ.get("CLASSROOM_DB"))}
