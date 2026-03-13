"""
Seed a fresh PostgreSQL database with reference data from JSON fixtures.

Junior-dev tool: run after Docker Compose brings up the postgres container.
Usage (from project root, with venv activated):
    python scripts/pg-seed-data/seed_pg_database.py

Reads:  scripts/pg-seed-data/schema.sql         (DDL)
        scripts/pg-seed-data/fixtures/*.json     (data)
Writes: PostgreSQL database specified by PYTHON_DATABASE_URL
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root (two levels up from this script)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")

import psycopg2  # noqa: E402
import psycopg2.extras  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
SCHEMA_FILE = SCRIPT_DIR / "schema.sql"
FIXTURES_DIR = SCRIPT_DIR / "fixtures"
METADATA_FILE = FIXTURES_DIR / "metadata.json"

# ── FK-safe insert order ──────────────────────────────────────────────
# Tables are grouped into tiers: each tier only depends on tables in
# earlier tiers (or has no FK dependencies). Within a tier, order is
# arbitrary.  Tables not listed here are appended at the end (they are
# typically empty or have no FK constraints).

INSERT_ORDER: list[list[str]] = [
    # Tier 0: No FK dependencies — pure reference tables
    [
        "industry_sectors",
        "technology_areas",
        "postal_geo_data",
        "skill_subcategories",
        "social_media_platforms",
        "cip",
        "socc",
        "socc_2010",
        "socc_2018",
        "otherprioritypopulations",
        "ragrecordmanager",
        "self_assessments",          # FK → pathways, but pathways is tier 0 below
    ],
    # Tier 1: Depend only on tier-0 tables
    [
        "pathways",                  # no FK to seeded tables
        "skills",                    # FK → skill_subcategories
        "edu_providers",             # FK → users (PII, NULLed)
        "companies",                 # FK → industry_sectors, users (NULLed)
        "training",                  # no FK to seeded tables
        "programs",                  # no FK to seeded tables
    ],
    # Tier 2: Depend on tier-0 and tier-1 tables
    [
        "jobrole",                   # FK → pathways
        "company_addresses",         # FK → companies, postal_geo_data
        "edu_addresses",             # FK → edu_providers, postal_geo_data
        "company_social_links",      # FK → companies, social_media_platforms
        "company_testimonials",      # FK → companies
        "cip_to_socc_map",           # FK → cip, socc
        "socc2018_to_cip2020_map",   # FK → cip, socc_2018
        "pathway_has_skills",        # FK → pathways, skills
        "pathway_subcategories",     # FK → pathways
        "pathwaytraining",           # FK → pathways, training
        "provider_programs",         # FK → edu_providers, programs, cip
        "providertestimonials",      # FK → edu_providers
        "sa_questions",              # FK → self_assessments
        "proj_based_tech_assessments",  # FK → pathways
    ],
    # Tier 3: Depend on tier-2 tables
    [
        "jobroleskill",              # FK → jobrole, skills
        "jobroletraining",           # FK → jobrole, training
        "job_postings",              # FK → companies, company_addresses, industry_sectors, technology_areas
        "events",                    # FK → users (NULLed)
        "provider_program_has_skills",  # FK → provider_programs, skills
        "sa_possible_answers",       # FK → sa_questions
        "_otherprioritypopulations", # FK → otherprioritypopulations (+ PII table)
    ],
    # Tier 4: Depend on tier-3 tables
    [
        "_jobpostingskills",         # FK → job_postings, skills
    ],
]


# ── Helpers ───────────────────────────────────────────────────────────


def get_pg_connection() -> psycopg2.extensions.connection:
    """Create psycopg2 connection from PYTHON_DATABASE_URL."""
    dsn = os.getenv("PYTHON_DATABASE_URL", "")
    # Strip SQLAlchemy dialect prefix if present
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    if not dsn:
        print("ERROR: Set PYTHON_DATABASE_URL in your .env file")
        print("Example: postgresql+psycopg2://postgres:YourPassword@localhost:5432/talent_finder")
        sys.exit(1)
    return psycopg2.connect(dsn)


def wait_for_postgres(max_retries: int = 30, delay: float = 2.0) -> psycopg2.extensions.connection:
    """Wait for PostgreSQL to be ready, retrying on connection failure."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = get_pg_connection()
            print(f"  Connected to PostgreSQL (attempt {attempt})")
            return conn
        except psycopg2.OperationalError as exc:
            if attempt == max_retries:
                print(f"ERROR: Could not connect after {max_retries} attempts: {exc}")
                sys.exit(1)
            print(f"  Waiting for PostgreSQL... (attempt {attempt}/{max_retries})")
            time.sleep(delay)
    # Should never reach here
    sys.exit(1)


