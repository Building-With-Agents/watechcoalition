"""Demo: fetch N unique jobs, append one exact duplicate, run ingestion dedup.

This exercises **in-batch ingestion deduplication** (content fingerprint +
source priority), not fuzzy dedup at enrichment. With an exact copy of the first
record appended, you should see ``total_input == unique + 1``,
``duplicates_skipped >= 1``, and ``new_records == unique`` (assuming that job
was not already in ``raw_ingested_jobs`` from a prior run).

Usage (repo root, venv active, ``JSEARCH_API_KEY`` for jsearch)::

    py -3.11 -m agents.scripts.ingest_duplicate_demo
    py -3.11 -m agents.scripts.ingest_duplicate_demo --unique 9 --stage --migrate

``--stage`` writes to ``dbo.raw_ingested_jobs`` and ``dbo.job_ingestion_runs``
like the Ingestion Agent after dedup.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
load_dotenv(_REPO_ROOT / ".env")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch N jobs + 1 duplicate; show ingestion dedup counts.")
    p.add_argument("--source", choices=["jsearch", "crawl4ai"], default="jsearch")
    p.add_argument(
        "--unique",
        type=int,
        default=9,
        help="Number of distinct jobs to fetch before appending one duplicate (default: 9).",
    )
    p.add_argument("--query", default="software engineer")
    p.add_argument("--location", default="Washington state")
    p.add_argument("--region-id", default="duplicate-demo")
    p.add_argument(
        "--stage",
        action="store_true",
        help="Persist deduped rows to raw_ingested_jobs and record job_ingestion_runs.",
    )
    p.add_argument("--migrate", action="store_true", help="Run SQLAlchemy migrations before any DB access.")
    return p.parse_args()


async def _fetch_records(source: str, region) -> list:
    from agents.ingestion.sources import get_adapter

    adapter = get_adapter(source)
    return await adapter.fetch(region)


def main() -> None:
    args = _parse_args()

    if args.migrate:
        from agents.common.data_store.database import get_engine
        from agents.common.data_store.migrations import run_migrations

        run_migrations(get_engine())

    from agents.common.data_store.database import session_scope
    from agents.common.data_store.models import JobIngestionRun, RawIngestedJob
    from agents.common.types import RawJobRecord, RegionConfig
    from agents.ingestion.deduplicator import deduplicate_batch

    region = RegionConfig(
        region_id=args.region_id,
        display_name="Duplicate demo",
        query_location=args.location,
        radius_miles=50,
        states=["WA"],
        countries=["US"],
        sources=[args.source],
        role_categories=[],
        keywords=[args.query],
    )

    fetched = asyncio.run(_fetch_records(args.source, region))
    if not fetched:
        print("error: no records returned from source (check API keys / network)", file=sys.stderr)
        sys.exit(1)

    n = min(args.unique, len(fetched))
    unique_recs: list[RawJobRecord] = fetched[:n]
    duplicate = unique_recs[0].model_copy(deep=True)
    batch: list[RawJobRecord] = unique_recs + [duplicate]

    record_dicts = [r.model_dump() for r in batch]
    with session_scope() as session:
        dedup_result = deduplicate_batch(record_dicts, session)

    print("ingest_duplicate_demo")
    print(f"  source:          {args.source}")
    print(f"  unique fetched:  {len(unique_recs)} (requested up to {args.unique})")
    print(f"  batch size:      {len(batch)}  (= unique + 1 duplicate of first job)")
    print(f"  duplicates_skipped: {dedup_result.duplicates_skipped}")
    print(f"  new_records:      {len(dedup_result.new_records)}")
    print(f"  source_priority_resolved: {dedup_result.source_priority_resolved}")

    if dedup_result.duplicates_skipped < 1:
        print(
            "  note: expected at least 1 in-batch skip; if 0, the duplicate may differ "
            "in fingerprint fields or cross-batch dedup removed rows.",
            file=sys.stderr,
        )

    if not args.stage:
        print("  (--stage not set; no rows written)")
        return

    run_id = str(uuid.uuid4())
    new_models = [RawJobRecord(**r) for r in dedup_result.new_records]
    staged_count = 0
    error_count = 0

    with session_scope() as session:
        session.add(
            JobIngestionRun(
                run_id=run_id,
                region_id=args.region_id,
                source=args.source,
                status="running",
            )
        )
        session.flush()

        for record in new_models:
            try:
                session.add(
                    RawIngestedJob(
                        ingestion_run_id=run_id,
                        region_id=args.region_id,
                        source=record.source,
                        external_id=record.external_id,
                        raw_payload_hash=record.raw_payload_hash,
                        title=record.title,
                        company=record.company,
                        description=record.description or None,
                        city=record.city,
                        state=record.state,
                        country=record.country,
                        is_remote=record.is_remote,
                        job_url=record.job_url,
                        source_url=record.source_url or None,
                        date_posted=str(record.date_posted) if record.date_posted else None,
                        employment_type=record.employment_type,
                        experience_level=record.experience_level,
                        salary_raw=record.salary_raw,
                        salary_min=record.salary_min,
                        salary_max=record.salary_max,
                        salary_currency=record.salary_currency,
                        salary_period=record.salary_period,
                        raw_payload=record.raw_payload,
                        processing_status="pending",
                    )
                )
                session.flush()
                staged_count += 1
            except Exception as exc:
                error_count += 1
                print(f"  stage error: {record.external_id}: {exc}", file=sys.stderr)

        run = session.query(JobIngestionRun).filter_by(run_id=run_id).first()
        if run:
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.total_fetched = len(batch)
            run.staged_count = staged_count
            run.dedup_count = dedup_result.duplicates_skipped
            run.error_count = error_count

    print(f"  staged run_id:   {run_id}")
    print(f"  staged_count:    {staged_count}")
    print(f"  error_count:     {error_count}")


if __name__ == "__main__":
    main()
