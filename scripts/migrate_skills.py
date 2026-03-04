"""
One-time migration script: Copy the `skills` table from MSSQL to PostgreSQL.

pgloader cannot handle the scientific-notation vector embeddings that MSSQL
stores, so this script reads via pyodbc (MSSQL) and writes via psycopg2
(PostgreSQL), converting embeddings to the format pgvector expects.

Usage (from project root, with venv activated):
    python scripts/migrate_skills.py
"""

import os
import json
import pyodbc
import psycopg2
from psycopg2.extras import execute_values

# ── Connection strings ────────────────────────────────────────────────
# MSSQL: read from the Prisma-style DATABASE_URL or build from .env.docker vars
MSSQL_CONN = (
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
).replace("postgresql+psycopg2://", "postgresql://")  # psycopg2 uses plain postgresql://


def migrate_skills():
    # ── Read from MSSQL ──────────────────────────────────────────────
    print("Connecting to MSSQL...")
    mssql = pyodbc.connect(MSSQL_CONN)
    cur_ms = mssql.cursor()
    cur_ms.execute(
        "SELECT skill_id, skill_subcategory_id, skill_name, skill_info_url, "
        "skill_type, embedding, updatedAt, createdAt FROM skills"
    )
    rows = cur_ms.fetchall()
    print(f"  Read {len(rows)} skills from MSSQL")
    mssql.close()

    # ── Write to PostgreSQL ──────────────────────────────────────────
    print("Connecting to PostgreSQL...")
    pg = psycopg2.connect(PG_DSN)
    cur_pg = pg.cursor()

    # Clear existing rows (pgloader created the table but 0 rows loaded)
    cur_pg.execute("DELETE FROM dbo.skills")

    inserted = 0
    skipped = 0
    for row in rows:
        skill_id = str(row.skill_id)
        subcat_id = str(row.skill_subcategory_id)
        name = row.skill_name
        info_url = row.skill_info_url or ""
        skill_type = row.skill_type
        embedding_raw = row.embedding
        updated_at = row.updatedAt
        created_at = row.createdAt

        # Convert embedding to pgvector format
        embedding_pg = None
        if embedding_raw is not None:
            try:
                # MSSQL stores as varchar — it may be a JSON array string
                if isinstance(embedding_raw, str):
                    floats = json.loads(embedding_raw)
                elif isinstance(embedding_raw, (bytes, bytearray)):
                    floats = json.loads(embedding_raw.decode("utf-8"))
                else:
                    floats = list(embedding_raw)
                # pgvector expects '[0.1,0.2,...]' format with standard decimal notation
                embedding_pg = "[" + ",".join(f"{float(v):.10f}" for v in floats) + "]"
            except Exception as e:
                print(f"  WARNING: Could not convert embedding for skill {skill_id}: {e}")
                embedding_pg = None

        cur_pg.execute(
            """
            INSERT INTO dbo.skills
                (skill_id, skill_subcategory_id, skill_name, skill_info_url,
                 skill_type, embedding, updatedat, createdat)
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s, %s)
            """,
            (skill_id, subcat_id, name, info_url, skill_type,
             embedding_pg, updated_at, created_at),
        )
        inserted += 1

    pg.commit()
    print(f"  Inserted {inserted} skills into PostgreSQL (skipped {skipped})")

    # Verify
    cur_pg.execute("SELECT COUNT(*) FROM dbo.skills")
    pg_count = cur_pg.fetchone()[0]
    print(f"  PostgreSQL skills count: {pg_count}")

    cur_pg.close()
    pg.close()
    print("Done.")


if __name__ == "__main__":
    migrate_skills()
