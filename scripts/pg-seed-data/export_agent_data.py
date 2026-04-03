"""
Export agent pipeline data to JSON fixtures for dev seeding.

Admin tool: run after processing pipeline data, commit fixtures to git
so devs can seed their local databases with enriched job postings.

Usage (from project root, with venv activated):
    python scripts/pg-seed-data/export_agent_data.py
    python scripts/pg-seed-data/export_agent_data.py --limit 500  # cap per table

Reads from PYTHON_DATABASE_URL and writes JSON files to scripts/pg-seed-data/agent-fixtures/.
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

# Agent pipeline tables to export, in dependency order
AGENT_TABLES = [
    "raw_ingested_jobs",
    "job_ingestion_runs",
    "normalized_jobs",
    "normalization_quarantine",
    "extracted_intelligence",
    "llm_audit_log",
    "employer_profiles",
]

OUTPUT_DIR = Path(__file__).parent / "agent-fixtures"


# ── Helpers (reused from export_pg_fixtures.py) ──────────────────────


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
    dsn = dsn.replace("postgresql+psycopg2://", "postgresql://")
    if not dsn:
        print("ERROR: Set PYTHON_DATABASE_URL in your .env file")
        sys.exit(1)
    return psycopg2.connect(dsn)


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
    limit: int | None = None,
) -> list[dict]:
    """Export one table to a list of dicts."""
    select_parts: list[str] = []
    for col_name, _data_type, udt_name in columns:
        if udt_name == "vector":
            select_parts.append(f'"{col_name}"::text AS "{col_name}"')
        else:
            select_parts.append(f'"{col_name}"')

    select_clause = ", ".join(select_parts)
    query = f'SELECT {select_clause} FROM "dbo"."{table_name}"'
    if limit:
        query += f" LIMIT {limit}"
    cur.execute(query)
    rows = cur.fetchall()

    records: list[dict] = []
    for row in rows:
        record: dict = {}
        for i, (col_name, _dt, _udt) in enumerate(columns):
            record[col_name] = row[i]
        records.append(record)

    return records


def write_json(filepath: Path, data: object) -> None:
    """Write data to a JSON file with custom serialization."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, default=json_serializer, indent=2, ensure_ascii=False)
    filepath.write_text(text + "\n", encoding="utf-8")


# ── Main ─────────────────────────────────────────────────────────────


def export_all(limit: int | None = None) -> None:
    """Export all agent pipeline tables to JSON fixtures."""
    print("=" * 60)
    print("Agent Pipeline Data Export")
    print("=" * 60)

    conn = get_pg_connection()
    cur = conn.cursor()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metadata: dict = {
        "exportedAt": datetime.utcnow().isoformat() + "Z",
        "source": "postgresql",
        "schema": "dbo",
        "counts": {},
        "skipped": [],
    }

    exported_count = 0
    total_rows = 0

    for table in AGENT_TABLES:
        columns = get_columns(cur, table)
        if not columns:
            metadata["skipped"].append(table)
            print(f"  {table}: SKIPPED (table does not exist or no columns)")
            continue

        records = export_table(cur, table, columns, limit=limit)

        if len(records) == 0:
            metadata["skipped"].append(table)
            print(f"  {table}: SKIPPED (0 rows)")
            continue

        out_path = OUTPUT_DIR / f"{table}.json"
        write_json(out_path, records)

        metadata["counts"][table] = len(records)
        exported_count += 1
        total_rows += len(records)
        print(f"  {table}: {len(records):,} rows -> {out_path.name}")

    # Write metadata
    write_json(OUTPUT_DIR / "metadata.json", metadata)

    cur.close()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Export complete: {total_rows:,} total rows across {exported_count} tables")
    print(f"Skipped: {len(metadata['skipped'])} tables (empty or missing)")
    print(f"Fixtures written to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    row_limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            row_limit = int(sys.argv[i + 1])
    export_all(limit=row_limit)
