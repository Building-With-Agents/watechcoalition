"""
Connectivity test: SQLAlchemy + pyodbc, reads DATABASE_URL from agents/.env,
prints job_postings row count. No Prisma, no hardcoded credentials.
Run from repo root: python -m agents.connectivity_test
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load agents/.env (script lives in agents/; when run as -m from repo root, __file__ is agents/connectivity_test.py)
_agents_dir = Path(__file__).resolve().parent
load_dotenv(_agents_dir / ".env")
# Fallback: if run from repo root, also try repo_root/agents/.env
if not os.getenv("DATABASE_URL"):
    _repo_agents = Path.cwd() / "agents" / ".env"
    if _repo_agents.exists():
        load_dotenv(_repo_agents)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL or not DATABASE_URL.strip():
    print("Error: DATABASE_URL not set. Set it in agents/.env", file=sys.stderr)
    sys.exit(1)

# Convert sqlserver://...;database=...;user=...;password=... to mssql+pyodbc://
_engine_url = DATABASE_URL.strip().strip('"').strip("'")
if _engine_url.lower().startswith("sqlserver://"):
    # Parse semicolon-separated key=value
    parts = _engine_url.replace("sqlserver://", "", 1).split(";")
    host_port = parts[0].strip()  # e.g. localhost:1433
    params = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            params[k.strip().lower()] = v.strip()
    user = params.get("user", "")
    password = params.get("password", "")
    database = params.get("database", "")
    from urllib.parse import quote_plus

    if user and password and database:
        _user_enc = quote_plus(user)
        _pass_enc = quote_plus(password)
        extra = "driver=ODBC+Driver+18+for+SQL+Server"
        if params.get("trustservercertificate", "").lower() == "true":
            extra += "&TrustServerCertificate=yes"
        if params.get("encrypt", "").lower() == "false":
            extra += "&Encrypt=no"
        _engine_url = f"mssql+pyodbc://{_user_enc}:{_pass_enc}@{host_port}/{database}?{extra}"
    else:
        print(
            "Error: DATABASE_URL in sqlserver:// form must include user=, password=, database=.",
            file=sys.stderr,
        )
        sys.exit(1)
# If not sqlserver://, _engine_url is already set above; use as-is (e.g. mssql+pyodbc://...)

def main():
    try:
        engine = create_engine(_engine_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            count = result.scalar()
        print(f"job_postings row count: {count}")
        sys.exit(0)
    except Exception as e:
        print(f"Connectivity error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
