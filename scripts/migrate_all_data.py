"""
Full data migration: MSSQL -> PostgreSQL (non-PII tables only).

pgloader created the schema (tables, indexes, foreign keys) but could not
properly convert MSSQL's uniqueidentifier type or vector embeddings.
This script:
  1. Disables FK constraints in PostgreSQL
  2. Truncates all non-PII tables
  3. Copies every row from MSSQL via pyodbc (which returns proper UUID strings)
  4. Re-enables FK constraints

Tables containing PII (user data, auth tokens, jobseeker profiles, etc.)
are excluded from data migration. Their schemas exist in PostgreSQL but
remain empty.

Usage (from project root, with venv activated):
    python scripts/migrate_all_data.py
"""

import json
import os
import sys

import pyodbc
import psycopg2
import psycopg2.extras

# Tables excluded from data migration because they contain PII
# (personally identifiable information). Matched case-insensitively.
PII_TABLES = {
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

# ── Connection config ─────────────────────────────────────────────────
MSSQL_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER=localhost,{os.getenv('MSSQL_PORT', '11433')};"
    f"DATABASE={os.getenv('MSSQL_DATABASE', 'talent_finder')};"
    "UID=SA;"
    f"PWD={os.getenv('MSSQL_SA_PASSWORD', 'YourComplex!P4ssw0rd')};"
    "TrustServerCertificate=yes;"
)

PG_DSN = os.getenv(
    "PYTHON_DATABASE_URL",
    "postgresql+psycopg2://postgres:YourComplex!P4ssw0rd@localhost:5432/talent_finder",
).replace("postgresql+psycopg2://", "postgresql://")


def get_mssql_tables(mssql_cur):
    """Get all user tables in MSSQL."""
    mssql_cur.execute(
        "SELECT TABLE_SCHEMA, TABLE_NAME "
        "FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_TYPE='BASE TABLE' "
        "ORDER BY TABLE_NAME"
    )
    return [(row.TABLE_SCHEMA, row.TABLE_NAME) for row in mssql_cur.fetchall()]


def get_columns(mssql_cur, schema, table):
    """Get column names and types for a MSSQL table."""
    mssql_cur.execute(
        "SELECT COLUMN_NAME, DATA_TYPE "
        "FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA=? AND TABLE_NAME=? "
        "ORDER BY ORDINAL_POSITION",
        (schema, table),
    )
    return [(row.COLUMN_NAME, row.DATA_TYPE) for row in mssql_cur.fetchall()]


def convert_value(val, data_type):
    """Convert a MSSQL value to PostgreSQL-compatible format."""
    if val is None:
        return None
    # pyodbc returns UUIDs as strings automatically — just ensure str
    if data_type == "uniqueidentifier":
        return str(val).upper()
    # bytes / bytearray → keep as bytes for psycopg2
    if isinstance(val, (bytes, bytearray)):
        return bytes(val)
    return val


def convert_embedding(val):
    """Convert MSSQL vector embedding string to pgvector format."""
    if val is None:
        return None
    try:
        if isinstance(val, str):
            floats = json.loads(val)
        elif isinstance(val, (bytes, bytearray)):
            floats = json.loads(val.decode("utf-8"))
        else:
            floats = list(val)
        return "[" + ",".join(f"{float(v):.10f}" for v in floats) + "]"
    except Exception as e:
        print(f"    WARNING: embedding conversion failed: {e}")
        return None


