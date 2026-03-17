"""Phase 2 migration: extraction pipeline tables.

Creates the following tables if they do not already exist:
    * extracted_intelligence — 6-dimension extraction results per job record
    * llm_audit_log — centralized audit log for all LLM calls

Safe to run multiple times (IF NOT EXISTS semantics).
"""

from __future__ import annotations

import os

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

log = structlog.get_logger()


EXTRACTED_INTELLIGENCE_SQL = """
CREATE TABLE IF NOT EXISTS dbo.extracted_intelligence (
    id SERIAL PRIMARY KEY,
    normalized_job_id INTEGER NOT NULL,
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
    extraction_failed BOOLEAN DEFAULT FALSE
);
"""

EXTRACTED_INTELLIGENCE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_extracted_intelligence_norm_id ON dbo.extracted_intelligence (normalized_job_id);",
]


LLM_AUDIT_LOG_SQL = """
CREATE TABLE IF NOT EXISTS dbo.llm_audit_log (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    prompt_hash VARCHAR(64) NOT NULL,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    latency_ms INTEGER NOT NULL,
    token_count INTEGER NOT NULL,
    cost_usd DOUBLE PRECISION NOT NULL,
    success BOOLEAN NOT NULL,
    error_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

LLM_AUDIT_LOG_INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_llm_audit_log_agent ON dbo.llm_audit_log (agent_name);",
    "CREATE INDEX IF NOT EXISTS ix_llm_audit_log_created ON dbo.llm_audit_log (created_at);",
]


def get_engine() -> Engine:
    """Construct a SQLAlchemy engine using PYTHON_DATABASE_URL."""
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")

    log.info("migration_using_database_url", url_prefix=database_url.split("@")[0])
    return create_engine(database_url)


def run_migration() -> None:
    """Execute the extraction tables migration idempotently."""
    engine = get_engine()

    log.info("migration_phase2_start")
    with engine.begin() as conn:
        log.info("migration_create_extracted_intelligence")
        conn.execute(text(EXTRACTED_INTELLIGENCE_SQL))
        for stmt in EXTRACTED_INTELLIGENCE_INDEXES:
            conn.execute(text(stmt))

        log.info("migration_create_llm_audit_log")
        conn.execute(text(LLM_AUDIT_LOG_SQL))
        for stmt in LLM_AUDIT_LOG_INDEXES:
            conn.execute(text(stmt))

    log.info("migration_phase2_complete")


if __name__ == "__main__":
    run_migration()
