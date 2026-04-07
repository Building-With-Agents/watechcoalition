"""
Run the full extraction pipeline on all normalized records that don't yet have extracted_intelligence.

Resets raw_ingested_jobs to 'pending' for records that have been normalized but not yet extracted,
then runs the processing loop to extract and enrich them.

Usage:
    python agents/scripts/run_full_extraction.py
    python agents/scripts/run_full_extraction.py --batch-size 10 --delay 5

At ~1 min/job with Azure OpenAI, 1000 jobs takes ~16-17 hours.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv

load_dotenv(_REPO_ROOT / ".env")

from agents.common.data_store.database import session_scope
from sqlalchemy import text


def reset_unextracted_to_pending() -> int:
    """Reset raw_ingested_jobs to 'pending' for records not yet in extracted_intelligence."""
    with session_scope() as s:
        # Find raw jobs that have been normalized but whose normalized_jobs row
        # doesn't have a corresponding extracted_intelligence row
        result = s.execute(text("""
            UPDATE dbo.raw_ingested_jobs
            SET processing_status = 'pending'
            WHERE id IN (
                SELECT rij.id
                FROM dbo.raw_ingested_jobs rij
                JOIN dbo.normalized_jobs nj ON nj.raw_job_id = rij.id
                LEFT JOIN dbo.extracted_intelligence ei ON ei.normalized_job_id = nj.id
                WHERE rij.processing_status = 'normalized'
                  AND ei.id IS NULL
                  AND rij.title != ''
                  AND rij.company != ''
                  AND rij.description IS NOT NULL
                  AND length(rij.description) > 50
            )
        """))
        count = result.rowcount
        s.commit()
        return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full extraction on unprocessed records")
    parser.add_argument("--batch-size", type=int, default=5, help="Records per iteration (default: 5)")
    parser.add_argument("--delay", type=int, default=5, help="Seconds between iterations (default: 5)")
    args = parser.parse_args()

    reset_count = reset_unextracted_to_pending()
    print(f"Reset {reset_count} records to pending for extraction")

    if reset_count == 0:
        print("Nothing to process — all normalized records already have extracted_intelligence.")
        return

    max_iterations = (reset_count + args.batch_size - 1) // args.batch_size
    est_minutes = reset_count  # ~1 min/job
    print(f"Estimated: {max_iterations} iterations, ~{est_minutes} min ({est_minutes // 60}h {est_minutes % 60}m)")
    print(f"Running: --max-iterations {max_iterations} --batch-size {args.batch_size} --delay {args.delay}")

    os.environ["NORM_BATCH_SIZE"] = str(args.batch_size)

    # Import and run the processing loop
    from agents.scripts.run_processing_loop import main as run_loop
    sys.argv = [
        "run_processing_loop.py",
        "--max-iterations", str(max_iterations),
        "--batch-size", str(args.batch_size),
        "--delay", str(args.delay),
    ]
    run_loop()


if __name__ == "__main__":
    main()
