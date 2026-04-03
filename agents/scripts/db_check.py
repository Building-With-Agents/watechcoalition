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

from sqlalchemy import text  # noqa: E402

from agents.common.data_store.database import get_engine  # noqa: E402
from agents.common.env import load_repo_root_dotenv  # noqa: E402

load_repo_root_dotenv()


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
        "SELECT 'job_ingestion_runs' AS tbl, COUNT(*) AS cnt FROM dbo.job_ingestion_runs "
        "UNION ALL SELECT 'raw_ingested_jobs', COUNT(*) FROM dbo.raw_ingested_jobs "
        "UNION ALL SELECT 'normalized_jobs', COUNT(*) FROM dbo.normalized_jobs "
        "UNION ALL SELECT 'normalization_quarantine', COUNT(*) FROM dbo.normalization_quarantine "
        "UNION ALL SELECT 'extracted_intelligence', COUNT(*) FROM dbo.extracted_intelligence "
        "UNION ALL SELECT 'llm_audit_log', COUNT(*) FROM dbo.llm_audit_log "
        "UNION ALL SELECT 'employer_profiles', COUNT(*) FROM dbo.employer_profiles "
        "UNION ALL SELECT 'job_postings', COUNT(*) FROM dbo.job_postings"
    )


def migrate() -> None:
    """Run agent migrations."""
    from agents.common.data_store.migrations import run_migrations

    run_migrations(get_engine())
    print("Migrations complete")


def reset() -> None:
    """Truncate all agent-managed tables for a clean pipeline re-run.

    FK-safe order: child tables first, then parent tables.
    Preserves: llm_audit_log (cost data persists across runs),
    socc, companies, industry_sectors, technology_areas, skills (reference data).
    """
    tables_in_order = [
        "dbo.extracted_intelligence",
        "dbo.employer_profiles",
        "dbo.normalization_quarantine",
        "dbo.normalized_jobs",
        "dbo.raw_ingested_jobs",
        "dbo.job_ingestion_runs",
        "dbo.job_postings",
    ]
    print("This will DELETE all data in these agent tables:")
    for t in tables_in_order:
        print(f"  - {t}")
    print("\nPreserved (not truncated):")
    print("  - dbo.llm_audit_log (cost audit data)")
    print("  - dbo.socc, companies, industry_sectors, technology_areas, skills (reference data)")
    confirm = input("\nType 'yes' to confirm: ").strip().lower()
    if confirm != "yes":
        print("Aborted.")
        return

    engine = get_engine()
    with engine.begin() as conn:
        for t in tables_in_order:
            try:
                conn.execute(text(f"TRUNCATE {t} CASCADE"))
                print(f"  truncated {t}")
            except Exception as exc:
                print(f"  skipped {t} ({exc})")
    print("\nReset complete — agent pipeline tables are empty. Ready for fresh run.")


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
