"""
Last run start/finish timestamps for the ingestion trigger (EXP-005 observability).

Writes a small JSON file on each pipeline run so we can query "last run start"
and "last run finish" without a database. Path is agents/data/scheduler_last_run.json
by default, or SCHEDULER_STATE_PATH (env) for an absolute path.

State is stored per scheduler type so APScheduler and Task Scheduler do not
overwrite each other. Set SCHEDULER_TYPE=apscheduler or SCHEDULER_TYPE=task_scheduler
before running; default is apscheduler. The batch script sets task_scheduler;
scheduler.py sets apscheduler.

Per-scheduler section includes: last_run_start, last_run_finish, last_run_duration_seconds
(time between start and finish for the last run), recent_durations_seconds (last N run
durations), average_duration_seconds (average of recent_durations_seconds), and
last_5_runs (for drift: expected_fire_at, actual_fire_at, drift_seconds per run).

Read from command line:

    python -m agents.orchestration.last_run_state
    python -m agents.orchestration.last_run_state --drift-table [apscheduler|task_scheduler]
"""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Repo root / agents dir for default path when run as __main__ or imported.
_AGENTS_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_PATH = _AGENTS_DIR / "data" / "scheduler_last_run.json"

# Allowed values for SCHEDULER_TYPE; default when unset.
_SCHEDULER_TYPES = ("apscheduler", "task_scheduler")
_DEFAULT_SCHEDULER_TYPE = "apscheduler"

# Keep this many recent run durations for the running average.
_MAX_RECENT_DURATIONS = 20
# Keep this many runs for 5-cycle drift (expected vs actual fire time).
_MAX_DRIFT_RUNS = 5


def _state_path() -> Path:
    p = os.environ.get("SCHEDULER_STATE_PATH", "").strip()
    if p:
        return Path(p)
    _DEFAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_PATH


def _scheduler_type() -> str:
    """Return current scheduler type from SCHEDULER_TYPE env (apscheduler | task_scheduler)."""
    raw = os.environ.get("SCHEDULER_TYPE", "").strip().lower()
    return raw if raw in _SCHEDULER_TYPES else _DEFAULT_SCHEDULER_TYPE


def _interval_minutes() -> int:
    """Return INGESTION_INTERVAL_MINUTES from env (default 2) for drift expected-time calculation."""
    raw = os.environ.get("INGESTION_INTERVAL_MINUTES", "2").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 2


def _parse_iso(s: str | None) -> datetime | None:
    """Parse ISO timestamp; return None if missing or invalid."""
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _backfill_duration(section: dict) -> None:
    """If section has last_run_start and last_run_finish but no duration fields, compute and set them."""
    if section.get("last_run_duration_seconds") is not None:
        return
    start_s = section.get("last_run_start")
    finish_s = section.get("last_run_finish")
    start_dt = _parse_iso(start_s)
    finish_dt = _parse_iso(finish_s)
    if start_dt is None or finish_dt is None:
        return
    duration_sec = round((finish_dt - start_dt).total_seconds(), 3)
    section["last_run_duration_seconds"] = duration_sec
    recent: list[float] = list(section.get("recent_durations_seconds", []))
    recent.append(duration_sec)
    section["recent_durations_seconds"] = recent[-_MAX_RECENT_DURATIONS:]
    if section["recent_durations_seconds"]:
        section["average_duration_seconds"] = round(
            sum(section["recent_durations_seconds"]) / len(section["recent_durations_seconds"]), 3
        )


def _normalize(data: dict) -> dict:
    """Ensure data has nested apscheduler and task_scheduler; migrate old flat format; backfill duration when missing."""
    out = {
        "apscheduler": dict(data.get("apscheduler", {})),
        "task_scheduler": dict(data.get("task_scheduler", {})),
    }
    # Migrate old flat keys into apscheduler so existing files keep working.
    if "last_run_start" in data or "last_run_finish" in data:
        out["apscheduler"]["last_run_start"] = data.get("last_run_start")
        out["apscheduler"]["last_run_finish"] = data.get("last_run_finish")
    # Backfill duration/recent_durations/average for any section that has start+finish but no duration.
    for _key in _SCHEDULER_TYPES:
        _backfill_duration(out[_key])
    return out