def migrate():
    print("=" * 60)
    print("MSSQL -> PostgreSQL full data migration")
    print("=" * 60)

    # ── Connect ──────────────────────────────────────────────────
    print("\nConnecting to MSSQL...")
    mssql = pyodbc.connect(MSSQL_CONN_STR)
    mssql_cur = mssql.cursor()

    print("Connecting to PostgreSQL...")
    pg = psycopg2.connect(PG_DSN)
    pg_cur = pg.cursor()

    # ── Get table list from MSSQL ────────────────────────────────
    tables = get_mssql_tables(mssql_cur)
    print(f"\nFound {len(tables)} tables in MSSQL\n")

    # ── Disable FK constraints in PostgreSQL ─────────────────────
    print("Disabling FK constraints in PostgreSQL...")
    pg_cur.execute(
        "SELECT tablename, schemaname FROM pg_tables "
        "WHERE schemaname = 'dbo'"
    )
    pg_tables = pg_cur.fetchall()
    for tbl, sch in pg_tables:
        pg_cur.execute(
            f'ALTER TABLE "{sch}"."{tbl}" DISABLE TRIGGER ALL'
        )
    pg.commit()

    # ── Truncate all PostgreSQL tables ───────────────────────────
    print("Truncating all PostgreSQL tables...")
    for tbl, sch in pg_tables:
        pg_cur.execute(f'TRUNCATE TABLE "{sch}"."{tbl}" CASCADE')
    pg.commit()

    # ── Migrate each table (skip PII tables) ─────────────────────
    total_rows = 0
    skipped_pii = 0
    errors = []

    for schema, table in tables:
        if table.lower() in PII_TABLES:
            skipped_pii += 1
            print(f"  {schema}.{table}: SKIPPED (PII)")
            continue

        columns = get_columns(mssql_cur, schema, table)
        col_names = [c[0] for c in columns]
        col_types = {c[0]: c[1] for c in columns}

        # Check if this table has an embedding column (vector type)
        has_embedding = any(
            cn.lower() == "embedding" for cn in col_names
        )

        # Read all rows from MSSQL
        col_list = ", ".join(f"[{c}]" for c in col_names)
        mssql_cur.execute(f"SELECT {col_list} FROM [{schema}].[{table}]")
        rows = mssql_cur.fetchall()

        if not rows:
            print(f"  {schema}.{table}: 0 rows (empty)")
            continue

        # Build INSERT statement for PostgreSQL
        # pgloader lowercases all identifiers, so we must match
        pg_schema = schema.lower()
        pg_table = table.lower()
        pg_col_names = [c.lower() for c in col_names]
        pg_col_list = ", ".join(f'"{c}"' for c in pg_col_names)
        placeholders = ", ".join(["%s"] * len(col_names))

        # Check if embedding column needs vector cast
        if has_embedding:
            placeholder_parts = []
            for cn in pg_col_names:
                if cn == "embedding":
                    placeholder_parts.append("%s::vector")
                else:
                    placeholder_parts.append("%s")
            placeholders = ", ".join(placeholder_parts)

        insert_sql = (
            f'INSERT INTO "{pg_schema}"."{pg_table}" ({pg_col_list}) '
            f"VALUES ({placeholders})"
        )

        # Convert and insert rows
        row_count = 0
        for row in rows:
            converted = []
            for i, cn in enumerate(col_names):
                val = row[i]
                if cn.lower() == "embedding":
                    converted.append(convert_embedding(val))
                else:
                    converted.append(convert_value(val, col_types[cn]))
            try:
                pg_cur.execute(insert_sql, converted)
                row_count += 1
            except Exception as e:
                pg.rollback()
                # Re-disable triggers after rollback
                for tbl2, sch2 in pg_tables:
                    pg_cur.execute(
                        f'ALTER TABLE "{sch2}"."{tbl2}" DISABLE TRIGGER ALL'
                    )
                pg.commit()
                errors.append((f"{schema}.{table}", str(e)[:200]))
                print(f"  {schema}.{table}: ERROR on row {row_count + 1}: {str(e)[:100]}")
                break

        if row_count > 0:
            pg.commit()

        total_rows += row_count
        print(f"  {schema}.{table}: {row_count} rows")

    # ── Re-enable FK constraints ─────────────────────────────────
    print("\nRe-enabling FK constraints...")
    for tbl, sch in pg_tables:
        pg_cur.execute(
            f'ALTER TABLE "{sch}"."{tbl}" ENABLE TRIGGER ALL'
        )
    pg.commit()

    # ── Summary ──────────────────────────────────────────────────
    migrated_count = len(tables) - skipped_pii
    print("\n" + "=" * 60)
    print(f"Migration complete: {total_rows} total rows across {migrated_count} tables")
    print(f"Skipped {skipped_pii} PII tables")
    if errors:
        print(f"\n{len(errors)} tables had errors:")
        for tbl, err in errors:
            print(f"  {tbl}: {err}")
    else:
        print("No errors!")
    print("=" * 60)

    mssql.close()
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    migrate()
