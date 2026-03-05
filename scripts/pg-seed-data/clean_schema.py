"""
Process raw pg_dump output into a clean, idempotent schema.sql.

Admin tool: run once after pg_dump to produce the seed-ready DDL file.
Usage (from project root):
    python scripts/pg-seed-data/clean_schema.py

Reads:  scripts/pg-seed-data/schema_raw.sql  (from pg_dump)
Writes: scripts/pg-seed-data/schema.sql       (cleaned, idempotent)
"""

from __future__ import annotations

import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RAW_FILE = SCRIPT_DIR / "schema_raw.sql"
OUT_FILE = SCRIPT_DIR / "schema.sql"

# Agent-managed tables — removed from schema.sql (created by run_migrations)
AGENT_TABLES = {
    "raw_ingested_jobs",
    "normalized_jobs",
    "job_ingestion_runs",
}


def clean_schema() -> None:
    raw = RAW_FILE.read_text(encoding="utf-8")

    # Split into lines for processing
    lines = raw.splitlines()

    # Remove psql meta-commands (\restrict, \unrestrict, etc.)
    lines = [ln for ln in lines if not re.match(r"^\\", ln)]

    # Remove SET statements and pg_catalog calls (session config noise)
    lines = [
        ln
        for ln in lines
        if not re.match(r"^SET\s", ln)
        and not re.match(r"^SELECT pg_catalog\.", ln)
    ]

    cleaned = "\n".join(lines)

    # Remove agent-managed table CREATE TABLE blocks
    for table in AGENT_TABLES:
        # Remove CREATE TABLE ... ); blocks
        pattern = rf"CREATE TABLE dbo\.{table}\s*\([^;]*\);\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    # Remove agent-managed table sequences (autoincrement)
    for table in AGENT_TABLES:
        pattern = rf"CREATE SEQUENCE dbo\.{table}_id_seq[^;]*;\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        pattern = rf"ALTER SEQUENCE dbo\.{table}_id_seq[^;]*;\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)
        pattern = rf"ALTER TABLE ONLY dbo\.{table}_id_seq[^;]*;\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    # Remove any ALTER TABLE referencing agent tables
    for table in AGENT_TABLES:
        pattern = rf"ALTER TABLE (?:ONLY )?dbo\.{table}[^;]*;\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    # Remove any CREATE INDEX referencing agent tables
    for table in AGENT_TABLES:
        pattern = rf"CREATE (?:UNIQUE )?INDEX[^;]*ON dbo\.{table}[^;]*;\s*"
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL)

    # Remove orphaned pg_dump comment blocks referencing agent tables
    for table in AGENT_TABLES:
        # Comment blocks like: --\n-- Name: <table>...\n--
        for prefix in [table, f"{table}_id_seq", f"ix_{table}", f"uq_{table}"]:
            pattern = rf"--\n-- Name: {prefix}[^\n]*\n--\n"
            cleaned = re.sub(pattern, "", cleaned)
        # "-- Name: raw_ingested_jobs id; Type: DEFAULT; ..."
        pattern = rf"--\n-- Name: {table} [^\n]*\n--\n"
        cleaned = re.sub(pattern, "", cleaned)

    # Make CREATE SCHEMA idempotent
    cleaned = cleaned.replace(
        "CREATE SCHEMA dbo;",
        "CREATE SCHEMA IF NOT EXISTS dbo;",
    )

    # Collapse excessive blank lines
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)

    # Build final output with header
    header = """\
-- =================================================================
-- PostgreSQL schema for watechcoalition reference data (dbo schema)
-- Generated from pg_dump, cleaned for idempotent seeding.
--
-- Agent-managed tables (raw_ingested_jobs, normalized_jobs,
-- job_ingestion_runs) are NOT included — they are created by
-- agents/common/data_store/migrations.py:run_migrations().
--
-- Usage: psql -U postgres -d talent_finder -f schema.sql
--        (or executed by seed_pg_database.py)
-- =================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

"""

    final = header + cleaned.strip() + "\n"

    OUT_FILE.write_text(final, encoding="utf-8")
    print(f"Cleaned schema written to: {OUT_FILE}")
    print(f"  Lines: {len(final.splitlines())}")


if __name__ == "__main__":
    clean_schema()