def _load_data(path: Path) -> dict:
    """Load and normalize state from file."""
    if not path.exists():
        return {"apscheduler": {}, "task_scheduler": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return _normalize(data)
    except (json.JSONDecodeError, OSError):
        return {"apscheduler": {}, "task_scheduler": {}}


def write_last_run_start() -> datetime:
    """Record that a run has started for the current scheduler type. Returns the start time for passing to write_last_run_finish.

    Also appends to last_5_runs for drift tracking: expected_fire_at (from interval), actual_fire_at (now), drift_seconds.
    First run: expected = actual. Run N+1: expected = previous expected + INGESTION_INTERVAL_MINUTES.
    """
    path = _state_path()
    data = _load_data(path)
    key = _scheduler_type()
    data[key] = dict(data.get(key, {}))
    section = data[key]
    now = datetime.now(UTC)
    section["last_run_start"] = now.isoformat()

    # Drift: expected vs actual fire time (last 5 runs for EXP-005).
    last_5: list[dict] = list(section.get("last_5_runs", []))
    interval_min = _interval_minutes()
    last_expected = _parse_iso(last_5[-1]["expected_fire_at"]) if last_5 else None
    expected = now if last_expected is None else last_expected + timedelta(minutes=interval_min)
    drift_sec = round((now - expected).total_seconds(), 3)
    last_5.append({
        "expected_fire_at": expected.isoformat(),
        "actual_fire_at": now.isoformat(),
        "drift_seconds": drift_sec,
    })
    section["last_5_runs"] = last_5[-_MAX_DRIFT_RUNS:]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return now


def write_last_run_finish(started_at: datetime | None = None) -> None:
    """Record that a run has finished for the current scheduler type. Computes duration and running average.

    If started_at is provided (e.g. from write_last_run_start()), duration is always computed.
    Otherwise falls back to parsing last_run_start from the state file.
    """
    path = _state_path()
    data = _load_data(path)
    key = _scheduler_type()
    data[key] = dict(data.get(key, {}))
    section = data[key]
    finish = datetime.now(UTC)
    section["last_run_finish"] = finish.isoformat()

    # Duration of this run (seconds): prefer passed-in start time so we don't rely on file state
    start_dt = started_at if started_at is not None else _parse_iso(section.get("last_run_start"))
    if start_dt is not None:
        duration_sec = round((finish - start_dt).total_seconds(), 3)
        section["last_run_duration_seconds"] = duration_sec
        recent: list[float] = list(section.get("recent_durations_seconds", []))
        recent.append(duration_sec)
        section["recent_durations_seconds"] = recent[-_MAX_RECENT_DURATIONS:]
        if section["recent_durations_seconds"]:
            section["average_duration_seconds"] = round(
                sum(section["recent_durations_seconds"]) / len(section["recent_durations_seconds"]), 3
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def read_last_run(scheduler_type: str | None = None) -> dict:
    """Return last-run state for one or both schedulers.

    If scheduler_type is None, returns full file shape (each section includes
    last_run_start, last_run_finish, last_run_duration_seconds, recent_durations_seconds,
    average_duration_seconds when present).
    If scheduler_type is "apscheduler" or "task_scheduler", returns that section only.
    """
    path = _state_path()
    data = _load_data(path)
    if scheduler_type is not None:
        if scheduler_type not in _SCHEDULER_TYPES:
            scheduler_type = _DEFAULT_SCHEDULER_TYPE
        return dict(data.get(scheduler_type, {}))
    return data


def format_drift_table(scheduler_type: str | None = None) -> str:
    """Format last_5_runs as a Markdown table: Cycle | Expected | Actual | Drift (s).

    If scheduler_type is None, returns a table for each scheduler (apscheduler, then task_scheduler).
    """
    data = read_last_run()
    keys = [scheduler_type] if scheduler_type and scheduler_type in _SCHEDULER_TYPES else list(_SCHEDULER_TYPES)
    lines: list[str] = []
    for key in keys:
        section = data.get(key, {})
        runs: list[dict] = section.get("last_5_runs", [])
        if not runs:
            lines.append(f"**{key}**: no drift data yet (run 5 cycles to populate).\n")
            continue
        lines.append(f"**{key}** (last {len(runs)} runs)\n")
        lines.append("| Cycle | Expected | Actual | Drift (s) |")
        lines.append("|-------|----------|--------|-----------|")
        for i, r in enumerate(runs, 1):
            exp = r.get("expected_fire_at", "")
            act = r.get("actual_fire_at", "")
            drift = r.get("drift_seconds", "")
            lines.append(f"| {i} | {exp} | {act} | {drift} |")
        lines.append("")
    return "\n".join(lines).strip()


if __name__ == "__main__":
    if str(_AGENTS_DIR.parent) not in sys.path:
        sys.path.insert(0, str(_AGENTS_DIR.parent))
    argv = sys.argv[1:]
    if argv and argv[0] == "--drift-table":
        sched = argv[1] if len(argv) > 1 and argv[1] in _SCHEDULER_TYPES else None
        print(format_drift_table(sched))  # noqa: T201
    else:
        out = read_last_run()
        print(json.dumps(out, indent=2))  # noqa: T201
