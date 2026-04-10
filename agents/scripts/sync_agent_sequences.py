"""
Resync PostgreSQL SERIAL/IDENTITY sequences for agent tables to MAX(id).

Use after pg_restore, COPY with explicit ids, or when inserts fail with:
  duplicate key value violates unique constraint "..._pkey" Key (id)=(N) already exists.

Prerequisites:
  - PYTHON_DATABASE_URL in .env

Usage (from repo root):
  python agents/scripts/sync_agent_sequences.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_REPO_ROOT / ".env")

import structlog  # noqa: E402

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
log = structlog.get_logger()


def main() -> None:
    from agents.common.data_store.database import get_engine
    from agents.common.data_store.migrations import sync_postgresql_agent_sequences

    try:
        engine = get_engine()
    except RuntimeError as exc:
        log.error("database_not_configured", error=str(exc))
        sys.exit(1)

    if engine.dialect.name != "postgresql":
        log.error("not_postgresql", dialect=engine.dialect.name)
        sys.exit(1)

    sync_postgresql_agent_sequences(engine)
    log.info("sync_agent_sequences_complete")
    print("OK: PostgreSQL agent table sequences resynced.")  # noqa: T201


if __name__ == "__main__":
    main()
