# ruff: noqa: T201
"""Inspect Week 5 JSONB columns on dbo.extracted_intelligence.

This repo does **not** use a ``job_extractions`` table. Skills / tools / tasks /
responsibilities / context are stored on **dbo.extracted_intelligence**
(columns: ``tasks``, ``responsibilities``, ``context`` — the event payload may
say ``context_signals`` but the DB column name is ``context``).

Usage (repo root, venv activated, ``PYTHON_DATABASE_URL`` set):

    python agents/scripts/inspect_extracted_intelligence_week5.py
    python agents/scripts/inspect_extracted_intelligence_week5.py --limit 5 --summary-only

Why ``pipeline_runner.py`` might show empty Week 5 fields
---------------------------------------------------------
``pipeline_runner`` only calls ``extract_context`` / ``extract_tasks`` /
``extract_responsibilities`` **after normalization** for **logging**
(``extraction_stubs_result``). It does **not** write to PostgreSQL.

Rows in ``extracted_intelligence`` are created when **SkillsExtractionAgent**
runs (``process`` → ``SQLAlchemyExtractionStore.save``), which requires:

- ``PYTHON_DATABASE_URL`` set and ``check_db_connection()`` true
- Work items with a non-null ``normalized_job_id`` (batch/inline load from DB)
- The agent actually reaching the save path (not fixture-only fallback with no DB rows)

If you only ran the walking skeleton without DB-backed normalized jobs, the
store will skip saves (``normalized_job_id is None``) or you may have no rows.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from sqlalchemy import select  # noqa: E402

from agents.common.data_store.database import check_db_connection, session_scope  # noqa: E402
from agents.common.data_store.models import ExtractedIntelligence  # noqa: E402


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, list):
        return len(value) == 0
    if isinstance(value, dict):
        return len(value) == 0
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of most recent rows by extracted_at (default: 20)",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print counts only, not full JSON blobs",
    )
    args = parser.parse_args()

    if not check_db_connection():
        print("ERROR: Database unreachable (check PYTHON_DATABASE_URL).", file=sys.stderr)
        return 1

    with session_scope() as session:
        stmt = select(ExtractedIntelligence).order_by(ExtractedIntelligence.extracted_at.desc()).limit(args.limit)
        rows = list(session.scalars(stmt).all())

    if not rows:
        print("No rows in dbo.extracted_intelligence.")
        print(
            "\nHint: Run SkillsExtractionAgent against events that load NormalizedJob rows "
            "with IDs; pipeline_runner stub logging does not insert here."
        )
        return 0

    empty_tasks = 0
    empty_resp = 0
    empty_ctx = 0

    for row in rows:
        t_empty = _is_empty(row.tasks)
        r_empty = _is_empty(row.responsibilities)
        c_empty = _is_empty(row.context)
        if t_empty:
            empty_tasks += 1
        if r_empty:
            empty_resp += 1
        if c_empty:
            empty_ctx += 1

    print("=== Summary (most recent by extracted_at) ===")
    print(f"rows_fetched: {len(rows)}")
    print(f"tasks_empty_or_null: {empty_tasks} / {len(rows)}")
    print(f"responsibilities_empty_or_null: {empty_resp} / {len(rows)}")
    print(f"context_empty_or_null (column name `context`, not context_signals): {empty_ctx} / {len(rows)}")
    print()

    if args.summary_only:
        return 0

    for row in rows:
        record = {
            "id": row.id,
            "normalized_job_id": row.normalized_job_id,
            "extracted_at": row.extracted_at.isoformat() if row.extracted_at else None,
            "extraction_version": row.extraction_version,
            "extraction_model": row.extraction_model,
            "extraction_failed": row.extraction_failed,
            "extraction_tokens_used": row.extraction_tokens_used,
            "extraction_cost_usd": row.extraction_cost_usd,
            "tasks": row.tasks,
            "responsibilities": row.responsibilities,
            "context_signals": row.context,
            "skills_count": len(row.skills or []),
            "tools_count": len(row.tools or []),
        }
        print("---")
        print(json.dumps(record, indent=2, default=str))

    if empty_tasks == len(rows) and empty_resp == len(rows) and empty_ctx == len(rows):
        print(
            "\n=== Debug note ===\n"
            "All three Week 5 dimensions are empty. Common causes:\n"
            "1. Rows were written before Week 5 agent changes (re-run extraction).\n"
            "2. SkillsExtractionAgent saw jobs with no description/requirements/"
            "responsibilities text — Pass 2 skips tasks/responsibilities/skills; "
            "context may still be non-empty if title/description matched patterns.\n"
            "3. You only ran pipeline_runner.py — it never calls "
            "SQLAlchemyExtractionStore.save(); run the skills agent on DB-backed batches.\n"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
