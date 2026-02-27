"""
Minimal MSSQL connectivity test for the agents service.
Run from repo root: python -m agents.tests.test_db_connection
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from repo root when run from agents/ or repo root 
load_dotenv()
if not os.getenv("PYTHON_DATABASE_URL"):
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DATABASE_URL = os.getenv("PYTHON_DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("ERROR: DATABASE_URL is not set. Set it in .env at the repo root.")

def main():
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            count = result.scalar()
        print(f"job_postings row count: {count}")
    except Exception as e:
        raise SystemExit(f"Connection failed: {e}") from e

if __name__ == "__main__":
    main()
