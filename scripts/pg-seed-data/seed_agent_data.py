"""
Seed a local PostgreSQL database with agent pipeline data from JSON fixtures.

Junior-dev tool: run after seed_pg_database.py to populate enriched job postings
so analytics and visualization dashboards have data to work with.

Usage (from project root, with venv activated):
    python scripts/pg-seed-data/seed_agent_data.py

Reads:  scripts/pg-seed-data/agent-fixtures/*.json  (data)
Writes: PostgreSQL database specified by PYTHON_DATABASE_URL

Uses UPSERT (INSERT ... ON CONFLICT DO NOTHING) — safe to run multiple times.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (two levels up from this script)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")

import psycopg2  # noqa: E402
import psycopg2.extras  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "agent-fixtures"

# ── FK-safe insert order ──────────────────────────────────────────────
# Tables ordered so that FK dependencies are satisfied:
# companies has no FK deps — must be before job_postings (company_id FK)
# naics has no FK deps — reference table for NAICS codes
# raw_ingested_jobs has no FK deps on other agent tables
# job_ingestion_runs has no FK deps on other agent tables
# normalized_jobs → raw_ingested_jobs (via raw_ingested_job_id)
# extracted_intelligence → normalized_jobs (via normalized_job_id)
# employer_profiles has no FK deps on other agent tables
# job_postings → companies (via company_id)
# llm_audit_log has no FK deps on other agent tables

INSERT_ORDER = [
    "companies",
    "naics",
    "raw_ingested_jobs",
    "job_ingestion_runs",
    "normalized_jobs",
    "normalization_quarantine",
    "extracted_intelligence",
    "employer_profiles",
    "job_postings",
    "llm_audit_log",
]


def get_pg_connection() -> psycopg2.extensions.connection:
    """Create psycopg2 connection from PYTHON_DATABASE_URL."""
    dsn = os.getenv("PYTHON_DATABASE_URL", "")
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    if not dsn:
        print("ERROR: Set PYTHON_DATABASE_URL in your .env file")
        sys.exit(1)
    return psycopg2.connect(dsn)


def get_primary_key(cur: psycopg2.extensions.cursor, table: str) -> list[str]:
    """Get primary key column(s) for a dbo table."""
    cur.execute(
        """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        JOIN pg_class c ON c.oid = i.indrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE i.indisprimary
          AND c.relname = %s
          AND n.nspname = 'dbo'
        ORDER BY array_position(i.indkey, a.attnum)
    """,
        (table,),
    )
    return [row[0] for row in cur.fetchall()]


def upsert_records(
    cur: psycopg2.extensions.cursor,
    table: str,
    records: list[dict],
    pk_cols: list[str],
) -> tuple[int, int]:
    """Insert records with ON CONFLICT DO NOTHING. Returns (inserted, skipped)."""
    if not records:
        return 0, 0

    columns = list(records[0].keys())
    col_names = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(["%s"] * len(columns))
    conflict_cols = ", ".join(f'"{c}"' for c in pk_cols)

    sql = (
        f'INSERT INTO "dbo"."{table}" ({col_names}) '
        f"VALUES ({placeholders}) "
        f"ON CONFLICT ({conflict_cols}) DO NOTHING"
    )

    inserted = 0
    skipped = 0

    for record in records:
        values = []
        for col in columns:
            val = record.get(col)
            # Convert ISO datetime strings back to datetime objects
            if isinstance(val, str) and len(val) >= 19:
                for _fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        val = datetime.fromisoformat(val)
                        break
                    except ValueError:
                        continue
            # Handle JSON/dict values — store as JSON string
            if isinstance(val, (dict, list)):
                val = json.dumps(val)
            values.append(val)

        cur.execute(sql, values)
        if cur.rowcount > 0:
            inserted += 1
        else:
            skipped += 1

    return inserted, skipped


def run_migrations() -> None:
    """Run agent migrations to ensure schema is current."""
    try:
        from agents.common.data_store.database import get_engine
        from agents.common.data_store.migrations import run_migrations as _migrate

        _migrate(get_engine())
        print("Migrations: OK")
    except Exception as e:
        print(f"Migrations: SKIPPED ({e})")
        print("  (Tables may already exist — continuing with seed)")


def seed_all() -> None:
    """Seed all agent pipeline tables from JSON fixtures."""
    print("=" * 60)
    print("Agent Pipeline Data Seed")
    print("=" * 60)

    if not FIXTURES_DIR.exists():
        print(f"\nERROR: Fixtures directory not found: {FIXTURES_DIR}")
        print("Run export_agent_data.py first to generate fixtures.")
        sys.exit(1)

    # Run migrations first
    print("\nRunning migrations...")
    run_migrations()

    conn = get_pg_connection()
    cur = conn.cursor()

    total_inserted = 0
    total_skipped = 0

    print(f"\nSeeding from: {FIXTURES_DIR}\n")

    for table in INSERT_ORDER:
        fixture_file = FIXTURES_DIR / f"{table}.json"
        if not fixture_file.exists():
            print(f"  {table}: SKIPPED (no fixture file)")
            continue

        records = json.loads(fixture_file.read_text(encoding="utf-8"))
        if not records:
            print(f"  {table}: SKIPPED (0 records in fixture)")
            continue

        pk_cols = get_primary_key(cur, table)
        if not pk_cols:
            print(f"  {table}: SKIPPED (no primary key found — table may not exist)")
            conn.rollback()
            continue

        try:
            inserted, skipped = upsert_records(cur, table, records, pk_cols)
            conn.commit()
            total_inserted += inserted
            total_skipped += skipped
            print(
                f"  {table}: {inserted:,} inserted, {skipped:,} skipped "
                f"(of {len(records):,} total)"
            )
        except Exception as e:
            conn.rollback()
            print(f"  {table}: ERROR — {e}")

    print(f"\n{'=' * 60}")
    print(f"Seed complete: {total_inserted:,} inserted, {total_skipped:,} skipped")
    print("=" * 60)

    cur.close()
    conn.close()


if __name__ == "__main__":
    seed_all()
