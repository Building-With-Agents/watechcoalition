"""Idempotent database migrations for agent-managed tables.

Creates agent tables (raw_ingested_jobs, job_ingestion_runs, normalized_jobs)
and adds Phase 1 columns to the existing job_postings table.

Optional legacy raw-SQL scripts (pre-consolidation paths) live under
``legacy_migrations/`` for reference only; use :func:`run_migrations` for the app.

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

_EXTRACTED_INTELLIGENCE_DDL = """
CREATE TABLE IF NOT EXISTS dbo.extracted_intelligence (
    id SERIAL PRIMARY KEY,
    normalized_job_id INTEGER,
    extraction_version TEXT NOT NULL,
    extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    extraction_model TEXT NOT NULL,
    extraction_tokens_used INTEGER NOT NULL DEFAULT 0,
    extraction_cost_usd DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    skills JSONB NOT NULL DEFAULT '[]',
    tools JSONB NOT NULL DEFAULT '[]',
    tasks JSONB NOT NULL DEFAULT '[]',
    responsibilities JSONB NOT NULL DEFAULT '[]',
    context JSONB NOT NULL DEFAULT '[]',
    overall_confidence DOUBLE PRECISION,
    extraction_warnings JSONB DEFAULT '[]',
    extraction_failed BOOLEAN NOT NULL DEFAULT FALSE,
    extraction_metadata JSONB
);
CREATE INDEX IF NOT EXISTS ix_extracted_intelligence_normalized_job_id
    ON dbo.extracted_intelligence (normalized_job_id);
CREATE INDEX IF NOT EXISTS ix_extracted_intelligence_extracted_at
    ON dbo.extracted_intelligence (extracted_at);
CREATE INDEX IF NOT EXISTS ix_extracted_intelligence_failed
    ON dbo.extracted_intelligence (extraction_failed);
"""

_LLM_AUDIT_LOG_DDL = """
CREATE TABLE IF NOT EXISTS dbo.llm_audit_log (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    token_count INTEGER,
    cost_usd DOUBLE PRECISION,
    success BOOLEAN NOT NULL,
    error_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_llm_audit_log_agent_name ON dbo.llm_audit_log (agent_name);
CREATE INDEX IF NOT EXISTS ix_llm_audit_log_created_at ON dbo.llm_audit_log (created_at);
CREATE INDEX IF NOT EXISTS ix_llm_audit_log_success ON dbo.llm_audit_log (success);
"""

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

_NORMALIZED_JOBS_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS requirements TEXT",
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS responsibilities TEXT",
]

# Backfill token columns when llm_audit_log predates full DDL (idempotent)
_LLM_AUDIT_LOG_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS input_tokens INTEGER",
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS output_tokens INTEGER",
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS token_count INTEGER",
]


def run_migrations(engine: Engine) -> None:
    """Create agent tables and add Phase 1 columns. Safe to run multiple times."""
    log.info("migrations_start")

    # 0. Ensure the dbo schema exists (required by ORM models)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dbo"))

    # 1. Create agent-managed tables via SQLAlchemy metadata
    Base.metadata.create_all(engine)
    log.info("migrations_tables_created")

    # 2. Create extracted_intelligence table
    with engine.begin() as conn:
        conn.execute(text(_EXTRACTED_INTELLIGENCE_DDL))
    log.info("migrations_extracted_intelligence_created")

    # 3. Create llm_audit_log table
    with engine.begin() as conn:
        conn.execute(text(_LLM_AUDIT_LOG_DDL))
    log.info("migrations_llm_audit_log_created")

    # 3b. Add token columns if table was created before they existed in DDL
    for stmt in _LLM_AUDIT_LOG_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_llm_audit_log_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

    # 4. Add Phase 1 columns to existing tables.
    #    Each ALTER runs in its own transaction so a single failure
    #    (e.g. job_postings not yet created) doesn't abort the rest.
    for stmt in _PHASE1_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

    for stmt in _NORMALIZED_JOBS_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_normalized_jobs_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

    log.info("migrations_complete")
