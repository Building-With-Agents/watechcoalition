"""
MSSQL connectivity test for the Job Intelligence Engine.
Uses SQLAlchemy + pyodbc only. Reads DB URL from .env (no hardcoded credentials).
Prints row count of job_postings.
"""
import os
import sys

from dotenv import load_dotenv

# Load .env from repo root (parent of agents/)
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(_REPO_ROOT, ".env"))

# Prefer PYTHON_DATABASE_URL (mssql+pyodbc); fall back to DATABASE_URL
DATABASE_URL = os.getenv("PYTHON_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: Set PYTHON_DATABASE_URL or DATABASE_URL in .env", file=sys.stderr)
    sys.exit(1)

def main() -> None:
    import warnings
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import DBAPIError, SAWarning

    # Suppress "Unrecognized server version" warning (e.g. SQL Server 2022 / 17.x) — harmless for this script
    warnings.filterwarnings("ignore", message=".*Unrecognized server version.*", category=SAWarning)

    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) AS cnt FROM job_postings"))
            row = result.fetchone()
            count = row[0] if row else 0
        print(f"job_postings row count: {count}")
    except DBAPIError as e:
        err = str(e.orig) if e.orig else str(e)
        if "Can't open lib" in err or "file not found" in err.lower():
            print("ODBC Driver not found. Your connection string expects a Microsoft ODBC driver that is not installed.", file=sys.stderr)
            print("", file=sys.stderr)
            print("On macOS: see ONBOARDING.md step 7.3 (brew install ... msodbcsql17).", file=sys.stderr)
            print("In .env use driver=ODBC+Driver+17+for+SQL+Server.", file=sys.stderr)
        elif "HYT00" in err or "timeout" in err.lower() or "Login timeout" in err:
            print("Login timeout expired — the client could not reach SQL Server in time.", file=sys.stderr)
            print("", file=sys.stderr)
            print("Check:", file=sys.stderr)
            print("  1. Docker is running and the SQL Server container is up: docker ps --filter 'name=mssql'", file=sys.stderr)
            print("  2. Start it if needed: docker compose --env-file .env.docker up -d (from repo root)", file=sys.stderr)
            print("  3. PYTHON_DATABASE_URL host/port match .env.docker (e.g. 127.0.0.1:1433 or localhost:1433 or the port you set)", file=sys.stderr)
            print("  4. Password in PYTHON_DATABASE_URL matches MSSQL_SA_PASSWORD in .env.docker", file=sys.stderr)
        else:
            print(f"Database error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
