"""
Static URL helpers for the 3D model viewer.

Production + local Streamlit:
  Use Streamlit built-in static serving (``enableStaticServing``) so assets are
  same-origin at ``{origin}/app/static/...``. That avoids Chrome Private Network
  Access blocks on localhost iframes and Streamlit "Component not found".

  Assets live under ``dashboard/static/`` (next to ``dashboard/app.py``) and are
  synced from the project-root ``static/`` folder on first resolve.
"""

from __future__ import annotations

import functools
import os
import shutil
import socket
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_server_lock = threading.Lock()
_server_port: int | None = None
_server_thread: threading.Thread | None = None
_assets_ready = False


def _project_root() -> Path:
    # dashboard/static_server.py → project root
    return Path(__file__).resolve().parent.parent


def _project_static_dir() -> Path:
    return (_project_root() / "static").resolve()


def _streamlit_static_dir() -> Path:
    """Folder Streamlit serves when main script is dashboard/app.py."""
    return (Path(__file__).resolve().parent / "static").resolve()


def ensure_streamlit_static_assets() -> Path:
    """
    Make sure ``dashboard/static`` has model_viewer.html + models/inverter
    (copied/symlinked from project ``static/``).
    """
    global _assets_ready
    dest_root = _streamlit_static_dir()
    src_root = _project_static_dir()
    dest_root.mkdir(parents=True, exist_ok=True)

    if not src_root.is_dir():
        raise FileNotFoundError(f"Project static not found: {src_root}")

    # HTML viewers
    for html_name in (
        "model_viewer.html",
        "inverter_lab_viewer.html",
    ):
        src_html = src_root / html_name
        dash_html = dest_root / html_name
        if not src_html.is_file() and dash_html.is_file():
            try:
                shutil.copy2(dash_html, src_root / html_name)
            except OSError:
                pass
            src_html = src_root / html_name
        if src_html.is_file():
            try:
                if (not dash_html.is_file()) or (
                    src_html.stat().st_mtime > dash_html.stat().st_mtime
                ):
                    shutil.copy2(src_html, dash_html)
            except OSError:
                try:
                    shutil.copy2(src_html, dash_html)
                except OSError:
                    pass

    def _sync_model_dir(rel: str) -> None:
        src_inv = src_root / "models" / rel
        dst_inv = dest_root / "models" / rel
        if not src_inv.is_dir():
            # also allow assets already only under dashboard/static
            if dst_inv.is_dir():
                return
            return
        dst_inv.parent.mkdir(parents=True, exist_ok=True)
        if dst_inv.is_symlink() or (dst_inv.exists() and not any(dst_inv.iterdir())):
            if dst_inv.is_symlink() or dst_inv.is_file():
                dst_inv.unlink(missing_ok=True)
            elif dst_inv.is_dir():
                shutil.rmtree(dst_inv, ignore_errors=True)
        if not dst_inv.exists():
            shutil.copytree(src_inv, dst_inv)
        else:
            for f in src_inv.iterdir():
                if f.is_file():
                    target = dst_inv / f.name
                    try:
                        # Also re-copy when size differs (git checkout often equalizes mtime)
                        need = (not target.is_file()) or target.stat().st_size == 0
                        if not need and target.is_file():
                            ss, ds = f.stat(), target.stat()
                            need = (
                                ss.st_mtime > ds.st_mtime
                                or ss.st_size != ds.st_size
                            )
                        if need:
                            shutil.copy2(f, target)
                    except OSError:
                        try:
                            shutil.copy2(f, target)
                        except OSError:
                            pass

    # Inverter meshes (primary + second Meshy unit) + training assemblies
    _sync_model_dir("inverter")
    _sync_model_dir("inverter_2411046235")
    _sync_model_dir("solar_inverter_subsystem")

    _assets_ready = True
    return dest_root