def run_schema_ddl(conn: psycopg2.extensions.connection) -> None:
    """Execute schema.sql to create all tables.

    Drops and recreates the dbo schema for a clean start.  This makes
    the script truly idempotent — safe to run against a fresh database
    or one that already has tables.
    """
    if not SCHEMA_FILE.exists():
        print(f"ERROR: Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)

    ddl = SCHEMA_FILE.read_text(encoding="utf-8")
    cur = conn.cursor()
    try:
        # Drop existing dbo schema (CASCADE drops all objects inside it)
        cur.execute("DROP SCHEMA IF EXISTS dbo CASCADE")
        conn.commit()
        print("  Dropped existing dbo schema")

        # Now run the full DDL (creates schema + tables + indexes + FKs)
        cur.execute(ddl)
        conn.commit()
        print("  Schema DDL executed successfully")
    except Exception as exc:
        conn.rollback()
        print(f"ERROR executing schema DDL: {exc}")
        sys.exit(1)
    finally:
        cur.close()


def get_dbo_tables(cur: psycopg2.extensions.cursor) -> list[str]:
    """Get all table names in the dbo schema."""
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'dbo'
        ORDER BY tablename
    """)
    return [row[0] for row in cur.fetchall()]


def disable_fk_triggers(conn: psycopg2.extensions.connection, tables: list[str]) -> None:
    """Disable all triggers (FK enforcement) on dbo tables."""
    cur = conn.cursor()
    for table in tables:
        cur.execute(f'ALTER TABLE "dbo"."{table}" DISABLE TRIGGER ALL')
    conn.commit()
    cur.close()


def enable_fk_triggers(conn: psycopg2.extensions.connection, tables: list[str]) -> None:
    """Re-enable all triggers (FK enforcement) on dbo tables."""
    cur = conn.cursor()
    for table in tables:
        cur.execute(f'ALTER TABLE "dbo"."{table}" ENABLE TRIGGER ALL')
    conn.commit()
    cur.close()


def truncate_tables(conn: psycopg2.extensions.connection, tables: list[str]) -> None:
    """Truncate all dbo tables (with CASCADE for FK safety)."""
    cur = conn.cursor()
    for table in tables:
        cur.execute(f'TRUNCATE TABLE "dbo"."{table}" CASCADE')
    conn.commit()
    cur.close()


def get_column_types(
    cur: psycopg2.extensions.cursor, table_name: str
) -> dict[str, str]:
    """Get {column_name: udt_name} for a dbo table."""
    cur.execute(
        """
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'dbo' AND table_name = %s
        ORDER BY ordinal_position
    """,
        (table_name,),
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def load_fixture(table_name: str) -> list[dict]:
    """Load JSON fixture for a table. Returns empty list if no file."""
    filepath = FIXTURES_DIR / f"{table_name}.json"
    if not filepath.exists():
        return []
    text = filepath.read_text(encoding="utf-8")
    return json.loads(text)


def insert_records(
    conn: psycopg2.extensions.connection,
    table_name: str,
    records: list[dict],
    col_types: dict[str, str],
) -> int:
    """Insert records into a dbo table using fast batch inserts.

    Returns count inserted.
    """
    if not records:
        return 0

    cur = conn.cursor()

    # Use first record's keys as column list (all records have same shape)
    columns = list(records[0].keys())

    # Filter to columns that actually exist in the DB table
    db_columns = set(col_types.keys())
    columns = [c for c in columns if c in db_columns]

    if not columns:
        cur.close()
        return 0

    # Build INSERT template with appropriate casts
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholder_parts: list[str] = []
    for col in columns:
        udt = col_types.get(col, "")
        if udt == "vector":
            placeholder_parts.append("%s::vector")
        elif udt == "uuid":
            placeholder_parts.append("%s::uuid")
        else:
            placeholder_parts.append("%s")
    values_template = "(" + ", ".join(placeholder_parts) + ")"

    insert_sql = f'INSERT INTO "dbo"."{table_name}" ({col_list}) VALUES %s'

    # Build values list
    values_list = []
    for record in records:
        values_list.append(tuple(record.get(c) for c in columns))

    try:
        psycopg2.extras.execute_values(
            cur, insert_sql, values_list,
            template=values_template,
            page_size=1000,
        )
        conn.commit()
        inserted = len(values_list)
    except Exception as exc:
        conn.rollback()
        print(f"    BATCH ERROR: {str(exc)[:300]}")
        # Fall back to row-by-row to identify problematic rows
        inserted = 0
        for i, vals in enumerate(values_list):
            row_sql = f'INSERT INTO "dbo"."{table_name}" ({col_list}) VALUES {values_template}'
            try:
                cur.execute(row_sql, vals)
                conn.commit()
                inserted += 1
            except Exception as row_exc:
                conn.rollback()
                if inserted < 3:  # Only log first few errors
                    print(f"    Row {i + 1} error: {str(row_exc)[:200]}")

    cur.close()
    return inserted


def run_agent_migrations(conn: psycopg2.extensions.connection) -> None:
    """Create agent-managed tables via run_migrations().

    These tables (raw_ingested_jobs, normalized_jobs, job_ingestion_runs)
    are created by the agent pipeline, not part of the seed fixtures.
    Also adds Phase 1 columns to job_postings.
    """
    try:
        # Import lazily — agents/ may not be on PYTHONPATH in all setups
        sys.path.insert(0, str(_REPO_ROOT))
        from agents.common.data_store.database import get_engine
        from agents.common.data_store.migrations import run_migrations

        engine = get_engine()
        run_migrations(engine)
        print("  Agent migrations completed (agent tables + Phase 1 columns)")
    except ImportError as exc:
        print(f"  WARNING: Could not import agent migrations: {exc}")
        print("  Agent-managed tables will be created when the pipeline first runs.")
    except Exception as exc:
        print(f"  WARNING: Agent migrations failed: {exc}")
        print("  Agent-managed tables will be created when the pipeline first runs.")


# ── Main ──────────────────────────────────────────────────────────────


def seed_database() -> None:
    """Seed PostgreSQL with reference data from JSON fixtures."""
    print("=" * 60)
    print("PostgreSQL Database Seeder")
    print("=" * 60)

    # ── Load metadata ─────────────────────────────────────────────
    if not METADATA_FILE.exists():
        print(f"ERROR: Metadata file not found: {METADATA_FILE}")
        print("Run the export script first: python scripts/pg-seed-data/export_pg_fixtures.py")
        sys.exit(1)

    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    expected_counts: dict[str, int] = metadata["counts"]
    print(f"\nFixtures: {len(expected_counts)} tables, "
          f"{sum(expected_counts.values()):,} total rows expected")

    # ── Connect (with retry for Docker startup) ────────────────────
    print("\nConnecting to PostgreSQL...")
    conn = wait_for_postgres()

    # ── Step 1: Run schema DDL ─────────────────────────────────────
    print("\nStep 1: Creating schema and tables...")
    run_schema_ddl(conn)

    # ── Step 2: Get table list and disable FK triggers ──────────────
    print("\nStep 2: Preparing for data load...")
    cur = conn.cursor()
    dbo_tables = get_dbo_tables(cur)
    print(f"  Found {len(dbo_tables)} tables in dbo schema")

    disable_fk_triggers(conn, dbo_tables)
    print("  FK triggers disabled")

    # ── Step 3: Truncate all tables (idempotent re-run) ─────────────
    truncate_tables(conn, dbo_tables)
    print("  All tables truncated")

    # ── Step 4: Load fixtures in FK-safe order ──────────────────────
    print("\nStep 3: Loading fixture data...")

    # Build ordered table list: explicit tiers first, then remaining
    ordered_tables: list[str] = []
    for tier in INSERT_ORDER:
        ordered_tables.extend(tier)

    # Append any tables in metadata but not in explicit order
    remaining = [
        t for t in expected_counts
        if t not in set(ordered_tables)
    ]
    ordered_tables.extend(sorted(remaining))

    total_inserted = 0
    table_results: dict[str, tuple[int, int]] = {}  # table -> (inserted, expected)

    for table_name in ordered_tables:
        expected = expected_counts.get(table_name, 0)

        records = load_fixture(table_name)
        if not records and expected == 0:
            table_results[table_name] = (0, 0)
            continue

        # Get column types for proper casting
        col_types = get_column_types(cur, table_name)
        if not col_types:
            print(f"  {table_name}: SKIPPED (table not in schema)")
            continue

        inserted = insert_records(conn, table_name, records, col_types)
        total_inserted += inserted
        table_results[table_name] = (inserted, expected)

        status = "OK" if inserted == expected else "WARN"
        if expected == 0 and inserted == 0:
            continue  # Don't print empty tables
        print(f"  {status} {table_name}: {inserted:,} / {expected:,} rows")

    cur.close()

    # ── Step 5: Re-enable FK triggers ───────────────────────────────
    print("\nStep 4: Re-enabling FK triggers...")
    enable_fk_triggers(conn, dbo_tables)
    print("  FK triggers re-enabled")

    # ── Step 6: Run agent migrations ─────────────────────────────
    print("\nStep 5: Running agent migrations...")
    run_agent_migrations(conn)

    # ── Step 7: Verify counts ───────────────────────────────────────
    print("\nStep 6: Verifying row counts...")
    cur = conn.cursor()
    mismatches: list[str] = []
    for table_name, (inserted, expected) in table_results.items():
        if expected == 0:
            continue
        cur.execute(f'SELECT count(*) FROM "dbo"."{table_name}"')
        actual = cur.fetchone()[0]
        if actual != expected:
            mismatches.append(
                f"  {table_name}: expected {expected:,}, got {actual:,}"
            )
    cur.close()
    conn.close()

    # ── Summary ──────────────────────────────────────────────────────
    total_expected = sum(expected_counts.values())
    tables_with_data = sum(1 for _, (i, e) in table_results.items() if e > 0)

    print(f"\n{'=' * 60}")
    print(f"Seed complete: {total_inserted:,} / {total_expected:,} rows "
          f"across {tables_with_data} tables")

    if mismatches:
        print(f"\nWARNING: {len(mismatches)} count mismatches:")
        for m in mismatches:
            print(m)
    else:
        print("All row counts verified")

    print(f"\nNext steps:")
    print(f"  1. Activate venv:  agents\\.venv\\Scripts\\Activate.ps1")
    print(f"  2. Run pipeline:   python agents/pipeline_runner.py")
    print("=" * 60)


if __name__ == "__main__":
    seed_database()
