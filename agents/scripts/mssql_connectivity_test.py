"""
MSSQL connectivity test: run SELECT COUNT(*) FROM job_postings.
Loads env from agents/.env. Uses SQLAlchemy + pyodbc, structlog. No hardcoded credentials.
"""
import os
from pathlib import Path

import structlog
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load agents/.env (parent of scripts/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

log = structlog.get_logger()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    log.error("mssql_connectivity_failed", error="DATABASE_URL not set")
    raise SystemExit(1)

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        row = conn.execute(text("SELECT COUNT(*) AS count FROM job_postings")).fetchone()
    count = row[0] if row is not None else 0
    log.info("mssql_connectivity_ok", table="job_postings", row_count=count)
except Exception as e:
    log.error("mssql_connectivity_failed", error=str(e))
    raise SystemExit(1)
