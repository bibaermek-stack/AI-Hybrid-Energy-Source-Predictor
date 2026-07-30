"""
Locate optional CACER_Simulator checkout (git submodule or env override).

Never put CACER ``src/`` on PYTHONPATH as top-level ``src`` alongside EcoPradict.
"""

from __future__ import annotations

import os
from pathlib import Path

# EcoPradict project root: .../EcoPredict AI
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_SUBMODULE = _PROJECT_ROOT / "third_party" / "CACER_Simulator"


def get_cacer_root() -> Path | None:
    """
    Return CACER root directory if present.

    Order:
    1. ``ECOPREDICT_CACER_ROOT`` environment variable
    2. ``third_party/CACER_Simulator`` git submodule
    """
    env = (os.environ.get("ECOPREDICT_CACER_ROOT") or "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir() and (p / "README.md").is_file():
            return p
        return None
    if _DEFAULT_SUBMODULE.is_dir() and (
        (_DEFAULT_SUBMODULE / "README.md").is_file()
        or (_DEFAULT_SUBMODULE / "LICENSE.txt").is_file()
    ):
        return _DEFAULT_SUBMODULE.resolve()
    return None


def cacer_tutorial_path(name: str = "4. Tutorial_power_flow_simulator.ipynb") -> Path | None:
    root = get_cacer_root()
    if root is None:
        return None
    path = root / name
    return path if path.is_file() else None


def power_flow_notebook_path() -> Path:
    """EcoPradict elective notebook (always relative to project, may not exist yet)."""
    return _PROJECT_ROOT / "notebooks" / "labs" / "power_flow.ipynb"


def sim_cacer_status() -> dict[str, object]:
    """Dependency and path status for Labs / docs (no hard import failures)."""
    root = get_cacer_root()
    pandapower_ok = False
    pvlib_ok = False
    pandapower_err = ""
    pvlib_err = ""
    try:
        import pandapower  # noqa: F401

        pandapower_ok = True
    except Exception as e:  # pragma: no cover - env dependent
        pandapower_err = str(e)
    try:
        import pvlib  # noqa: F401

        pvlib_ok = True
    except Exception as e:  # pragma: no cover
        pvlib_err = str(e)

    nb = power_flow_notebook_path()
    tut = cacer_tutorial_path()
    return {
        "cacer_root": str(root) if root else None,
        "cacer_present": root is not None,
        "tutorial_power_flow": str(tut) if tut else None,
        "ecopredict_notebook": str(nb),
        "ecopredict_notebook_exists": nb.is_file(),
        "pandapower": pandapower_ok,
        "pandapower_error": pandapower_err,
        "pvlib": pvlib_ok,
        "pvlib_error": pvlib_err,
        "sim_cacer_ready": pandapower_ok and pvlib_ok,
        "install_hint": 'pip install -e ".[sim-cacer]"',
        "submodule_hint": (
            "git submodule update --init --recursive third_party/CACER_Simulator"
        ),
    }
