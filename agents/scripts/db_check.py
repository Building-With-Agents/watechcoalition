# ruff: noqa: T201
"""Quick database verification utility.

Usage (from repo root, venv activated):

    python agents/scripts/db_check.py tables          # list dbo tables
    python agents/scripts/db_check.py counts          # row counts for agent tables
    python agents/scripts/db_check.py query "SELECT 1"  # run arbitrary SELECT
    python agents/scripts/db_check.py migrate         # run agent migrations
    python agents/scripts/db_check.py reset           # truncate all agent tables (for fresh re-runs)

Reads PYTHON_DATABASE_URL from .env automatically.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is on sys.path so "agents.*" imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from sqlalchemy import text  # noqa: E402

from agents.common.data_store.database import get_engine  # noqa: E402


def _run_query(sql: str) -> None:
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
        if not rows:
            print("(no rows)")
            return
        # Print column headers from first row's keys
        keys = rows[0]._fields if hasattr(rows[0], "_fields") else list(range(len(rows[0])))
        print("\t".join(str(k) for k in keys))
        print("-" * 60)
        for row in rows:
            print("\t".join(str(v) for v in row))


def tables() -> None:
    """List all tables in the dbo schema."""
    _run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'dbo' ORDER BY table_name")


def counts() -> None:
    """Row counts for agent-managed tables."""
    _run_query(
        "SELECT 'raw_ingested_jobs' AS tbl, COUNT(*) AS cnt FROM dbo.raw_ingested_jobs "
        "UNION ALL SELECT 'normalized_jobs', COUNT(*) FROM dbo.normalized_jobs "
        "UNION ALL SELECT 'job_ingestion_runs', COUNT(*) FROM dbo.job_ingestion_runs "
        "UNION ALL SELECT 'normalization_quarantine', COUNT(*) FROM dbo.normalization_quarantine"
    )


def migrate() -> None:
    """Run agent migrations."""
    from agents.common.data_store.migrations import run_migrations

    run_migrations(get_engine())
    print("Migrations complete")


def reset() -> None:
    """Truncate all agent-managed tables for a clean re-run.

    FK-safe order: child tables first, then parent tables.
    """
    # Only ingestion + normalization agent tables (Phase 1 Week 03)
    tables_in_order = [
        "dbo.normalization_quarantine",
        "dbo.normalized_jobs",
        "dbo.raw_ingested_jobs",
        "dbo.job_ingestion_runs",
    ]
    print("This will DELETE all data in agent tables:")
    for t in tables_in_order:
        print(f"  - {t}")
    confirm = input("Type 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    engine = get_engine()
    with engine.begin() as conn:
        for t in tables_in_order:
            conn.execute(text(f"TRUNCATE {t} CASCADE"))
            print(f"  truncated {t}")
    print("Reset complete — all agent tables are empty.")


def query(sql: str) -> None:
    """Run an arbitrary SELECT query."""
    if not sql.strip().upper().startswith("SELECT"):
        print("ERROR: Only SELECT queries are allowed.")
        sys.exit(1)
    _run_query(sql)


COMMANDS = {
    "tables": tables,
    "counts": counts,
    "migrate": migrate,
    "reset": reset,
    "query": query,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: python agents/scripts/db_check.py <{'|'.join(COMMANDS)}>")
        print("  query requires a SQL string argument, e.g.:")
        print('  python agents/scripts/db_check.py query "SELECT COUNT(*) FROM dbo.raw_ingested_jobs"')
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "query":
        if len(sys.argv) < 3:
            print("ERROR: query command requires a SQL string argument.")
            sys.exit(1)
        query(sys.argv[2])
    else:
        COMMANDS[cmd]()


if __name__ == "__main__":
    main()
