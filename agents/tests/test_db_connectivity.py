"""
MSSQL connectivity test

Verifies that the Python agent layer can reach the database using
SQLAlchemy and that the job_postings table is accessible. Requires
PYTHON_DATABASE_URL in .env. Prisma's DATABASE_URL is used by Next.js and is
not a compatible SQLAlchemy DSN for this test.

Usage (from repository root with agents venv activated):
    python -m agents.tests.test_db_connectivity
    # or: cd agents && pytest tests/test_db_connectivity.py -v
"""

import os
import sys

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

load_dotenv()


def _get_sqlalchemy_database_url() -> str | None:
    """
    Return a SQLAlchemy-compatible database URL for the Python agents.

    Prefer `PYTHON_DATABASE_URL`. Prisma's `DATABASE_URL` is not compatible
    with SQLAlchemy in this project, so only fall back when it already looks
    like a SQLAlchemy URL.
    """
    python_database_url = os.getenv("PYTHON_DATABASE_URL")
    if python_database_url:
        return python_database_url

    database_url = os.getenv("DATABASE_URL")
    if database_url and "://" in database_url and database_url.startswith(("mssql+", "sqlite")):
        return database_url
    return None


def _write_line(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def run_db_connectivity_check() -> None:
    """Simple SQLAlchemy connect test to local MSSQL; requires PYTHON_DATABASE_URL in .env."""
    database_url = _get_sqlalchemy_database_url()
    if not database_url:
        _write_line("FAIL: PYTHON_DATABASE_URL environment variable is not set.")
        _write_line("      Set it in your .env file with a SQLAlchemy-compatible MSSQL DSN and try again.")
        sys.exit(1)

    _write_line("Connecting to database...")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            row_count = result.scalar()
        _write_line("PASS: Connected successfully.")
        _write_line(f"      job_postings row count: {row_count}")
    except OperationalError as exc:
        _write_line("FAIL: Could not connect to the database.")
        _write_line("      Check that PYTHON_DATABASE_URL is correct and the server is reachable.")
        _write_line(f"      Error: {exc}")
        sys.exit(1)
    except SQLAlchemyError as exc:
        _write_line("FAIL: Query error — check that the job_postings table exists.")
        _write_line(f"      Error: {exc}")
        sys.exit(1)


def test_db_connectivity_pytest() -> None:
    """Pytest-discoverable version: skips if Python agent DB config is unavailable."""
    database_url = _get_sqlalchemy_database_url()
    if not database_url:
        pytest.skip("PYTHON_DATABASE_URL not set")
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
        row_count = result.scalar()
    assert row_count is not None and row_count >= 0


if __name__ == "__main__":
    run_db_connectivity_check()
