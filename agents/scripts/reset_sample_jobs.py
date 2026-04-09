# ruff: noqa: T201
"""Roll back 3 fully-processed jobs so the pipeline can re-process them.

Dev tool: clears downstream rows (normalized_jobs, extracted_intelligence,
job_postings) for 3 enriched raw jobs and resets their processing_status to
'pending' so run_processing_loop.py will pick them up again.

Usage (repo root, venv activated):

    python agents/scripts/reset_sample_jobs.py                  # default 3 jobs
    python agents/scripts/reset_sample_jobs.py --count 5        # custom count
    python agents/scripts/reset_sample_jobs.py --dry-run        # preview only, no writes

Purpose:
    After seeding from fixtures the DB is fully processed (nothing pending).
    This script lets devs verify their Week 7 pipeline step produces real
    output by giving the processing loop something to work on.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from sqlalchemy import text  # noqa: E402

from agents.common.data_store.database import get_engine  # noqa: E402
from agents.common.env import load_repo_root_dotenv  # noqa: E402

load_repo_root_dotenv()


def reset_jobs(count: int, dry_run: bool) -> None:
    engine = get_engine()

    with engine.begin() as conn:
        # Pick `count` processed raw jobs — any that have at least a normalized
        # row (extraction optional but preferred). Uses a LEFT JOIN so records
        # that went through normalization but not yet extraction are also valid
        # reset candidates. Prefer records that have extraction done (ei.id IS
        # NOT NULL) so the reset exercises the most pipeline steps.
        rows = conn.execute(
            text("""
                SELECT r.id AS raw_id, r.external_id, r.source, r.title, r.company,
                       n.id AS norm_id, (ei.id IS NOT NULL) AS has_extraction
                FROM dbo.raw_ingested_jobs r
                JOIN dbo.normalized_jobs n ON n.raw_job_id = r.id
                LEFT JOIN dbo.extracted_intelligence ei ON ei.normalized_job_id = n.id
                WHERE r.processing_status NOT IN ('pending', 'quarantined')
                ORDER BY (ei.id IS NOT NULL) DESC, r.id DESC
                LIMIT :count
            """),
            {"count": count},
        ).fetchall()

    if not rows:
        print("No fully-enriched records found — nothing to reset.")
        print("Tip: make sure you ran seed_pg_database.py + seed_agent_data.py first.")
        return

    raw_ids  = [r.raw_id  for r in rows]
    norm_ids = [r.norm_id for r in rows]

    print(f"\n{'DRY RUN — ' if dry_run else ''}Resetting {len(rows)} job(s):\n")
    for r in rows:
        print(f"  raw_id={r.raw_id:>6}  norm_id={r.norm_id:>6}  [{r.source}] {r.company} — {r.title}")

    if dry_run:
        print("\n(dry-run: no changes written)")
        return

    print()

    with engine.begin() as conn:
        # 1. Delete extracted_intelligence rows (FK child of normalized_jobs)
        result = conn.execute(
            text("DELETE FROM dbo.extracted_intelligence WHERE normalized_job_id = ANY(:ids)"),
            {"ids": norm_ids},
        )
        print(f"  extracted_intelligence deleted : {result.rowcount}")

        # 2. Delete job_postings rows created by this batch
        #    Matched via ingestion_run_id + external_id carried through normalization
        result = conn.execute(
            text("""
                DELETE FROM dbo.job_postings jp
                USING dbo.normalized_jobs nj
                WHERE nj.id = ANY(:ids)
                  AND jp.source     = nj.source
                  AND jp.external_id = nj.external_id
            """),
            {"ids": norm_ids},
        )
        print(f"  job_postings deleted           : {result.rowcount}")

        # 3. Delete normalized_jobs rows
        result = conn.execute(
            text("DELETE FROM dbo.normalized_jobs WHERE id = ANY(:ids)"),
            {"ids": norm_ids},
        )
        print(f"  normalized_jobs deleted        : {result.rowcount}")

        # 4. Reset raw_ingested_jobs back to 'pending'
        result = conn.execute(
            text("""
                UPDATE dbo.raw_ingested_jobs
                SET processing_status = 'pending',
                    error_message = NULL
                WHERE id = ANY(:ids)
            """),
            {"ids": raw_ids},
        )
        print(f"  raw_ingested_jobs reset        : {result.rowcount} -> 'pending'")

    print(f"\nDone. Run the pipeline to re-process these {len(rows)} job(s):")
    print("  python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 3")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset N fully-processed jobs to pending for pipeline re-testing.")
    parser.add_argument("--count",   type=int,  default=3,     help="Number of jobs to reset (default: 3)")
    parser.add_argument("--dry-run", action="store_true",      help="Preview what would be reset without writing")
    args = parser.parse_args()

    if args.count < 1:
        print("--count must be at least 1")
        sys.exit(1)

    reset_jobs(count=args.count, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
