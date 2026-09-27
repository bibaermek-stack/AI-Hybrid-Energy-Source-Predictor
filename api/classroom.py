"""
Classes: a teacher sees how each student is doing in the labs and lessons.

A teacher creates a class and gets a short code for the students and a
secret teacher key (only its hash is stored). A student joins from the app
with the code and a name and gets a random token. From then on the grading
routes (lab test, practice task, lesson quiz) record the result they compute
here under that student, so a score cannot be sent from the phone, only
earned. The teacher reads the class table with the key, in the app or on the
web page static/classroom/.

Storage: the service's Postgres (DATABASE_URL) when there is one, which
survives deploys; otherwise SQLite at $CLASSROOM_DB or data/classroom.sqlite3
(tests, local runs). /classes/status says which, and whether it answers.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
import time
from pathlib import Path
from typing import Any, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from src.utils.db_url import normalize_db_url

router = APIRouter()

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I
CODE_LEN = 6
MAX_CLASSES = 2000
MAX_STUDENTS_PER_CLASS = 300

# Prefixed: the Postgres is shared with the rest of the platform.
meta = sa.MetaData()
classes = sa.Table(
    "classroom_classes",
    meta,
    sa.Column("code", sa.String(12), primary_key=True),
    sa.Column("name", sa.String(80), nullable=False),
    sa.Column("key_salt", sa.String(64), nullable=False),
    sa.Column("key_hash", sa.String(128), nullable=False),
    sa.Column("created_at", sa.Float, nullable=False),
)
students = sa.Table(
    "classroom_students",
    meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("class_code", sa.String(12), nullable=False, index=True),
    sa.Column("token", sa.String(64), nullable=False, unique=True),
    sa.Column("name", sa.String(80), nullable=False),
    sa.Column("joined_at", sa.Float, nullable=False),
    sa.Column("last_seen", sa.Float, nullable=False),
)
results = sa.Table(
    "classroom_results",
    meta,
    sa.Column("student_id", sa.Integer, primary_key=True),
    sa.Column("kind", sa.String(16), primary_key=True),
    sa.Column("item", sa.String(64), primary_key=True),
    sa.Column("sub", sa.String(64), primary_key=True, default=""),
    sa.Column("best", sa.Float, nullable=False),
    sa.Column("passed", sa.Integer, nullable=False),
    sa.Column("attempts", sa.Integer, nullable=False),
    sa.Column("updated_at", sa.Float, nullable=False),
)

_engines: dict[str, sa.Engine] = {}
_lock = threading.Lock()  # SQLite takes one writer; Postgres does not need it


def database_url() -> str:
    """$CLASSROOM_DB (a file) wins, then DATABASE_URL, then a local file."""
    path = os.environ.get("CLASSROOM_DB")
    if path:
        return f"sqlite:///{path}"
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if url:
        return normalize_db_url(url)
    return "sqlite:///data/classroom.sqlite3"


def engine() -> sa.Engine:
    url = database_url()
    with _lock:
        eng = _engines.get(url)
        if eng is None:
            if url.startswith("sqlite:///"):
                Path(url[len("sqlite:///") :]).parent.mkdir(parents=True, exist_ok=True)
            eng = sa.create_engine(url, pool_pre_ping=True)
            meta.create_all(eng)
            _engines[url] = eng
    return eng


def _hash_key(key: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", key.encode(), bytes.fromhex(salt), 100_000).hex()


def _class_or_404(conn: sa.Connection, code: str):
    row = conn.execute(sa.select(classes).where(classes.c.code == code.upper())).first()
    if row is None:
        raise HTTPException(status_code=404, detail="No class with this code.")
    return row


def _check_key(row, key: Optional[str]) -> None:
    if not key or not hmac.compare_digest(_hash_key(key, row.key_salt), row.key_hash):
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
        with engine().begin() as conn:
            sid = conn.execute(
                sa.select(students.c.id).where(
                    students.c.token == student.token,
                    students.c.class_code == student.class_code.upper(),
                )
            ).scalar()
            if sid is None:
                return
            conn.execute(students.update().where(students.c.id == sid).values(last_seen=now))
            key = (
                (results.c.student_id == sid)
                & (results.c.kind == kind)
                & (results.c.item == item)
                & (results.c.sub == sub)
            )
            old = conn.execute(sa.select(results.c.best, results.c.passed).where(key)).first()
            if old is None:
                conn.execute(
                    results.insert().values(
                        student_id=sid,
                        kind=kind,
                        item=item,
                        sub=sub,
                        best=float(percent),
                        passed=int(bool(passed)),
                        attempts=1,
                        updated_at=now,
                    )
                )
            else:
                conn.execute(
                    results.update()
                    .where(key)
                    .values(
                        best=max(old.best, float(percent)),
                        passed=max(old.passed, int(bool(passed))),
                        attempts=results.c.attempts + 1,
                        updated_at=now,
                    )
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
    with engine().begin() as conn:
        if conn.execute(sa.select(sa.func.count()).select_from(classes)).scalar() >= MAX_CLASSES:
            raise HTTPException(status_code=429, detail="Too many classes on this server.")
        for _ in range(20):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            if (
                conn.execute(sa.select(classes.c.code).where(classes.c.code == code)).first()
                is None
            ):
                break
        conn.execute(
            classes.insert().values(
                code=code,
                name=req.name.strip(),
                key_salt=salt,
                key_hash=_hash_key(key, salt),
                created_at=time.time(),
            )
        )
    return {"code": code, "name": req.name.strip(), "teacher_key": key}


class Join(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)


@router.post("/classes/{code}/join")
def join_class(code: str, req: Join) -> dict[str, Any]:
    now = time.time()
    token = secrets.token_urlsafe(18)
    with engine().begin() as conn:
        row = _class_or_404(conn, code)
        count = conn.execute(
            sa.select(sa.func.count())
            .select_from(students)
            .where(students.c.class_code == row.code)
        ).scalar()
        if count >= MAX_STUDENTS_PER_CLASS:
            raise HTTPException(status_code=429, detail="The class is full.")
        conn.execute(
            students.insert().values(
                class_code=row.code,
                token=token,
                name=req.name.strip(),
                joined_at=now,
                last_seen=now,
            )
        )
    return {"code": row.code, "class_name": row.name, "token": token}


@router.get("/classes/{code}/results")
def class_results(code: str, x_teacher_key: Optional[str] = Header(None)) -> dict[str, Any]:
    """Every student with their best result per lab test, task and lesson quiz."""
    from src.education.lab_tasks import LAB_TASKS
    from src.education.labs.lab_registry import list_labs

    with engine().connect() as conn:
        row = _class_or_404(conn, code)
        _check_key(row, x_teacher_key)
        members = conn.execute(
            sa.select(students.c.id, students.c.name, students.c.joined_at, students.c.last_seen)
            .where(students.c.class_code == row.code)
            .order_by(students.c.name)
        ).all()
        rows = conn.execute(
            sa.select(results)
            .join(students, students.c.id == results.c.student_id)
            .where(students.c.class_code == row.code)
        ).all()

    by_student: dict[int, dict[str, Any]] = {
        s.id: {
            "id": s.id,
            "name": s.name,
            "joined_at": s.joined_at,
            "last_seen": s.last_seen,
            "labs": {},
            "quizzes": {},
        }
        for s in members
    }
    for r in rows:
        st = by_student.get(r.student_id)
        if st is None:
            continue
        if r.kind == "quiz":
            st["quizzes"][r.item] = {"best": r.best, "passed": bool(r.passed)}
            continue
        lab = st["labs"].setdefault(
            r.item, {"test": None, "passed": False, "attempts": 0, "tasks": []}
        )
        if r.kind == "lab_test":
            lab["test"], lab["passed"], lab["attempts"] = r.best, bool(r.passed), r.attempts
        elif r.kind == "lab_task":
            lab["tasks"].append(r.sub)
    for st in by_student.values():
        st["labs_passed"] = sum(1 for lab in st["labs"].values() if lab["passed"])
        st["tasks_done"] = sum(len(lab["tasks"]) for lab in st["labs"].values())
        tests = [lab["test"] for lab in st["labs"].values() if lab["test"] is not None]
        st["test_avg"] = round(sum(tests) / len(tests), 1) if tests else None
    return {
        "code": row.code,
        "name": row.name,
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
    with engine().begin() as conn:
        row = _class_or_404(conn, code)
        _check_key(row, x_teacher_key)
        found = conn.execute(
            sa.select(students.c.id).where(
                students.c.id == student_id, students.c.class_code == row.code
            )
        ).first()
        if found is None:
            raise HTTPException(status_code=404, detail="No such student in this class.")
        conn.execute(results.delete().where(results.c.student_id == student_id))
        conn.execute(students.delete().where(students.c.id == student_id))
    return {"removed": student_id}


@router.get("/classes/status")
def status() -> dict[str, Any]:
    """Where class data lives, whether that survives a redeploy, and whether it answers."""
    url = database_url()
    backend = "postgresql" if url.startswith("postgresql") else "sqlite"
    try:
        with engine().connect() as conn:
            conn.execute(sa.text("SELECT 1"))
        ok, error = True, ""
    except Exception as err:
        ok, error = False, f"{type(err).__name__}: {err}"[:200]
    return {
        "backend": backend,
        # a Postgres, or a file the operator placed (a volume); not the default file
        "persistent": backend == "postgresql" or bool(os.environ.get("CLASSROOM_DB")),
        "ok": ok,
        "error": error,
    }
