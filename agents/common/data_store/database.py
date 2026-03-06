"""Database engine, session factory, and connection utilities.

All agents share one engine per process. The connection URL comes from
``PYTHON_DATABASE_URL`` (``postgresql+psycopg2://...``).
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import Generator

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

log = structlog.get_logger()

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine (created on first call)."""
    global _engine
    if _engine is None:
        url = os.getenv("PYTHON_DATABASE_URL")
        if not url:
            raise RuntimeError(
                "PYTHON_DATABASE_URL is not set. Expected format: postgresql+psycopg2://user:pass@host:port/db"
            )
        _engine = create_engine(url, pool_pre_ping=True, pool_size=5)
        log.info("db_engine_created", url=url.split("@")[-1])  # log host only, no creds
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Return a singleton sessionmaker bound to the shared engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session_factory


@contextlib.contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager that yields a session and handles commit/rollback."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connection() -> bool:
    """Return True if a simple SELECT 1 succeeds against the database."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        log.warning("db_connection_check_failed", error=str(exc))
        return False
