"""Static educational markdown content loaders."""

from pathlib import Path

CONTENT_DIR = Path(__file__).resolve().parent


def list_content_files() -> list[Path]:
    return sorted(CONTENT_DIR.glob("*.md"))


def read_content(name: str) -> str:
    path = CONTENT_DIR / name
    if not path.suffix:
        path = path.with_suffix(".md")
    return path.read_text(encoding="utf-8")
