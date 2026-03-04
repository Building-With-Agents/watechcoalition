"""Idempotent database migrations for agent-managed tables.

Creates agent tables (raw_ingested_jobs, job_ingestion_runs, normalized_jobs)
and adds Phase 1 columns to the existing job_postings table.

Usage:
    from agents.common.data_store.migrations import run_migrations
    from agents.common.data_store.database import get_engine
    run_migrations(get_engine())
"""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.engine import Engine

from agents.common.data_store.models import Base

log = structlog.get_logger()

# Phase 1 columns to add to dbo.job_postings (idempotent via IF NOT EXISTS)
_PHASE1_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS source TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS external_id TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS ingestion_run_id TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS ai_relevance_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS is_spam BOOLEAN",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS spam_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS overall_confidence DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS field_confidence JSONB",
]


def run_migrations(engine: Engine) -> None:
    """Create agent tables and add Phase 1 columns. Safe to run multiple times."""
    log.info("migrations_start")

    # 1. Create agent-managed tables via SQLAlchemy metadata
    Base.metadata.create_all(engine)
    log.info("migrations_tables_created")

    # 2. Add Phase 1 columns to existing job_postings table
    with engine.begin() as conn:
        for stmt in _PHASE1_ALTER_STATEMENTS:
            try:
                conn.execute(text(stmt))
            except Exception as exc:
                # Column may already exist or table may not exist yet — log and continue
                log.warning(
                    "migration_alter_skipped",
                    statement=stmt,
                    error=str(exc),
                )

    log.info("migrations_complete")
