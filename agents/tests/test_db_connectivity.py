"""
MSSQL connectivity test

Verifies that the Python agent layer can reach the database using
SQLAlchemy and that the job_postings table is accessible. Requires
DATABASE_URL in .env (Prisma sqlserver:// format is used by Next.js;
for SQLAlchemy you may need mssql+pyodbc:// with driver if this test fails).

Usage (from repository root with agents venv activated):
    python -m agents.tests.test_db_connectivity
    # or: cd agents && pytest tests/test_db_connectivity.py -v
"""

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

load_dotenv()


def test_db_connectivity() -> None:
    """Simple SQLAlchemy connect test to local MSSQL; requires DATABASE_URL in .env."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL environment variable is not set.")
        print("      Set it in your .env file and try again.")
        sys.exit(1)

    print("Connecting to database...")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            row_count = result.scalar()
        print("PASS: Connected successfully.")
        print(f"      job_postings row count: {row_count}")
    except OperationalError as exc:
        print("FAIL: Could not connect to the database.")
        print("      Check that DATABASE_URL is correct and the server is reachable.")
        print(f"      Error: {exc}")
        sys.exit(1)
    except SQLAlchemyError as exc:
        print("FAIL: Query error — check that the job_postings table exists.")
        print(f"      Error: {exc}")
        sys.exit(1)


def test_db_connectivity_pytest() -> None:
    """Pytest-discoverable version: skips if DATABASE_URL unset; asserts connect + query."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        import pytest
        pytest.skip("DATABASE_URL not set")
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
        row_count = result.scalar()
    assert row_count is not None and row_count >= 0


if __name__ == "__main__":
    test_db_connectivity()
