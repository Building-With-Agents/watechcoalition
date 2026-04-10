"""
Bounded JSearch ingest + description coverage report for dbo.raw_ingested_jobs.

Stages up to ``--limit`` rows in one ingestion run, then prints how many have a
non-empty ``description`` column (and optional S3 status breakdown).

Prerequisites:
  - JSEARCH_API_KEY, PYTHON_DATABASE_URL in .env

Optional env (JSearch pagination — see ``jsearch_adapter``):
  - ``JSEARCH_MAX_PAGES`` — max ``/search`` pages per run (default 10, cap 50).
  - ``BATCH_SIZE`` — desired volume; page count is ``min(ceil(BATCH_SIZE/10), JSEARCH_MAX_PAGES)``.
  Example for up to ~300 listings before dedup: ``JSEARCH_MAX_PAGES=30`` and ``BATCH_SIZE=300``.

Usage (from repo root):
  python agents/scripts/ingest_description_sample.py --limit 50
  python -m agents.scripts.ingest_description_sample --limit 50 --query "data engineer"
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Path bootstrap
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

import structlog  # noqa: E402

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()


@dataclass(frozen=True)
class DescriptionCoverage:
    """Counts for one ``ingestion_run_id`` on ``dbo.raw_ingested_jobs``."""

    total_staged: int
    with_non_empty_description: int
    pending: int
    awaiting_description: int

    @property
    def pct_with_description(self) -> float:
        if self.total_staged <= 0:
            return 0.0
        return 100.0 * self.with_non_empty_description / self.total_staged


def build_region_config(
    *,
    region_id: str,
    query_location: str,
    keywords: list[str],
) -> dict:
    """Region dict compatible with ``IngestionAgent.process`` / ``RegionConfig``."""
    return {
        "region_id": region_id,
        "display_name": region_id,
        "query_location": query_location,
        "radius_miles": 9999,
        "states": [],
        "countries": ["US"],
        "sources": ["jsearch"],
        "role_categories": [],
        "keywords": keywords,
    }


def query_description_coverage(session, batch_id: str) -> DescriptionCoverage:
    """Compute coverage for rows staged under ``ingestion_run_id == batch_id``."""
    from agents.common.data_store.models import RawIngestedJob

    rows = (
        session.query(RawIngestedJob)
        .filter(RawIngestedJob.ingestion_run_id == batch_id)
        .all()
    )
    total = len(rows)
    with_desc = sum(1 for r in rows if (r.description or "").strip() != "")
    pending = sum(1 for r in rows if (r.processing_status or "") == "pending")
    awaiting = sum(1 for r in rows if (r.processing_status or "") == "awaiting_description")
    return DescriptionCoverage(
        total_staged=total,
        with_non_empty_description=with_desc,
        pending=pending,
        awaiting_description=awaiting,
    )


def run_ingest_and_report(
    *,
    limit: int,
    region_id: str,
    query_location: str,
    keywords: list[str],
) -> tuple[int, DescriptionCoverage]:
    """Run one JSearch ingestion capped to ``limit``; return exit code and coverage.

    Returns ``(0, coverage)`` on success, ``(1, coverage_or_placeholder)`` on failure.
    """
    from agents.common.data_store.database import session_scope
    from agents.common.event_envelope import EventEnvelope
    from agents.ingestion.agent import IngestionAgent

    region_config = build_region_config(
        region_id=region_id,
        query_location=query_location,
        keywords=keywords,
    )
    event = EventEnvelope(
        correlation_id=f"ingest-description-sample-{region_id}",
        agent_id="ingest-description-sample",
        payload={
            "region_config": region_config,
            "source": "jsearch",
            "limit": limit,
        },
    )
    agent = IngestionAgent()
    out = agent.process(event)
    payload = out.payload
    et = payload.get("event_type")
    if et == "SourceFailure":
        log.error("ingest_source_failure", error=payload.get("error", ""))
        return 1, DescriptionCoverage(0, 0, 0, 0)
    if et != "IngestBatch":
        log.error("ingest_unexpected_event", event_type=et, payload_keys=list(payload.keys()))
        return 1, DescriptionCoverage(0, 0, 0, 0)

    batch_id = str(payload.get("batch_id") or "")
    if not batch_id:
        log.error("ingest_missing_batch_id")
        return 1, DescriptionCoverage(0, 0, 0, 0)

    try:
        from agents.common.data_store.database import check_db_connection

        if not check_db_connection():
            log.error("db_unavailable_for_coverage")
            return 1, DescriptionCoverage(0, 0, 0, 0)

        with session_scope() as session:
            coverage = query_description_coverage(session, batch_id)
    except Exception as exc:
        log.error("coverage_query_failed", error=str(exc))
        return 1, DescriptionCoverage(0, 0, 0, 0)

    return 0, coverage


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run bounded JSearch ingest and print raw description coverage",
    )
    parser.add_argument("--limit", type=int, default=50, help="Max records to fetch/stage (default 50)")
    parser.add_argument(
        "--query",
        default="software engineer",
        help="Primary keyword passed to JSearch (default: software engineer)",
    )
    parser.add_argument("--location", default="United States", help="query_location for region (default: United States)")
    parser.add_argument(
        "--region-id",
        default="sample-description-check",
        help="region_id for this run (default: sample-description-check)",
    )
    parser.add_argument(
        "--no-sync-sequences",
        action="store_true",
        help="Skip PostgreSQL SERIAL/IDENTITY resync (see sync_agent_sequences.py / run_migrations)",
    )
    args = parser.parse_args()

    if args.limit <= 0:
        log.error("limit_must_be_positive", limit=args.limit)
        sys.exit(1)

    if not args.no_sync_sequences:
        try:
            from agents.common.data_store.migrations import sync_postgresql_agent_sequences

            sync_postgresql_agent_sequences()
            log.info("postgresql_agent_sequences_synced")
        except RuntimeError as exc:
            log.error("database_not_configured", error=str(exc))
            sys.exit(1)
        except Exception as exc:
            log.warning("postgresql_sequence_sync_failed", error=str(exc))

    api_key = os.getenv("JSEARCH_API_KEY", "").strip()
    if not api_key:
        log.error("missing_jsearch_api_key")
        sys.exit(1)

    code, cov = run_ingest_and_report(
        limit=args.limit,
        region_id=args.region_id,
        query_location=args.location,
        keywords=[args.query],
    )
    if code != 0:
        sys.exit(code)

    pct = cov.pct_with_description
    print(  # noqa: T201
        f"Description coverage: {cov.with_non_empty_description}/{cov.total_staged} ({pct:.1f}%) "
        f"[pending={cov.pending}, awaiting_description={cov.awaiting_description}]"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
