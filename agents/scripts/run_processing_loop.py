"""
Processing loop — paced Normalize → Extract → Enrich pipeline.

Picks up pending raw records in FIFO order, processes them through
normalization, skills extraction, and enrichment. Pauses between batches
to respect LLM rate limits. Exits when no pending records remain.

This is Loop 2 of the flywheel pattern (see issue #161):
  Loop 1: batch_ingest.py fills raw_ingested_jobs
  Loop 2: this script processes them at a sustainable pace

Prerequisites:
  - PYTHON_DATABASE_URL set
  - Azure OpenAI keys set (for extraction + enrichment LLM calls)
  - Optional: NORM_BATCH_SIZE env var (default: 50)

Usage (from repo root):
  python agents/scripts/run_processing_loop.py
  python agents/scripts/run_processing_loop.py --batch-size 25 --delay 15
  python agents/scripts/run_processing_loop.py --max-iterations 5
"""

from __future__ import annotations

import argparse
import os
import sys
import time
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


def _count_pending() -> int:
    """Count raw_ingested_jobs with processing_status='pending'."""
    try:
        from agents.common.data_store.database import session_scope
        from agents.common.data_store.models import RawIngestedJob

        with session_scope() as session:
            return session.query(RawIngestedJob).filter(
                RawIngestedJob.processing_status == "pending"
            ).count()
    except Exception as exc:
        log.error("count_pending_failed", error=str(exc))
        return -1


def _count_unextracted() -> int:
    """Count normalized_jobs that don't have an extracted_intelligence row yet."""
    try:
        from agents.common.data_store.database import session_scope
        from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob

        with session_scope() as session:
            return (
                session.query(NormalizedJob)
                .outerjoin(
                    ExtractedIntelligence,
                    NormalizedJob.id == ExtractedIntelligence.normalized_job_id,
                )
                .filter(ExtractedIntelligence.id == None)  # noqa: E711
                .count()
            )
    except Exception as exc:
        log.error("count_unextracted_failed", error=str(exc))
        return -1


def _count_enriched() -> int:
    """Count job_postings (enriched output)."""
    try:
        from agents.common.data_store.database import session_scope

        with session_scope() as session:
            from sqlalchemy import text
            row = session.execute(text("SELECT COUNT(*) FROM dbo.job_postings")).scalar()
            return row or 0
    except Exception as exc:
        log.error("count_enriched_failed", error=str(exc))
        return -1


