#!/usr/bin/env python3
"""Connectivity test: SQLAlchemy + pyodbc, reads DATABASE_URL from .env, prints job_postings row count."""

import os
import sys
import urllib.parse
import warnings
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SAWarning

# Suppress "Unrecognized server version" for Docker/newer SQL Server builds
warnings.filterwarnings("ignore", message=".*Unrecognized server version.*", category=SAWarning)

# Load .env from repo root (script lives in scripts/)
_repo_root = Path(__file__).resolve().parent.parent
load_dotenv(_repo_root / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set. Add it to .env in the repo root.", file=sys.stderr)
    sys.exit(1)

# ODBC driver name (Linux: install msodbcsql18; name is "ODBC Driver 18 for SQL Server")
ODBC_DRIVER = "ODBC Driver 18 for SQL Server"


def _prisma_to_odbc_connect(url: str) -> str:
    """Convert Prisma-style sqlserver:// URL to a pyodbc ODBC connection string."""
    url = url.strip()
    if url.startswith("sqlserver://"):
        url = url[len("sqlserver://") :]
    parts = [p.strip() for p in url.split(";")]
    # First part: host:port or user:password@host:port
    first = parts[0] if parts else ""
    host_port = first
    user, password = None, None
    if "@" in first:
        user_pass, host_port = first.rsplit("@", 1)
        if ":" in user_pass:
            user, password = user_pass.split(":", 1)
            password = urllib.parse.unquote(password)
    opts = {}
    for p in parts[1:]:
        if "=" in p:
            k, v = p.split("=", 1)
            opts[k.strip().lower()] = v.strip()
    server = opts.get("server") or host_port
    if ":" in server and not server.startswith("["):
        server = server.replace(":", ",", 1)  # localhost:1433 -> localhost,1433
    database = opts.get("database", "master")
    uid = opts.get("user") or opts.get("user id") or user
    pwd = opts.get("password") or opts.get("pwd") or password
    encrypt = opts.get("encrypt", "true").lower() in ("1", "true", "yes")
    trust = opts.get("trustservercertificate", "true").lower() in ("1", "true", "yes")
    # Build ODBC connection string (semicolon-separated, no spaces around =)
    conn_parts = [
        f"DRIVER={{{ODBC_DRIVER}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
    ]
    if uid:
        conn_parts.append(f"UID={uid}")
    if pwd:
        conn_parts.append(f"PWD={pwd}")
    conn_parts.append("Encrypt=yes" if encrypt else "Encrypt=no")
    conn_parts.append("TrustServerCertificate=yes" if trust else "TrustServerCertificate=no")
    return ";".join(conn_parts)


def _build_engine_url(raw: str):
    """Build a SQLAlchemy engine from DATABASE_URL (Prisma or mssql+pyodbc style)."""
    raw = raw.strip()
    # Prisma-style: sqlserver://host:port;database=db;user=u;password=p;...
    if raw.startswith("sqlserver://") and ";" in raw:
        odbc_str = _prisma_to_odbc_connect(raw)
        quoted = urllib.parse.quote_plus(odbc_str)
        return create_engine(f"mssql+pyodbc:///?odbc_connect={quoted}")
    # Standard URL: ensure mssql+pyodbc and driver set
    url = raw
    if url.startswith("sqlserver://"):
        url = "mssql+pyodbc://" + url[len("sqlserver://") :]
    if not url.startswith("mssql+pyodbc://"):
        return create_engine(url)
    # Append driver if missing (avoids IM012)
    if "driver=" not in url.lower() and "odbc_connect=" not in url.lower():
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}driver={urllib.parse.quote_plus(ODBC_DRIVER)}&TrustServerCertificate=yes"
    return create_engine(url)


def main() -> None:
    try:
        engine = _build_engine_url(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
            count = result.scalar()
        print(f"job_postings row count: {count}")
    except (ImportError, OSError) as e:
        if "libodbc" in str(e) or "pyodbc" in str(e).lower():
            print(
                "ERROR: ODBC driver not found. Install system dependencies first.\n"
                "  On Ubuntu/Pop!_OS/Debian:\n"
                "    sudo apt-get update && sudo apt-get install -y unixodbc unixodbc-dev\n"
                "  Then install Microsoft ODBC Driver for SQL Server:\n"
                "    https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server\n",
                file=sys.stderr,
            )
        raise SystemExit(1) from e

if __name__ == "__main__":
    main()
