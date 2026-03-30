"""Read-only SQLAlchemy engine for the Streamlit dashboard.

Separate singleton from ``agents.common.data_store.get_engine`` so the dashboard
does not share the pipeline writer pool. Connections use PostgreSQL
``default_transaction_read_only=on`` so accidental writes fail fast.

Optional ``PYTHON_DATABASE_URL_READONLY`` points at a dedicated read-only role;
otherwise ``PYTHON_DATABASE_URL`` is used with the session read-only flag.
"""

from __future__ import annotations

import os

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

log = structlog.get_logger()

_dashboard_engine: Engine | None = None


def get_dashboard_engine() -> Engine:
    """Return a singleton engine for dashboard queries (read-only transactions)."""
    global _dashboard_engine
    if _dashboard_engine is None:
        url = os.getenv("PYTHON_DATABASE_URL_READONLY") or os.getenv("PYTHON_DATABASE_URL")
        if not url:
            raise RuntimeError(
                "PYTHON_DATABASE_URL (or PYTHON_DATABASE_URL_READONLY) is not set. Expected postgresql+psycopg2://..."
            )
        _dashboard_engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=3,
            connect_args={"options": "-c default_transaction_read_only=on"},
        )
        log.info("dashboard_db_engine_created", url=url.split("@")[-1])
    return _dashboard_engine


def check_dashboard_db_connection() -> bool:
    """Return True if SELECT 1 succeeds on the dashboard engine."""
    try:
        engine = get_dashboard_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        log.warning("dashboard_db_connection_check_failed", error=str(exc))
        return False
