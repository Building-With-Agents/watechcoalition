"""
JSearch detail backfill — moves ``awaiting_description`` rows to ``pending`` when
detail text passes the substantive gate (see ``agents.ingestion.description_gating``).

DB-polled worker with ``FOR UPDATE SKIP LOCKED`` on PostgreSQL. No Celery.

Usage (repo root):
  python agents/scripts/run_jsearch_description_backfill.py --dry-run
  python agents/scripts/run_jsearch_description_backfill.py --batch-size 25

Live HTTP requires ``JSEARCH_API_KEY`` and ``JSEARCH_DETAIL_FETCH_ENABLED=1``.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

import httpx  # noqa: E402
import structlog  # noqa: E402
from sqlalchemy import func, or_, select  # noqa: E402

from agents.common.data_store.database import get_engine, session_scope  # noqa: E402
from agents.common.data_store.models import RawIngestedJob  # noqa: E402
from agents.ingestion.description_gating import (  # noqa: E402
    description_gate_reason,
    is_substantive_description,
)
from agents.ingestion.sources.jsearch_detail_client import (  # noqa: E402
    extract_description_from_detail_job,
    fetch_job_detail,
)

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

DETAIL_FAILED_TERMINAL = "detail_failed_terminal"


def _detail_fetch_enabled() -> bool:
    return os.getenv("JSEARCH_DETAIL_FETCH_ENABLED", "").strip().lower() in ("1", "true", "yes")


def _max_attempts() -> int:
    raw = os.getenv("JSEARCH_DETAIL_MAX_ATTEMPTS", "3")
    try:
        return max(1, min(int(raw), 50))
    except (TypeError, ValueError):
        return 3


def _max_rows_per_run() -> int | None:
    raw = os.getenv("JSEARCH_DETAIL_MAX_ROWS_PER_RUN", "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
        return max(1, n) if n > 0 else None
    except (TypeError, ValueError):
        return None


def claim_jsearch_awaiting_batch(
    session,
    *,
    batch_size: int,
    max_attempts: int,
    dialect_name: str,
) -> list[RawIngestedJob]:
    """Lock up to ``batch_size`` rows eligible for detail fetch."""
    stmt = (
        select(RawIngestedJob)
        .where(
            RawIngestedJob.source == "jsearch",
            RawIngestedJob.processing_status == "awaiting_description",
            RawIngestedJob.detail_fetch_attempts < max_attempts,
            or_(
                RawIngestedJob.detail_fetch_status.is_(None),
                RawIngestedJob.detail_fetch_status != DETAIL_FAILED_TERMINAL,
            ),
        )
        .order_by(RawIngestedJob.id)
        .limit(batch_size)
    )
    stmt = (
        stmt.with_for_update(skip_locked=True)
        if dialect_name == "postgresql"
        else stmt.with_for_update()
    )

    return list(session.scalars(stmt).all())


def count_eligible_jsearch_awaiting(session, *, max_attempts: int) -> int:
    q = select(func.count()).select_from(RawIngestedJob).where(
        RawIngestedJob.source == "jsearch",
        RawIngestedJob.processing_status == "awaiting_description",
        RawIngestedJob.detail_fetch_attempts < max_attempts,
        or_(
            RawIngestedJob.detail_fetch_status.is_(None),
            RawIngestedJob.detail_fetch_status != DETAIL_FAILED_TERMINAL,
        ),
    )
    return int(session.execute(q).scalar() or 0)


def _apply_detail_job_to_row(
    row: RawIngestedJob,
    job: dict,
    *,
    from_dedup: bool,
) -> dict[str, int]:
    """Mutate row from a JSearch job dict; return metric deltas."""
    metrics = {
        "jsearch_detail_success_total": 0,
        "description_thin_after_detail_total": 0,
    }
    row.description_fetched_at = datetime.now(timezone.utc)
    desc = extract_description_from_detail_job(job)
    merged_payload: dict = (
        {**row.raw_payload, **job} if isinstance(row.raw_payload, dict) else dict(job)
    )

    row.raw_payload = merged_payload
    row.description = desc or None
    row.description_fetched_at = datetime.now(timezone.utc)

    if is_substantive_description(desc):
        row.processing_status = "pending"
        row.description_source = "jsearch_detail"
        row.detail_last_error = None
        metrics["jsearch_detail_success_total"] = 1
        log.info(
            "description_backfill_promoted",
            gate_reason=description_gate_reason(desc),
            external_id_len=len(row.external_id or ""),
            from_dedup=from_dedup,
        )
    else:
        row.detail_last_error = description_gate_reason(desc)
        metrics["description_thin_after_detail_total"] = 1
        if row.detail_fetch_attempts >= _max_attempts():
            row.detail_fetch_status = DETAIL_FAILED_TERMINAL
        log.info(
            "description_still_thin_after_detail",
            gate_reason=description_gate_reason(desc),
            external_id_len=len(row.external_id or ""),
            from_dedup=from_dedup,
        )
    return metrics


async def _process_one_row(
    client: httpx.AsyncClient,
    row: RawIngestedJob,
    *,
    api_key: str,
    dry_run: bool,
    jobs_by_external_id: dict[str, dict],
) -> dict[str, int]:
    """Update ``row`` in memory + return counter deltas for logging."""
    metrics = {
        "jsearch_detail_requests_total": 0,
        "jsearch_detail_success_total": 0,
        "jsearch_detail_empty_body_total": 0,
        "description_thin_after_detail_total": 0,
        "detail_dedup_skips_total": 0,
    }
    eid = (row.external_id or "").strip()
    if not eid:
        row.detail_fetch_attempts += 1
        row.detail_last_error = "missing_external_id"
        row.description_fetched_at = datetime.now(timezone.utc)
        if row.detail_fetch_attempts >= _max_attempts():
            row.detail_fetch_status = DETAIL_FAILED_TERMINAL
        return metrics

    if eid in jobs_by_external_id:
        metrics["detail_dedup_skips_total"] = 1
        log.info("detail_dedup_skips_total", external_id_len=len(eid))
        row.detail_fetch_attempts += 1
        cached = jobs_by_external_id[eid]
        m2 = _apply_detail_job_to_row(row, cached, from_dedup=True)
        for k, v in m2.items():
            metrics[k] += v
        return metrics

    if dry_run:
        metrics["jsearch_detail_requests_total"] = 1
        log.info("jsearch_detail_dry_run_would_fetch", external_id_len=len(eid))
        return metrics

    metrics["jsearch_detail_requests_total"] = 1
    job, err, _status = await fetch_job_detail(client, job_id=eid, api_key=api_key)
    row.detail_fetch_attempts += 1

    if err or not job:
        row.detail_last_error = err or "unknown"
        row.description_fetched_at = datetime.now(timezone.utc)
        if err in (
            "http_404",
            "http_400",
            "http_401",
            "http_403",
            "no_job_in_payload",
        ) or row.detail_fetch_attempts >= _max_attempts():
            row.detail_fetch_status = DETAIL_FAILED_TERMINAL
        return metrics

    jobs_by_external_id[eid] = job
    desc = extract_description_from_detail_job(job)
    if not desc.strip():
        row.detail_last_error = "empty_description"
        row.description_fetched_at = datetime.now(timezone.utc)
        metrics["jsearch_detail_empty_body_total"] = 1
        if row.detail_fetch_attempts >= _max_attempts():
            row.detail_fetch_status = DETAIL_FAILED_TERMINAL
        return metrics

    m2 = _apply_detail_job_to_row(row, job, from_dedup=False)
    for k, v in m2.items():
        metrics[k] += v
    return metrics


async def run_backfill_batch(
    rows: list[RawIngestedJob],
    *,
    dry_run: bool,
    api_key: str,
) -> None:
    jobs_by_external_id: dict[str, dict] = {}
    totals = {
        "jsearch_detail_requests_total": 0,
        "jsearch_detail_success_total": 0,
        "jsearch_detail_empty_body_total": 0,
        "description_thin_after_detail_total": 0,
        "detail_dedup_skips_total": 0,
    }
    timeout = float(os.getenv("JSEARCH_DETAIL_TIMEOUT_SECONDS", "30") or "30")
    async with httpx.AsyncClient(timeout=timeout) as client:
        for row in rows:
            m = await _process_one_row(
                client,
                row,
                api_key=api_key,
                dry_run=dry_run,
                jobs_by_external_id=jobs_by_external_id,
            )
            for k, v in m.items():
                totals[k] += v

    promoted = sum(
        1
        for r in rows
        if r.processing_status == "pending" and (r.description_source or "") == "jsearch_detail"
    )
    fill_den = len(rows) or 1
    fill_rate = promoted / fill_den
    log.info(
        "jsearch_description_backfill_batch_complete",
        rows=len(rows),
        dry_run=dry_run,
        description_fill_rate=round(fill_rate, 4),
        **totals,
        rows_promoted_pending=promoted,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="JSearch detail backfill for raw_ingested_jobs.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read-only sample + unique external_id count; no locks, no HTTP.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Rows to claim per transaction (default 25).",
    )
    args = parser.parse_args()
    batch_size = max(1, args.batch_size)
    dry_run = args.dry_run

    if not dry_run and not _detail_fetch_enabled():
        log.error(
            "jsearch_detail_fetch_disabled",
            hint="Set JSEARCH_DETAIL_FETCH_ENABLED=1 or use --dry-run",
        )
        return 1

    api_key = os.getenv("JSEARCH_API_KEY", "").strip()
    if not dry_run and not api_key:
        log.error("jsearch_detail_missing_api_key")
        return 1

    engine = get_engine()
    max_attempts = _max_attempts()
    cap = _max_rows_per_run()

    if dry_run:
        with session_scope() as session:
            eligible = count_eligible_jsearch_awaiting(session, max_attempts=max_attempts)
            log.info(
                "jsearch_description_backfill_eligible_total",
                eligible=eligible,
                dry_run=True,
            )
            limit = min(batch_size, eligible)
            if cap is not None:
                limit = min(limit, cap)
            if limit <= 0:
                log.info(
                    "jsearch_detail_dry_run_summary",
                    would_fetch_approx=0,
                    rows_sampled=0,
                    batch_size=batch_size,
                    eligible=eligible,
                )
                return 0
            stmt = (
                select(RawIngestedJob.external_id)
                .where(
                    RawIngestedJob.source == "jsearch",
                    RawIngestedJob.processing_status == "awaiting_description",
                    RawIngestedJob.detail_fetch_attempts < max_attempts,
                    or_(
                        RawIngestedJob.detail_fetch_status.is_(None),
                        RawIngestedJob.detail_fetch_status != DETAIL_FAILED_TERMINAL,
                    ),
                )
                .order_by(RawIngestedJob.id)
                .limit(limit)
            )
            eids = list(session.scalars(stmt).all())
            seen: set[str] = set()
            would_fetch = 0
            for raw_eid in eids:
                e = (raw_eid or "").strip()
                if not e or e in seen:
                    continue
                seen.add(e)
                would_fetch += 1
            log.info(
                "jsearch_detail_dry_run_summary",
                would_fetch_approx=would_fetch,
                rows_sampled=len(eids),
                batch_size=batch_size,
                eligible=eligible,
            )
        return 0

    with session_scope() as session:
        eligible = count_eligible_jsearch_awaiting(session, max_attempts=max_attempts)
        log.info(
            "jsearch_description_backfill_eligible_total",
            eligible=eligible,
            dry_run=False,
        )

        limit = min(batch_size, eligible)
        if cap is not None:
            limit = min(limit, cap)
        if limit <= 0:
            return 0

        rows = claim_jsearch_awaiting_batch(
            session,
            batch_size=limit,
            max_attempts=max_attempts,
            dialect_name=engine.dialect.name,
        )
        if not rows:
            return 0

        asyncio.run(run_backfill_batch(rows, dry_run=False, api_key=api_key))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
