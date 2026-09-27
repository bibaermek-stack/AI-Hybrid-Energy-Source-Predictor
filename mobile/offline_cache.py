"""
The last good server replies, kept on the phone for use without a connection.

Every read the app makes (forecast, Solarman, metrics, the labs' theory, tasks
and tests, the Home prediction) is saved here when it succeeds. When the phone
is offline or the server does not answer, the screen shows the saved reply
with the time it was fetched instead of an empty page.

Files live in the app's private data folder (FLET_APP_STORAGE_DATA in a built
app), one JSON file per request.
"""

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Optional, Tuple


def cache_dir() -> Path:
    base = (
        os.environ.get("ECOPREDICT_CACHE_DIR")
        or os.environ.get("FLET_APP_STORAGE_DATA")
        or os.path.join(os.path.expanduser("~"), ".ecopredict")
    )
    return Path(base) / "cache"


def _path(key: str) -> Path:
    return cache_dir() / (hashlib.sha1(key.encode("utf-8")).hexdigest() + ".json")


def put(key: str, value: Any) -> None:
    """Save a reply; a full or read-only disk only costs the offline copy."""
    try:
        path = _path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"key": key, "saved_at": time.time(), "value": value}, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)  # never leave a half-written file behind
    except (OSError, TypeError, ValueError) as err:
        print(f"offline cache: {key} not saved: {err}")


def get(key: str) -> Optional[Tuple[Any, float]]:
    """(reply, time saved) or None."""
    try:
        saved = json.loads(_path(key).read_text(encoding="utf-8"))
        if saved.get("key") != key:
            return None
        return saved["value"], float(saved["saved_at"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def clear() -> None:
    try:
        for f in cache_dir().glob("*.json"):
            f.unlink()
    except OSError:
        pass
