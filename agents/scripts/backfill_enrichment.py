"""Backfill quality_score, soc_code, naics_code, employer_profile_id on job_postings.

Iterates job_postings rows missing quality_score, computes quality score,
classifies SOC/NAICS via LLM, and updates in place. Processes in batches
with a delay between records to respect rate limits.

Usage:
    python agents/scripts/backfill_enrichment.py
    python agents/scripts/backfill_enrichment.py --batch-size 25 --delay 5
    python agents/scripts/backfill_enrichment.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

import structlog
from sqlalchemy import text

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

_SELECT_PENDING_SQL = text("""
    SELECT job_posting_id, job_title, job_description, source, external_id
    FROM dbo.job_postings
    WHERE quality_score IS NULL
    ORDER BY job_posting_id
    LIMIT :batch_size
    OFFSET :offset
""")

_UPDATE_SQL = text("""
    UPDATE dbo.job_postings
    SET quality_score = :quality_score,
        soc_code = :soc_code,
        naics_code = :naics_code,
        spam_score = :spam_score
    WHERE job_posting_id = :job_posting_id
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill enrichment columns on job_postings")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--delay", type=int, default=3, help="Seconds between records (LLM rate limit)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-records", type=int, default=0, help="Max records to process (0 = all)")
    args = parser.parse_args()

    from agents.common.data_store.database import session_scope
    from agents.enrichment.agent import _enrichment_soc_llm
    from agents.enrichment.async_bridge import run_coroutine
    from agents.enrichment.classifiers.naics_classifier import classify_naics
    from agents.enrichment.classifiers.quality import score_quality
    from agents.enrichment.classifiers.soc_classifier import classify_soc
    from agents.enrichment.classifiers.spam_preview import score_spam_preview

    # Count total pending
    with session_scope() as s:
        total = s.execute(text("SELECT count(*) FROM dbo.job_postings WHERE quality_score IS NULL")).scalar()

    log.info("backfill_start", total_pending=total, batch_size=args.batch_size, delay=args.delay)
    if args.dry_run:
        print(f"\nPending: {total} job_postings without quality_score")
        print(f"Batch size: {args.batch_size}, delay: {args.delay}s")
        est_time = total * (args.delay + 8)  # ~8s per record for LLM calls
        print(f"Estimated time: ~{est_time // 60} min")
        return

    processed = 0
    updated = 0
    errors = 0
    soc_classified = 0
    naics_classified = 0

    while True:
        if args.max_records and processed >= args.max_records:
            break

        with session_scope() as session:
            rows = (
                session.execute(
                    _SELECT_PENDING_SQL,
                    {
                        "batch_size": args.batch_size,
                        "offset": 0,
                    },
                )
                .mappings()
                .all()
            )

            if not rows:
                break

            for row in rows:
                if args.max_records and processed >= args.max_records:
                    break

                jp_id = str(row["job_posting_id"])
                title = row["job_title"] or ""
                desc = row["job_description"] or ""

                try:
                    # Quality score
                    q_res = score_quality(
                        job_title=title,
                        job_description=desc,
                        extraction=None,
                        extraction_failed=False,
                    )

                    # Spam preview (heuristic only — no extraction data)
                    spam_res = score_spam_preview(
                        job_title=title,
                        job_description=desc,
                        extraction=None,
                        extraction_failed=False,
                        extraction_empty=True,
                    )

                    # SOC classification
                    soc_code = None
                    try:
                        raw_soc = run_coroutine(classify_soc(title, desc, session, _enrichment_soc_llm()))
                        soc_code = None if raw_soc == "unclassified" else raw_soc
                        if soc_code:
                            soc_classified += 1
                    except Exception as e:
                        log.warning("backfill_soc_failed", job_posting_id=jp_id, error=str(e))

                    # NAICS classification
                    naics_code = "unknown"
                    try:
                        raw_naics = classify_naics(title, desc, session)
                        naics_code = (raw_naics or "unknown").strip() or "unknown"
                        if naics_code != "unknown":
                            naics_classified += 1
                    except Exception as e:
                        log.warning("backfill_naics_failed", job_posting_id=jp_id, error=str(e))

                    session.execute(
                        _UPDATE_SQL,
                        {
                            "job_posting_id": jp_id,
                            "quality_score": q_res.quality_score,
                            "soc_code": soc_code,
                            "naics_code": naics_code,
                            "spam_score": spam_res.spam_score,
                        },
                    )
                    updated += 1

                except Exception as e:
                    log.warning("backfill_record_failed", job_posting_id=jp_id, error=str(e))
                    errors += 1

                processed += 1
                if processed % 10 == 0:
                    log.info(
                        "backfill_progress",
                        processed=processed,
                        updated=updated,
                        errors=errors,
                        soc=soc_classified,
                        naics=naics_classified,
                    )

                time.sleep(args.delay)

    log.info(
        "backfill_complete",
        processed=processed,
        updated=updated,
        errors=errors,
        soc_classified=soc_classified,
        naics_classified=naics_classified,
    )
    print("\nBackfill complete.")
    print(f"  Processed: {processed}")
    print(f"  Updated: {updated}")
    print(f"  Errors: {errors}")
    print(f"  SOC classified: {soc_classified}")
    print(f"  NAICS classified: {naics_classified}")


if __name__ == "__main__":
    main()
