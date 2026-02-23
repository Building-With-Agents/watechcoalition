"""
MSSQL connectivity test — Exercise 1.1

Verifies that the Python agent layer can reach the database using
SQLAlchemy + pyodbc and that the job_postings table is accessible.

Usage:
    python agents/tests/test_db_connectivity.py
"""

import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

load_dotenv()


def test_db_connectivity() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL environment variable is not set.")
        print("      Set it in your .env file and try again.")
        sys.exit(1)

    print(f"Connecting to database...")

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            row_count = result.scalar()
        print(f"PASS: Connected successfully.")
        print(f"      job_postings row count: {row_count}")
    except OperationalError as exc:
        print(f"FAIL: Could not connect to the database.")
        print(f"      Check that DATABASE_URL is correct and the server is reachable.")
        print(f"      Error: {exc}")
        sys.exit(1)
    except SQLAlchemyError as exc:
        print(f"FAIL: Query error — check that the job_postings table exists.")
        print(f"      Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    test_db_connectivity()
