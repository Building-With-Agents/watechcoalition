# ruff: noqa: T201
"""Populate dbo.extracted_intelligence from dbo.normalized_jobs via SkillsExtractionAgent.

Uses ``PYTHON_DATABASE_URL`` (load ``.env`` from repo root).

The agent's API is ``process(EventEnvelope)``, not ``process(JobRecord)``. This script
builds ``JobRecord``-equivalent inline payloads (with ``normalized_job_id`` = ``dbo.normalized_jobs.id``)
so ``SQLAlchemyExtractionStore`` persists one row per job.

Usage (repo root, venv activated):

    python agents/scripts/populate_week5_records.py
    python agents/scripts/populate_week5_records.py --limit 20 --sequential
    python agents/scripts/populate_week5_records.py --batch --limit 20
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from sqlalchemy import select  # noqa: E402

from agents.common.data_store.database import check_db_connection, session_scope  # noqa: E402
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob  # noqa: E402
from agents.common.event_envelope import EventEnvelope  # noqa: E402
from agents.common.types import JobRecord  # noqa: E402
from agents.skills_extraction.agent import SkillsExtractionAgent  # noqa: E402


def _normalized_job_to_job_record(row: NormalizedJob) -> JobRecord:
    """Map ORM row → ``JobRecord`` (same fields as ``EventOrDatabaseWorkItemLoader._from_normalized_row``)."""
    return JobRecord(
        raw_job_id=row.raw_job_id or 0,
        ingestion_run_id=row.ingestion_run_id,
        region_id=row.region_id or "",
        source=row.source,
        external_id=row.external_id,
        title=row.title,
        company=row.company,
        description=row.description,
        requirements=row.requirements,
        responsibilities=row.responsibilities,
        job_url=row.job_url,
        city=row.city,
        state_province=row.state_province,
        country=row.country,
        work_arrangement=row.work_arrangement,
        is_remote=row.is_remote,
        date_posted=row.date_posted,
        salary_raw=row.salary_raw,
        salary_min=row.salary_min,
        salary_max=row.salary_max,
        salary_currency=row.salary_currency,
        salary_period=row.salary_period,
        employment_type=row.employment_type,
        experience_level=row.experience_level,
        occupation_code=row.occupation_code,
        mapper_used=row.mapper_used or "",
    )


def _normalized_job_to_inline_payload(row: NormalizedJob) -> dict[str, Any]:
    """Inline dict for ``NormalizationComplete``-style payload (loader sets ``normalized_job_id``)."""
    return {
        "normalized_job_id": row.id,
        "id": row.id,
        "raw_job_id": row.raw_job_id or 0,
        "ingestion_run_id": row.ingestion_run_id,
        "region_id": row.region_id or "",
        "source": row.source,
        "external_id": row.external_id,
        "title": row.title,
        "company": row.company,
        "description": row.description,
        "requirements": row.requirements,
        "responsibilities": row.responsibilities,
        "job_url": row.job_url,
        "employment_type": row.employment_type,
    }


def _fetch_normalized_jobs(limit: int, order: str) -> list[NormalizedJob]:
    with session_scope() as session:
        q = select(NormalizedJob)
        if order == "id_desc":
            q = q.order_by(NormalizedJob.id.desc())
        elif order == "id_asc":
            q = q.order_by(NormalizedJob.id.asc())
        else:
            q = q.order_by(NormalizedJob.created_at.desc())
        rows = list(session.scalars(q.limit(limit)).all())
    return rows


def _build_event(
    *,
    correlation_id: str,
    batch_id: str,
    records: list[dict[str, Any]],
) -> EventEnvelope:
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="normalization-agent",
        payload={
            "event_type": "NormalizationComplete",
            "batch_id": batch_id,
            "normalized_jobs": records,
        },
    )


def _summarize_outcome(out: EventEnvelope) -> str:
    p = out.payload
    return (
        f"skills={p.get('skills_count')}, tools={p.get('tools_count')}, "
        f"tasks={p.get('tasks_count')}, resp={p.get('responsibilities_count')}, "
        f"context={p.get('context_signals_count')}, failed={p.get('failed_count')}, "
        f"cost_usd={p.get('extraction_cost_usd')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--limit", type=int, default=20, help="Rows to pull from normalized_jobs")
    parser.add_argument(
        "--order",
        choices=("id_desc", "id_asc", "created_desc"),
        default="id_desc",
        help="Order when selecting normalized jobs (default: newest id first)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="One agent.process() call for all rows (faster; single taxonomy batch)",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="One process() per row with per-row progress (more API calls)",
    )
    args = parser.parse_args()
    use_batch = args.batch or not args.sequential
    if args.batch and args.sequential:
        print("Use only one of --batch or --sequential; defaulting to --batch.")
        use_batch = True

    if not os.getenv("PYTHON_DATABASE_URL"):
        print("ERROR: PYTHON_DATABASE_URL is not set.", file=sys.stderr)
        return 1
    if not check_db_connection():
        print("ERROR: Cannot connect to PostgreSQL.", file=sys.stderr)
        return 1

    # Allow all fetched rows in one agent run (default cap in agent is 10).
    os.environ["SKILLS_EXTRACTION_MAX_JOBS"] = str(max(args.limit, 1))

    print(f"[1/4] Fetching up to {args.limit} rows from dbo.normalized_jobs ({args.order})...")
    rows = _fetch_normalized_jobs(args.limit, args.order)
    if not rows:
        print("No rows in dbo.normalized_jobs; nothing to do.")
        return 0

    n = len(rows)
    print(f"      Loaded {n} rows: normalized_job_ids={[r.id for r in rows]}")

    print("[2/4] Building JobRecord payloads (normalized_job_id = normalized_jobs.id)...")
    for i, row in enumerate(rows, 1):
        jr = _normalized_job_to_job_record(row)
        print(
            f"      [{i}/{n}] id={row.id} title={jr.title[:50]!r}… "
            f"company={jr.company[:30]!r}…"
        )

    agent = SkillsExtractionAgent()
    batch_id = f"populate-week5-{uuid.uuid4().hex[:8]}"
    correlation = f"populate-week5-{uuid.uuid4()}"

    if use_batch:
        print(
            f"[3/4] Running SkillsExtractionAgent.process() once (batched, batch_id={batch_id})…"
        )
        records = [_normalized_job_to_inline_payload(r) for r in rows]
        event = _build_event(
            correlation_id=correlation,
            batch_id=batch_id,
            records=records,
        )
        out = agent.process(event)
        print(f"      Done. {_summarize_outcome(out)}")
    else:
        print(f"[3/4] Running SkillsExtractionAgent.process() per row ({n} calls)…")
        for i, row in enumerate(rows, 1):
            rec = _normalized_job_to_inline_payload(row)
            ev = _build_event(
                correlation_id=f"{correlation}-{i}",
                batch_id=f"{batch_id}-{i}",
                records=[rec],
            )
            print(f"      [{i}/{n}] extracting normalized_job_id={row.id} …", flush=True)
            out = agent.process(ev)
            print(f"      [{i}/{n}] {_summarize_outcome(out)}")

    print("[4/4] Verifying dbo.extracted_intelligence rows…")
    with session_scope() as session:
        ids = [r.id for r in rows]
        found = 0
        for nid in ids:
            row = session.scalars(
                select(ExtractedIntelligence).where(
                    ExtractedIntelligence.normalized_job_id == nid
                )
            ).first()
            if row:
                found += 1
                print(
                    f"      id={row.id} normalized_job_id={nid} "
                    f"tasks={len(row.tasks or [])} resp={len(row.responsibilities or [])} "
                    f"context={len(row.context or [])}"
                )
            else:
                print(f"      MISSING extraction row for normalized_job_id={nid}", file=sys.stderr)

    print(f"Done. {found}/{n} extracted_intelligence rows present for those normalized_jobs.")
    return 0 if found == n else 2


if __name__ == "__main__":
    raise SystemExit(main())
