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

from sqlalchemy import text

from agents.common.data_store.database import session_scope


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
    parser.add_argument("--skip-export", action="store_true", help="Skip fixture export and PR after pipeline completes")
    args = parser.parse_args()

    reset_count = reset_unextracted_to_pending()

    if reset_count == 0:
        return

    max_iterations = (reset_count + args.batch_size - 1) // args.batch_size

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

    if not args.skip_export:
        _export_and_open_pr()


def _export_and_open_pr() -> None:
    """Export fixtures and open a PR against development."""
    import subprocess

    # Export fixtures
    subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "pg-seed-data" / "export_agent_data.py")],
        cwd=str(_REPO_ROOT),
        check=True,
    )

    # Git: create branch, commit, push, open PR
    branch = "update/re-export-fixtures-with-skills"
    subprocess.run(["git", "checkout", "-b", branch], cwd=str(_REPO_ROOT), check=False)
    subprocess.run(["git", "add", "scripts/pg-seed-data/agent-fixtures/"], cwd=str(_REPO_ROOT), check=True)

    commit_msg = "update: re-export agent fixtures after full extraction run"
    result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=str(_REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        subprocess.run(["git", "checkout", "development"], cwd=str(_REPO_ROOT), check=False)
        return

    subprocess.run(["git", "push", "-u", "origin", branch], cwd=str(_REPO_ROOT), check=True)
    subprocess.run(
        ["gh", "pr", "create",
         "--title", "Update fixtures: re-export after full extraction run",
         "--base", "development",
         "--body", "Re-exported agent fixtures after running full extraction pipeline. Skills arrays now populated."],
        cwd=str(_REPO_ROOT),
        check=True,
    )
    subprocess.run(["git", "checkout", "development"], cwd=str(_REPO_ROOT), check=False)


if __name__ == "__main__":
    main()
