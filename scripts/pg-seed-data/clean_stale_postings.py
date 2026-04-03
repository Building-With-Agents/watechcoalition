"""
Purge old agent pipeline data from the database before re-seeding.

Admin tool: cleans job pipeline tables while preserving reference data
and LLM audit logs (cost tracking).

Usage (from project root, with venv activated):
    python scripts/pg-seed-data/clean_stale_postings.py          # interactive
    python scripts/pg-seed-data/clean_stale_postings.py --yes    # non-interactive
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (two levels up from this script)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")

import psycopg2  # noqa: E402

# Tables to clean, in reverse FK dependency order.
# llm_audit_log is intentionally EXCLUDED — it persists for cost tracking.
TABLES_TO_CLEAN = [
    "extracted_intelligence",
    "normalization_quarantine",
    "normalized_jobs",
    "job_ingestion_runs",
    "raw_ingested_jobs",
]


def get_pg_connection() -> psycopg2.extensions.connection:
    """Create psycopg2 connection from PYTHON_DATABASE_URL."""
    dsn = os.getenv("PYTHON_DATABASE_URL", "")
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    if not dsn:
        print("ERROR: Set PYTHON_DATABASE_URL in your .env file")
        sys.exit(1)
    return psycopg2.connect(dsn)


def get_row_count(cur: psycopg2.extensions.cursor, table: str) -> int:
    """Get row count for a dbo table."""
    cur.execute(f'SELECT COUNT(*) FROM "dbo"."{table}"')
    return cur.fetchone()[0]


def clean_tables(confirm: bool = False) -> None:
    """Delete all rows from agent pipeline tables."""
    print("=" * 60)
    print("Clean Stale Pipeline Data")
    print("=" * 60)

    conn = get_pg_connection()
    cur = conn.cursor()

    # Show counts BEFORE
    print("\nCurrent row counts:")
    total_before = 0
    for table in TABLES_TO_CLEAN:
        try:
            count = get_row_count(cur, table)
            total_before += count
            print(f"  {table}: {count:,}")
        except psycopg2.errors.UndefinedTable:
            conn.rollback()
            print(f"  {table}: (table does not exist)")

    if total_before == 0:
        print("\nAll tables are already empty. Nothing to clean.")
        cur.close()
        conn.close()
        return

    print(f"\nTotal rows to delete: {total_before:,}")
    print("(llm_audit_log is preserved for cost tracking)")

    if not confirm:
        response = input("\nProceed with deletion? [y/N]: ").strip().lower()
        if response != "y":
            print("Aborted.")
            cur.close()
            conn.close()
            return

    # Delete in reverse FK order
    print("\nDeleting...")
    for table in TABLES_TO_CLEAN:
        try:
            cur.execute(f'DELETE FROM "dbo"."{table}"')
            deleted = cur.rowcount
            print(f"  {table}: {deleted:,} rows deleted")
        except psycopg2.errors.UndefinedTable:
            conn.rollback()
            print(f"  {table}: (table does not exist, skipped)")

    conn.commit()

    # Show counts AFTER
    print("\nRow counts after cleanup:")
    for table in TABLES_TO_CLEAN:
        try:
            count = get_row_count(cur, table)
            print(f"  {table}: {count:,}")
        except psycopg2.errors.UndefinedTable:
            conn.rollback()
            print(f"  {table}: (table does not exist)")

    cur.close()
    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
    clean_tables(confirm=auto_confirm)
