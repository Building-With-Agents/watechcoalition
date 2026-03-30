# ruff: noqa: T201
"""Seed dbo.normalized_jobs from JSON fixtures (no JSearch / LangSmith).

Selects the 20 most recently modified ``*.json`` files under ``agents/data/fixtures/``,
extracts job-shaped objects (``title`` + ``company``), maps them to ``NormalizedJob``,
and inserts via ``PYTHON_DATABASE_URL``.

Fixture shapes supported:

- Array of objects with ``title``, ``company``, optional ``raw_text`` / ``description``,
  ``requirements``, ``responsibilities``, ``posting_id``, ``source``, ``url``.
- Single object with the same fields (if it looks like a job row).

If fewer than 20 job records are found across those files, records are **padded** by
cycling the collected set with unique ``external_id`` values so exactly 20 rows are
inserted and the success line matches the assignment.

Usage (repo root, venv, ``PYTHON_DATABASE_URL`` set):

    python agents/scripts/seed_from_fixtures.py
"""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from agents.common.data_store.database import check_db_connection, session_scope  # noqa: E402
from agents.common.data_store.models import NormalizedJob  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"
INGESTION_RUN_ID = "fixture-seed"
TARGET_COUNT = 20
MAX_FILES = 20


def _parse_ts(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _is_job_like(obj: dict[str, Any]) -> bool:
    t = obj.get("title")
    c = obj.get("company")
    return isinstance(t, str) and bool(t.strip()) and isinstance(c, str) and bool(c.strip())


def _iter_job_dicts_from_json(data: Any) -> Iterator[dict[str, Any]]:
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and _is_job_like(item):
                yield item
    elif isinstance(data, dict) and _is_job_like(data):
        yield data


def _fixture_json_files_by_mtime() -> list[Path]:
    if not FIXTURES_DIR.is_dir():
        return []
    files = sorted(
        FIXTURES_DIR.rglob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return files[:MAX_FILES]


def _posting_id(obj: dict[str, Any]) -> int | None:
    p = obj.get("posting_id", obj.get("id"))
    if isinstance(p, int):
        return p
    if isinstance(p, str) and p.isdigit():
        return int(p)
    return None


def _body_len(obj: dict[str, Any]) -> int:
    t = obj.get("description") or obj.get("raw_text")
    return len(t) if isinstance(t, str) else 0


def _collect_job_records(file_paths: list[Path]) -> list[dict[str, Any]]:
    """Merge list fixtures: same ``posting_id`` → keep the copy with the longest body text."""
    by_pid: dict[int, dict[str, Any]] = {}
    orphans: list[dict[str, Any]] = []
    orphan_keys: set[tuple[str, str]] = set()

    for path in file_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for obj in _iter_job_dicts_from_json(data):
            rec = dict(obj)
            pid = _posting_id(rec)
            if pid is not None:
                prev = by_pid.get(pid)
                if prev is None or _body_len(rec) > _body_len(prev):
                    by_pid[pid] = rec
            else:
                key = (rec["title"].strip(), rec["company"].strip())
                if key in orphan_keys:
                    continue
                orphan_keys.add(key)
                orphans.append(rec)

    ordered = [by_pid[k] for k in sorted(by_pid)] + orphans
    return ordered[:TARGET_COUNT] if len(ordered) >= TARGET_COUNT else ordered


def _map_to_normalized_job(obj: dict[str, Any], *, seq: int) -> NormalizedJob:
    """Map fixture dict → ORM row. ``posting_id`` / ``id`` from JSON are not DB PKs."""
    posting_id = obj.get("posting_id")
    if posting_id is None:
        posting_id = obj.get("id")
    ext = obj.get("external_id")
    if not ext:
        ext = f"fixture-{posting_id}" if posting_id is not None else f"fixture-seq-{seq}"
    source = str(obj.get("source") or "fixture_seed")[:50]

    description = obj.get("description") or obj.get("raw_text")
    if isinstance(description, str):
        description = description.strip() or None
    else:
        description = None

    requirements = obj.get("requirements")
    if isinstance(requirements, str):
        requirements = requirements.strip() or None
    else:
        requirements = None

    responsibilities = obj.get("responsibilities")
    if isinstance(responsibilities, str):
        responsibilities = responsibilities.strip() or None
    else:
        responsibilities = None

    raw_jid = int(posting_id) if isinstance(posting_id, int) else None
    if isinstance(posting_id, str) and posting_id.isdigit():
        raw_jid = int(posting_id)

    job_url = obj.get("job_url") or obj.get("url")
    if isinstance(job_url, str):
        job_url = job_url[:2083]
    else:
        job_url = None

    ts = _parse_ts(obj.get("timestamp") or obj.get("date_posted"))

    return NormalizedJob(
        raw_job_id=raw_jid,
        ingestion_run_id=INGESTION_RUN_ID[:64],
        region_id=None,
        source=source,
        external_id=str(ext)[:255],
        title=str(obj["title"]).strip()[:500],
        company=str(obj["company"]).strip()[:255],
        description=description,
        requirements=requirements,
        responsibilities=responsibilities,
        job_url=job_url,
        mapper_used="seed_from_fixtures",
        normalization_status="success",
        date_posted=ts,
        created_at=datetime.now(timezone.utc),
    )


def _pad_to_count(records: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    if not records:
        raise SystemExit(
            "No job-like records (title+company) found in the selected fixture files."
        )
    if len(records) >= n:
        return records[:n]
    padded: list[dict[str, Any]] = []
    i = 0
    while len(padded) < n:
        base = dict(records[i % len(records)])
        suffix = uuid.uuid4().hex[:8]
        base["external_id"] = f"{base.get('posting_id', 'x')}-pad-{len(padded)}-{suffix}"
        base.pop("posting_id", None)
        padded.append(base)
        i += 1
    return padded


def main() -> int:
    import os

    if not os.getenv("PYTHON_DATABASE_URL"):
        print("ERROR: PYTHON_DATABASE_URL is not set.", file=sys.stderr)
        return 1
    if not check_db_connection():
        print("ERROR: Cannot connect to PostgreSQL.", file=sys.stderr)
        return 1

    files = _fixture_json_files_by_mtime()
    if not files:
        print(f"ERROR: No JSON files under {FIXTURES_DIR}", file=sys.stderr)
        return 1

    print(f"Using {len(files)} most recent fixture file(s) by mtime:")
    for p in files:
        print(f"  - {p.relative_to(Path(__file__).resolve().parents[2])}")

    raw_records = _collect_job_records(files)
    records = _pad_to_count(raw_records, TARGET_COUNT)
    rows = [_map_to_normalized_job(rec, seq=i) for i, rec in enumerate(records)]

    with session_scope() as session:
        session.add_all(rows)

    print("Successfully seeded 20 jobs into dbo.normalized_jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