class _CORSRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _find_free_port(preferred: int = 8765) -> int:
    if not _port_open("127.0.0.1", preferred):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", preferred))
                return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def ensure_static_server(preferred_port: int = 8765) -> tuple[str, int]:
    """Dev fallback: threaded static server for project ``static/``."""
    global _server_port, _server_thread

    static_dir = _project_static_dir()
    if not static_dir.is_dir():
        raise FileNotFoundError(f"Static directory not found: {static_dir}")

    with _server_lock:
        if _server_port is not None and _port_open("127.0.0.1", _server_port):
            return f"http://127.0.0.1:{_server_port}", _server_port

        port = _find_free_port(preferred_port)
        handler = functools.partial(_CORSRequestHandler, directory=str(static_dir))
        httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        try:
            httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except OSError:
            pass

        def _run():
            try:
                httpd.serve_forever(poll_interval=0.5)
            except Exception:
                pass

        t = threading.Thread(target=_run, name="ecopredict-static-server", daemon=True)
        t.start()
        _server_thread = t
        _server_port = port

        for _ in range(20):
            if _port_open("127.0.0.1", port):
                break
            threading.Event().wait(0.05)

        return f"http://127.0.0.1:{port}", port


def browser_public_origin() -> str | None:
    """Browser-facing origin for this Streamlit app."""
    for key in ("PUBLIC_BASE_URL", "STREAMLIT_BROWSER_ORIGIN", "STATIC_PUBLIC_ORIGIN"):
        v = (os.getenv(key) or "").strip().rstrip("/")
        if v:
            return v

    railway_domain = (os.getenv("RAILWAY_PUBLIC_DOMAIN") or "").strip()
    if railway_domain:
        return f"https://{railway_domain}"

    try:
        import streamlit as st

        headers = st.context.headers
        host = headers.get("Host") or headers.get("host")
        if not host:
            return None
        proto = (
            headers.get("X-Forwarded-Proto")
            or headers.get("x-forwarded-proto")
            or ""
        ).split(",")[0].strip()
        if not proto:
            if host.startswith("localhost") or host.startswith("127.0.0.1"):
                proto = "http"
            else:
                proto = "https"
        return f"{proto}://{host}"
    except Exception:
        return None


def _fastapi_static_candidates() -> list[str]:
    custom = (os.getenv("API_STATIC_URL") or "").strip().rstrip("/")
    out: list[str] = []
    if custom:
        out.append(custom)
    out.extend(
        [
            "http://127.0.0.1:8001/static",
            "http://localhost:8001/static",
            "http://127.0.0.1:8000/static",
        ]
    )
    return out


def resolve_viewer_base_url(api_static_candidates: list[str] | None = None) -> tuple[str, str]:
    """
    Pick browser-reachable base for model_viewer.html.

    Returns (base_without_trailing_slash, source_label).
    """
    import urllib.request

    # Always prepare dashboard/static assets for Streamlit static serving
    try:
        ensure_streamlit_static_assets()
    except Exception:
        pass

    # 1) Explicit override
    env_base = (os.getenv("STATIC_VIEWER_BASE") or os.getenv("PUBLIC_STATIC_URL") or "").strip().rstrip("/")
    if env_base:
        return env_base, "env"

    # 2) Streamlit same-origin static (production + local) — preferred
    origin = browser_public_origin()
    if origin:
        # Official path when server.enableStaticServing = true
        return f"{origin}/app/static", "streamlit-static"

    # 3) Local FastAPI static (no browser Host header — e.g. tests)
    candidates = api_static_candidates or _fastapi_static_candidates()
    for base in candidates:
        url = base.rstrip("/") + "/model_viewer.html"
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=1.2) as resp:
                if 200 <= getattr(resp, "status", 200) < 400:
                    return base.rstrip("/"), "fastapi"
        except Exception:
            try:
                with urllib.request.urlopen(url, timeout=1.2) as resp:
                    if 200 <= getattr(resp, "status", 200) < 400:
                        return base.rstrip("/"), "fastapi"
            except Exception:
                continue

    # 4) Local threaded server
    base, port = ensure_static_server()
    return base.rstrip("/"), f"local:{port}"