def main() -> None:
    parser = argparse.ArgumentParser(description="Paced processing loop (Norm → Extract → Enrich)")
    parser.add_argument("--batch-size", type=int, default=50, help="Records per iteration (default: 50)")
    parser.add_argument("--delay", type=int, default=10, help="Seconds between iterations (default: 10)")
    parser.add_argument("--max-iterations", type=int, default=0, help="Max iterations (0 = run until empty)")
    parser.add_argument("--dry-run", action="store_true", help="Show pending count without processing")
    args = parser.parse_args()

    # Set batch size for normalization agent
    os.environ["NORM_BATCH_SIZE"] = str(args.batch_size)

    pending = _count_pending()
    enriched = _count_enriched()

    log.info(
        "processing_loop_start",
        pending=pending,
        enriched=enriched,
        batch_size=args.batch_size,
        delay=args.delay,
        max_iterations=args.max_iterations or "unlimited",
    )

    unextracted_preview = _count_unextracted()

    if args.dry_run:
        print(f"\nPending raw: {pending}")
        print(f"Unextracted normalized: {unextracted_preview}")
        print(f"Enriched: {enriched} job postings")
        print(f"Batch size: {args.batch_size}")
        total_work = max(pending, unextracted_preview)
        estimated_iterations = (total_work + args.batch_size - 1) // args.batch_size if total_work > 0 else 0
        print(f"Estimated iterations: {estimated_iterations}")
        print(f"Estimated time: ~{estimated_iterations * (args.delay + 30)}s ({estimated_iterations * (args.delay + 30) // 60} min)")
        return

    unextracted = _count_unextracted()

    if pending <= 0 and unextracted <= 0:
        log.info("nothing_to_process", pending=pending, unextracted=unextracted)
        print("No pending or unextracted records to process.")
        return

    # Late imports — heavy pipeline dependencies
    from agents.common.event_envelope import EventEnvelope
    from agents.enrichment.agent import EnrichmentAgent
    from agents.normalization.agent import NormalizationAgent
    from agents.skills_extraction.agent import SkillsExtractionAgent

    norm_agent = NormalizationAgent()
    extract_agent = SkillsExtractionAgent()
    enrich_agent = EnrichmentAgent()

    iteration = 0
    total_normalized = 0
    total_extracted = 0
    total_enriched_count = 0
    total_errors = 0

    while True:
        iteration += 1
        if args.max_iterations and iteration > args.max_iterations:
            log.info("max_iterations_reached", max=args.max_iterations)
            break

        pending = _count_pending()
        unextracted = _count_unextracted()

        if pending <= 0 and unextracted <= 0:
            log.info(
                "all_records_processed",
                total_normalized=total_normalized,
                total_extracted=total_extracted,
                total_enriched=total_enriched_count,
                total_errors=total_errors,
            )
            break

        log.info(
            "iteration_start",
            iteration=iteration,
            pending_raw=pending,
            unextracted=unextracted,
        )

        trigger = EventEnvelope(
            correlation_id=f"processing-loop-iter-{iteration}",
            agent_id="processing-loop",
            payload={"event_type": "ProcessingTrigger", "batch_id": ""},
        )

        try:
            iteration_start = time.perf_counter()
            # Stage 1: Normalize (may return 0 if all raw are already normalized)
            norm_out = norm_agent.process(trigger)
            norm_count = 0
            if norm_out is not None:
                norm_count = norm_out.payload.get("normalized_count", 0)
                quarantined = norm_out.payload.get("quarantined_count", 0)
                if norm_count > 0 or quarantined > 0:
                    log.info("normalized", count=norm_count, quarantined=quarantined, iteration=iteration)
                total_normalized += norm_count

            # Stage 2: Extract skills (FIFO — finds unextracted records itself)
            extract_event = norm_out or trigger
            extract_start = time.perf_counter()
            extract_out = extract_agent.process(extract_event)
            extract_duration_ms = int((time.perf_counter() - extract_start) * 1000)
            extract_count = 0
            if extract_out is not None:
                records = extract_out.payload.get("records", [])
                extract_count = len(records) if isinstance(records, list) else 0
                log.info(
                    "extracted",
                    count=extract_count,
                    iteration=iteration,
                    extraction_duration_ms=extract_duration_ms,
                )
                total_extracted += extract_count

            # Stage 3: Enrich (processes extraction output records)
            if extract_out is not None and extract_count > 0:
                enrich_out = enrich_agent.process(extract_out)
                enriched_count = 0
                if enrich_out is not None:
                    enriched_count = enrich_out.payload.get("enriched_count", 0)
                    log.info("enriched", count=enriched_count, iteration=iteration)
                    total_enriched_count += enriched_count

            enriched_total = _count_enriched()
            remaining_raw = _count_pending()
            remaining_unextracted = _count_unextracted()
            iteration_wall_clock_ms = int((time.perf_counter() - iteration_start) * 1000)

            log.info(
                "iteration_complete",
                iteration=iteration,
                norm_batch=norm_count,
                extract_batch=extract_count,
                extraction_duration_ms=extract_duration_ms,
                iteration_wall_clock_ms=iteration_wall_clock_ms,
                total_enriched=enriched_total,
                remaining_raw=remaining_raw,
                remaining_unextracted=remaining_unextracted,
            )

            if extract_count == 0 and norm_count == 0:
                log.info("no_progress", iteration=iteration)
                break

        except Exception as exc:
            log.error("iteration_failed", iteration=iteration, error=str(exc))
            total_errors += 1

        log.info("rate_limit_pause", seconds=args.delay)
        time.sleep(args.delay)

    enriched_final = _count_enriched()
    print("\nProcessing complete.")
    print(f"  Iterations: {iteration}")
    print(f"  Normalized: {total_normalized}")
    print(f"  Extracted: {total_extracted}")
    print(f"  Enriched: {total_enriched_count}")
    print(f"  Errors: {total_errors}")
    print(f"  Total enriched job postings: {enriched_final}")


if __name__ == "__main__":
    main()
