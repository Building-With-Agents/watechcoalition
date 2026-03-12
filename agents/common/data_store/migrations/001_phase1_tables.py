from __future__ import annotations

"""
Phase 1 migration: agent-managed tables and job_postings extensions.

This idempotent migration script:
    - Creates the following agent-owned tables if they do not already exist:
        * raw_ingested_jobs
        * normalized_jobs
        * job_ingestion_runs
    - Adds Phase 1 extension columns to the existing job_postings table:
        * source TEXT
        * external_id TEXT
        * ingestion_run_id TEXT
        * ai_relevance_score DOUBLE PRECISION
        * quality_score DOUBLE PRECISION
        * is_spam BOOLEAN
        * spam_score DOUBLE PRECISION
        * overall_confidence DOUBLE PRECISION
        * field_confidence JSONB

The migration is safe to run multiple times. It uses PostgreSQL syntax
(`IF NOT EXISTS`, JSONB) and connects via SQLAlchemy using the
`PYTHON_DATABASE_URL` environment variable (expected to be a
`postgresql+psycopg2://` URL).
"""

import os

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

log = structlog.get_logger()


RAW_INGESTED_JOBS_SQL = """
CREATE TABLE IF NOT EXISTS raw_ingested_jobs (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL UNIQUE,
    ingestion_run_id TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    raw_metadata_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    error_reason TEXT NULL
);
"""


NORMALIZED_JOBS_SQL = """
CREATE TABLE IF NOT EXISTS normalized_jobs (
    id UUID PRIMARY KEY,
    external_id TEXT NOT NULL,
    source TEXT NOT NULL,
    ingestion_run_id TEXT NOT NULL,
    raw_payload_hash TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NULL,
    salary_min DOUBLE PRECISION NULL,
    salary_max DOUBLE PRECISION NULL,
    salary_currency TEXT NULL,
    salary_period TEXT NULL,
    employment_type TEXT NULL,
    date_posted TIMESTAMPTZ NULL,
    description TEXT NULL,
    validation_status TEXT NOT NULL,
    quarantine_reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


JOB_INGESTION_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS job_ingestion_runs (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    record_count INTEGER NOT NULL DEFAULT 0,
    dedup_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL
);
"""


JOB_POSTINGS_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS job_postings (
    id TEXT PRIMARY KEY,
    title TEXT,
    company TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


JOB_POSTINGS_ALTERS = [
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS source TEXT;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS external_id TEXT;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS ingestion_run_id TEXT;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS ai_relevance_score DOUBLE PRECISION;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS is_spam BOOLEAN;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS spam_score DOUBLE PRECISION;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS overall_confidence DOUBLE PRECISION;",
    "ALTER TABLE job_postings ADD COLUMN IF NOT EXISTS field_confidence JSONB;",
]


def get_engine() -> Engine:
    """
    Construct a SQLAlchemy engine using PYTHON_DATABASE_URL.

    The environment variable is expected to contain a PostgreSQL connection
    string in `postgresql+psycopg2://` form. No credentials are hard-coded.
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")

    log.info("migration_using_database_url", url_prefix=database_url.split("@")[0])
    return create_engine(database_url)


def run_migration() -> None:
    """
    Execute the Phase 1 table and column migrations in an idempotent fashion.

    Each step logs progress via structlog and uses IF NOT EXISTS semantics so
    the script can be re-run safely without raising errors if objects already
    exist.
    """
    engine = get_engine()

    log.info("migration_phase1_start")
    with engine.begin() as conn:
        log.info("migration_create_raw_ingested_jobs")
        conn.execute(text(RAW_INGESTED_JOBS_SQL))

        log.info("migration_create_normalized_jobs")
        conn.execute(text(NORMALIZED_JOBS_SQL))

        log.info("migration_create_job_ingestion_runs")
        conn.execute(text(JOB_INGESTION_RUNS_SQL))

        log.info("migration_create_job_postings_minimal")
        conn.execute(text(JOB_POSTINGS_CREATE_SQL))

        for stmt in JOB_POSTINGS_ALTERS:
            log.info("migration_alter_job_postings", statement=stmt.strip())
            conn.execute(text(stmt))

    log.info("migration_phase1_complete")


if __name__ == "__main__":
    run_migration()

