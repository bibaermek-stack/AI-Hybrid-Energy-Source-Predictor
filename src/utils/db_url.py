"""
The database URL as SQLAlchemy should read it.

Railway gives DATABASE_URL as postgres:// or postgresql://. SQLAlchemy 2.1
reads a bare postgresql:// as the psycopg (v3) driver, which is not
installed; requirements.txt has psycopg2-binary. Every start logged
"No module named 'psycopg'" and nothing could use the database. Name the
driver explicitly.
"""

from __future__ import annotations


def normalize_db_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg2://" + url[len(prefix) :]
    return url
