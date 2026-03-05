"""
Export PostgreSQL reference data to JSON fixtures for junior dev seeding.

Admin tool: run once to generate fixtures, commit to git.
Usage (from project root, with venv activated):
    python scripts/pg-seed-data/export_pg_fixtures.py

Reads from PYTHON_DATABASE_URL and writes JSON files to scripts/pg-seed-data/fixtures/.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv

# Load .env from repo root (two levels up from this script)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")

import psycopg2  # noqa: E402

# ── Configuration ────────────────────────────────────────────────────

# Tables excluded from export (PII) — same list as migrate_all_data.py
PII_TABLES: set[str] = {
    "users",
    "jobseekers",
    "jobseekers_private_data",
    "jobseekers_education",
    "jobseeker_has_skills",
    "certificates",
    "work_experiences",
    "project_experiences",
    "project_has_skills",
    "volunteer_has_skills",
    "account",
    "session",
    "authenticator",
    "verificationtoken",
    "employers",
    "educators",
    "volunteers",
    "cfa_admin",
    "bookmarked_jobseekers",
    "events_on_users",
    "vw_userjobseekers",
    "jobseekerjobposting",
    "jobseekerjobpostingskillmatch",
    "casemgmt",
    "casemgmtnotes",
    "meeting",
    "brandingrating",
    "careerprepassessment",
    "cybersecurityrating",
    "dataanalyticsrating",
    "durableskillsrating",
    "itcloudrating",
    "softwaredevrating",
    "jobplacement",
    "traineedetail",
    "employerjobrolefeedback",
    "_prisma_migrations",
}

# Agent-managed tables — excluded from export (they start empty for juniors)
AGENT_TABLES: set[str] = {
    "raw_ingested_jobs",
    "normalized_jobs",
    "job_ingestion_runs",
}

EXCLUDED_TABLES = PII_TABLES | AGENT_TABLES

# FK columns that reference PII tables — NULL these out in exports
PII_FK_COLUMNS: dict[str, list[str]] = {
    "companies": ["createdby"],
    "job_postings": ["employer_id"],
    "events": ["createdbyid"],
}

# Columns to exclude from export (too large for git, regenerated via admin tool)
EXCLUDE_COLUMNS: dict[str, set[str]] = {
    "skills": {"embedding"},  # pgvector embeddings — 107MB, regenerate via /admin
}

OUTPUT_DIR = Path(__file__).parent / "fixtures"


# ── Helpers ──────────────────────────────────────────────────────────


def json_serializer(obj: object) -> str | float | None:
    """Custom JSON serializer for PostgreSQL types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, UUID):
        return str(obj).upper()
    if isinstance(obj, (bytes, memoryview)):
        raw = bytes(obj) if isinstance(obj, memoryview) else obj
        return raw.decode("utf-8", errors="replace")
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def get_pg_connection() -> psycopg2.extensions.connection:
    """Create psycopg2 connection from PYTHON_DATABASE_URL."""
    dsn = os.getenv("PYTHON_DATABASE_URL", "")
    # Strip SQLAlchemy dialect prefix if present
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    if not dsn:
        print("ERROR: Set PYTHON_DATABASE_URL in your .env file")
        sys.exit(1)
    return psycopg2.connect(dsn)


def get_dbo_tables(cur: psycopg2.extensions.cursor) -> list[str]:
    """Get all table names in the dbo schema, sorted."""
    cur.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'dbo'
        ORDER BY tablename
    """)
    return [row[0] for row in cur.fetchall()]


def get_columns(
    cur: psycopg2.extensions.cursor, table_name: str
) -> list[tuple[str, str, str]]:
    """Get (column_name, data_type, udt_name) for a dbo table."""
    cur.execute(
        """
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'dbo' AND table_name = %s
        ORDER BY ordinal_position
    """,
        (table_name,),
    )
    return cur.fetchall()


def export_table(
    cur: psycopg2.extensions.cursor,
    table_name: str,
    columns: list[tuple[str, str, str]],
) -> list[dict]:
    """Export one table to a list of dicts."""
    # Filter out excluded columns (e.g. embeddings too large for git)
    excluded = EXCLUDE_COLUMNS.get(table_name, set())
    columns = [c for c in columns if c[0] not in excluded]

    # Build SELECT with vector columns cast to text
    select_parts: list[str] = []
    for col_name, _data_type, udt_name in columns:
        if udt_name == "vector":
            select_parts.append(f'"{col_name}"::text AS "{col_name}"')
        else:
            select_parts.append(f'"{col_name}"')

    select_clause = ", ".join(select_parts)
    cur.execute(f'SELECT {select_clause} FROM "dbo"."{table_name}"')
    rows = cur.fetchall()

    # NULL out PII FK columns
    pii_fk_cols = {
        c.lower() for c in PII_FK_COLUMNS.get(table_name, [])
    }

    records: list[dict] = []
    for row in rows:
        record: dict = {}
        for i, (col_name, _dt, _udt) in enumerate(columns):
            val = row[i]
            if col_name.lower() in pii_fk_cols:
                val = None
            record[col_name] = val
        records.append(record)

    return records


def write_json(filepath: Path, data: object) -> None:
    """Write data to a JSON file with custom serialization."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, default=json_serializer, indent=2, ensure_ascii=False)
    filepath.write_text(text + "\n", encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────


def export_all() -> None:
    """Export all non-PII dbo tables to JSON fixtures."""
    print("=" * 60)
    print("PostgreSQL Fixture Export")
    print("=" * 60)

    conn = get_pg_connection()
    cur = conn.cursor()

    tables = get_dbo_tables(cur)
    print(f"Found {len(tables)} tables in dbo schema\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata: dict = {
        "exportedAt": datetime.utcnow().isoformat() + "Z",
        "source": "postgresql",
        "schema": "dbo",
        "counts": {},
        "skipped": [],
    }

    exported_count = 0

    for table in tables:
        if table.lower() in EXCLUDED_TABLES:
            metadata["skipped"].append(table)
            print(f"  {table}: SKIPPED (excluded)")
            continue

        columns = get_columns(cur, table)
        if not columns:
            metadata["skipped"].append(table)
            print(f"  {table}: SKIPPED (no columns)")
            continue

        records = export_table(cur, table, columns)

        out_path = OUTPUT_DIR / f"{table}.json"
        write_json(out_path, records)

        metadata["counts"][table] = len(records)
        exported_count += 1
        print(f"  {table}: {len(records)} rows -> {out_path.name}")

    # Write metadata
    write_json(OUTPUT_DIR / "metadata.json", metadata)

    cur.close()
    conn.close()

    total_rows = sum(metadata["counts"].values())
    print(f"\n{'=' * 60}")
    print(f"Export complete: {total_rows:,} total rows across {exported_count} tables")
    print(f"Skipped: {len(metadata['skipped'])} tables (PII/agent-managed)")
    print(f"Fixtures written to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    export_all()
