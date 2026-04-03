"""
Processing loop — paced Normalize → Extract → Enrich pipeline.

Picks up pending raw records in FIFO order, processes them through
normalization, skills extraction, and enrichment. Pauses between batches
to respect LLM rate limits. Exits when no pending records remain.

This is Loop 2 of the flywheel pattern (see issue #161):
  Loop 1: batch_ingest_borderplex.py fills raw_ingested_jobs
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


def _count_enriched() -> int:
    """Count job_postings (enriched output)."""
    try:
        from agents.common.data_store.database import session_scope
        from agents.common.data_store.models import JobPosting

        with session_scope() as session:
            return session.query(JobPosting).count()
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

    if args.dry_run:
        print(f"\nPending: {pending} raw records")
        print(f"Enriched: {enriched} job postings")
        print(f"Batch size: {args.batch_size}")
        estimated_iterations = (pending + args.batch_size - 1) // args.batch_size if pending > 0 else 0
        print(f"Estimated iterations: {estimated_iterations}")
        print(f"Estimated time: ~{estimated_iterations * (args.delay + 30)}s ({estimated_iterations * (args.delay + 30) // 60} min)")
        return

    if pending <= 0:
        log.info("no_pending_records")
        print("No pending records to process.")
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
    total_processed = 0
    total_errors = 0

    while True:
        iteration += 1
        if args.max_iterations and iteration > args.max_iterations:
            log.info("max_iterations_reached", max=args.max_iterations)
            break

        pending = _count_pending()
        if pending <= 0:
            log.info("all_records_processed", total_processed=total_processed, total_errors=total_errors)
            break

        log.info(
            "iteration_start",
            iteration=iteration,
            pending=pending,
            batch_size=min(args.batch_size, pending),
        )

        # Build a trigger event (normalization reads from DB, not from payload)
        trigger = EventEnvelope(
            correlation_id=f"processing-loop-iter-{iteration}",
            agent_id="processing-loop",
            payload={"event_type": "ProcessingTrigger", "batch_id": f"loop-{iteration}"},
        )

        try:
            # Stage 1: Normalize
            norm_out = norm_agent.process(trigger)
            if norm_out is None:
                log.error("normalization_returned_none", iteration=iteration)
                total_errors += 1
                time.sleep(args.delay)
                continue

            norm_count = norm_out.payload.get("normalized_count", 0)
            quarantined = norm_out.payload.get("quarantined_count", 0)
            log.info("normalized", count=norm_count, quarantined=quarantined, iteration=iteration)

            if norm_count == 0:
                log.info("nothing_normalized", iteration=iteration)
                time.sleep(args.delay)
                continue

            # Stage 2: Extract skills
            extract_out = extract_agent.process(norm_out)
            if extract_out is None:
                log.error("extraction_returned_none", iteration=iteration)
                total_errors += 1
                time.sleep(args.delay)
                continue

            extract_count = extract_out.payload.get("records_extracted", 0)
            log.info("extracted", count=extract_count, iteration=iteration)

            # Stage 3: Enrich
            enrich_out = enrich_agent.process(extract_out)
            if enrich_out is None:
                log.error("enrichment_returned_none", iteration=iteration)
                total_errors += 1
                time.sleep(args.delay)
                continue

            enriched_count = enrich_out.payload.get("enriched_count", 0)
            log.info("enriched", count=enriched_count, iteration=iteration)

            total_processed += norm_count
            enriched_total = _count_enriched()
            remaining = _count_pending()

            log.info(
                "iteration_complete",
                iteration=iteration,
                batch_processed=norm_count,
                total_processed=total_processed,
                total_enriched=enriched_total,
                remaining=remaining,
            )

        except Exception as exc:
            log.error("iteration_failed", iteration=iteration, error=str(exc))
            total_errors += 1

        if _count_pending() > 0:
            log.info("rate_limit_pause", seconds=args.delay)
            time.sleep(args.delay)

    enriched_final = _count_enriched()
    print("\nProcessing complete.")
    print(f"  Iterations: {iteration}")
    print(f"  Records processed: {total_processed}")
    print(f"  Errors: {total_errors}")
    print(f"  Total enriched job postings: {enriched_final}")


if __name__ == "__main__":
    main()
