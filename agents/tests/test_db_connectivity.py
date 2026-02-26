"""
Simple connectivity check for the Job Intelligence Engine database.

- Uses SQLAlchemy + pyodbc (no Prisma).
- Reads the connection URL from environment variables (no hardcoded credentials).
- Prints the row count from the job_postings table.

Connection resolution:
- Prefer PYTHON_DATABASE_URL (recommended for agents, mssql+pyodbc:// style).
- Fallback to DATABASE_URL *only* if it is already a SQLAlchemy/pyodbc URL.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


def load_env() -> None:
    """Load environment variables from .env files if present."""
    repo_root = Path(__file__).resolve().parents[2]
    candidate_paths = [
        repo_root / ".env",
        repo_root / "agents" / ".env",
        repo_root / "agents" / ".env.example",
    ]

    for env_path in candidate_paths:
        if env_path.exists():
            load_dotenv(env_path, override=False)
            break


def get_engine() -> Engine:
    """
    Build a SQLAlchemy engine using a pyodbc-style URL.

    Preferred variable:
    - PYTHON_DATABASE_URL (mssql+pyodbc://...)

    Fallback:
    - DATABASE_URL, but only if it already uses a SQLAlchemy-compatible
      driver prefix (e.g. mssql+pyodbc://). The default Prisma-style
      sqlserver:// URL will NOT work with SQLAlchemy.
    """
    url = os.getenv("PYTHON_DATABASE_URL")
    if not url:
        fallback = os.getenv("DATABASE_URL")
        if fallback and fallback.startswith("mssql+pyodbc://"):
            url = fallback

    if not url:
        raise RuntimeError(
            "No SQLAlchemy connection URL found. "
            "Set PYTHON_DATABASE_URL in your .env to a mssql+pyodbc:// URL."
        )

    return create_engine(url)


def main() -> None:
    load_env()
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM job_postings"))
        count = result.scalar_one()

    print(f"job_postings row count: {count}")


if __name__ == "__main__":
    main()

