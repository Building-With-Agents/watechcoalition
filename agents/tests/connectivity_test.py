"""
Connectivity test: connect to MSSQL via SQLAlchemy + pyodbc, run COUNT on job_postings, log result.
Reads DATABASE_URL from .env. Exits with 1 on failure.
"""
import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env from agents/ (parent of tests/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

logger = structlog.get_logger()


def main() -> int:
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("connectivity_test_success", error="DATABASE_URL not set")
        return 1

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            row_count = result.scalar()
        logger.info("connectivity_test_success", row_count=row_count)
        return 0
    except Exception as e:  # noqa: BLE001
        logger.error("connectivity_test_success", error=str(e), row_count=None)
        return 1


if __name__ == "__main__":
    sys.exit(main())
