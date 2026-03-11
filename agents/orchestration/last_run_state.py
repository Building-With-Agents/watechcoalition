"""
Last run start/finish timestamps for the ingestion trigger (EXP-005 observability).

Writes a small JSON file on each pipeline run so we can query "last run start"
and "last run finish" without a database. Path is agents/data/scheduler_last_run.json
by default, or SCHEDULER_STATE_PATH (env) for an absolute path.

Read from command line:

    python -m agents.orchestration.last_run_state
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repo root / agents dir for default path when run as __main__ or imported.
_AGENTS_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_PATH = _AGENTS_DIR / "data" / "scheduler_last_run.json"


def _state_path() -> Path:
    p = os.environ.get("SCHEDULER_STATE_PATH", "").strip()
    if p:
        return Path(p)
    _DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_PATH


def write_last_run_start() -> None:
    """Record that a run has started. Overwrites last_run_start; keeps existing last_run_finish."""
    path = _state_path()
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    data["last_run_start"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_last_run_finish() -> None:
    """Record that a run has finished. Keeps existing last_run_start."""
    path = _state_path()
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    data["last_run_finish"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_last_run() -> dict[str, str | None]:
    """Return last_run_start and last_run_finish (ISO strings or None if missing)."""
    path = _state_path()
    if not path.exists():
        return {"last_run_start": None, "last_run_finish": None}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "last_run_start": data.get("last_run_start"),
            "last_run_finish": data.get("last_run_finish"),
        }
    except (json.JSONDecodeError, OSError):
        return {"last_run_start": None, "last_run_finish": None}


if __name__ == "__main__":
    if str(_AGENTS_DIR.parent) not in sys.path:
        sys.path.insert(0, str(_AGENTS_DIR.parent))
    out = read_last_run()
    print(json.dumps(out, indent=2))
