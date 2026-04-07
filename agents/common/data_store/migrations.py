"""Idempotent database migrations for all agent-managed tables.

SQLAlchemy is the single database authority. Creates agent tables, adds
enrichment columns to job_postings, and ensures reference tables are
accessible. Prisma/MSSQL is being phased out.

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


def _drop_legacy_employer_profiles_if_serial_pk(engine: Engine) -> None:
    """Replace pre-UUID ``employer_profiles`` (SERIAL id) so ORM/create_all can recreate."""
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'dbo' AND table_name = 'employer_profiles'
                )
                """
            )
        ).scalar()
        if not exists:
            return
        row = conn.execute(
            text(
                """
                SELECT data_type FROM information_schema.columns
                WHERE table_schema = 'dbo' AND table_name = 'employer_profiles'
                  AND column_name = 'id'
                """
            )
        ).first()
        if row and row[0] in ("integer", "bigint", "smallint"):
            conn.execute(text("DROP TABLE IF EXISTS dbo.employer_profiles CASCADE"))
            log.info("migrations_employer_profiles_legacy_serial_dropped")


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

# Enrichment columns on dbo.job_postings (idempotent via IF NOT EXISTS).
# Phase 1 (Weeks 3-4): ingestion + extraction metadata.
# Phase 1b (Week 5): enrichment output — SOC, NAICS, temporal, borderplex, dedup.
_JOB_POSTINGS_ALTER_STATEMENTS = [
    # Phase 1 — ingestion & extraction metadata
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS source TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS external_id TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS ingestion_run_id TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS ai_relevance_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS is_spam BOOLEAN",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS spam_score DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS spam_tier TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS overall_confidence DOUBLE PRECISION",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS field_confidence JSONB",
    # Phase 1b — Week 5 enrichment output (SOC persisted here; legacy Prisma column may be occupation_code)
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS soc_code TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS naics_code TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS temporal_period TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS borderplex_subregion TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS is_duplicate BOOLEAN DEFAULT FALSE",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS duplicate_cluster_id UUID",
    # Fuzzy dedup (IMP-018): cached embedding + content hash for same-company window search
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS dedup_text_hash TEXT",
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS dedup_embedding vector(1536)",
    # Zip code (flywheel #161): resolved during normalization from posting or postal_geo_data lookup
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10)",
    # Link to dbo.employer_profiles (UUID PK) after enrichment upsert
    "ALTER TABLE dbo.job_postings ADD COLUMN IF NOT EXISTS employer_profile_id UUID REFERENCES dbo.employer_profiles(id)",
]

# Legacy Prisma cleanup: drop FK constraints and make NOT NULL columns nullable (#159).
# Pipeline stores location directly on job_postings row, not via company_addresses FK.
_JOB_POSTINGS_LEGACY_CLEANUP = [
    # Drop FK to company_addresses — pipeline stores location directly on job_postings
    "ALTER TABLE dbo.job_postings DROP CONSTRAINT IF EXISTS fk_job_postings_company_addresses1",
    # Drop FK to companies — pipeline resolves company_id via _resolve_or_create_company
    "ALTER TABLE dbo.job_postings DROP CONSTRAINT IF EXISTS fk_job_postings_companies1",
    # Make legacy NOT NULL columns nullable
    "ALTER TABLE dbo.job_postings ALTER COLUMN location_id DROP NOT NULL",
    "ALTER TABLE dbo.job_postings ALTER COLUMN county DROP NOT NULL",
    "ALTER TABLE dbo.job_postings ALTER COLUMN zip DROP NOT NULL",
    "ALTER TABLE dbo.job_postings ALTER COLUMN publish_date DROP NOT NULL",
    "ALTER TABLE dbo.job_postings ALTER COLUMN unpublish_date DROP NOT NULL",
]

_NORMALIZED_JOBS_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS requirements TEXT",
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS responsibilities TEXT",
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10)",
    "ALTER TABLE dbo.raw_ingested_jobs ADD COLUMN IF NOT EXISTS zip_code VARCHAR(10)",
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS naics_code TEXT",
    "ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS employer_metadata JSONB",
]

# Company HQ / location fields for enrichment resolve_location (#110)
_COMPANIES_LOCATION_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.companies ADD COLUMN IF NOT EXISTS city TEXT",
    "ALTER TABLE dbo.companies ADD COLUMN IF NOT EXISTS state TEXT",
    "ALTER TABLE dbo.companies ADD COLUMN IF NOT EXISTS normalized_location TEXT",
]

_UUID_REGEX = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"

# Backfill token columns when llm_audit_log predates full DDL (idempotent)
_LLM_AUDIT_LOG_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS input_tokens INTEGER",
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS output_tokens INTEGER",
    "ALTER TABLE dbo.llm_audit_log ADD COLUMN IF NOT EXISTS token_count INTEGER",
]

# extracted_intelligence created before ExtractionMetadata JSONB column existed
_EXTRACTED_INTELLIGENCE_ALTER_STATEMENTS = [
    "ALTER TABLE dbo.extracted_intelligence ADD COLUMN IF NOT EXISTS extraction_metadata JSONB",
]

# NAICS reference (PostgreSQL). Azure SQL / MSSQL: table is created via SQLAlchemy
# create_all when running seed_naics.py or agent migrations against that dialect.
_NAICS_DDL = """
CREATE TABLE IF NOT EXISTS dbo.naics (
    naics_code TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    seq_no INTEGER,
    createdat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updatedat TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

# Week 7 Pair B — weekly analytics aggregates (issues #180 / #181)
_WEEK7_ANALYTICS_AGGREGATES_DDL = """
CREATE TABLE IF NOT EXISTS dbo.sector_summary_weekly (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    sector TEXT NOT NULL,
    posting_count INTEGER NOT NULL,
    avg_salary DOUBLE PRECISION,
    median_salary DOUBLE PRECISION
);
CREATE TABLE IF NOT EXISTS dbo.geo_demand_weekly (
    id SERIAL PRIMARY KEY,
    week_start DATE NOT NULL,
    borderplex_subregion VARCHAR(32) NOT NULL,
    posting_count INTEGER NOT NULL
);
"""

_SERIAL_SEQUENCE_TARGETS = (
    ("raw_ingested_jobs", "id"),
    ("job_ingestion_runs", "id"),
    ("normalized_jobs", "id"),
    ("normalization_quarantine", "id"),
    ("extracted_intelligence", "id"),
    ("llm_audit_log", "id"),
    ("employer_profiles", "id"),
)


def _sync_serial_sequence(engine: Engine, *, table_name: str, column_name: str = "id") -> None:
    """Advance a PostgreSQL serial/identity sequence to at least ``MAX(column)``."""
    try:
        with engine.begin() as conn:
            seq_name = conn.execute(
                text(
                    "SELECT pg_get_serial_sequence(CAST(:table_name AS text), CAST(:column_name AS text))"
                ),
                {"table_name": f"dbo.{table_name}", "column_name": column_name},
            ).scalar()
            if not seq_name:
                return

            max_value = conn.execute(
                text(f'SELECT COALESCE(MAX("{column_name}"), 0) FROM dbo.{table_name}')
            ).scalar()
            max_value = int(max_value or 0)
            if max_value > 0:
                conn.execute(
                    text("SELECT setval(CAST(:seq AS regclass), :v, true)"),
                    {"seq": seq_name, "v": max_value},
                )
            else:
                conn.execute(
                    text("SELECT setval(CAST(:seq AS regclass), 1, false)"),
                    {"seq": seq_name},
                )
    except Exception as exc:
        log.warning(
            "migration_sequence_sync_skipped",
            table_name=table_name,
            column_name=column_name,
            error=str(exc),
        )


def _sync_agent_serial_sequences(engine: Engine) -> None:
    for table_name, column_name in _SERIAL_SEQUENCE_TARGETS:
        _sync_serial_sequence(engine, table_name=table_name, column_name=column_name)


def _ensure_duplicate_cluster_id_uuid(engine: Engine) -> None:
    """Convert ``job_postings.duplicate_cluster_id`` to ``UUID`` when legacy text remains."""
    try:
        with engine.begin() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'dbo'
                      AND table_name = 'job_postings'
                      AND column_name = 'duplicate_cluster_id'
                    """
                )
            ).first()
            if not row:
                return
            data_type = str(row[0] or "").lower()
            if data_type == "uuid":
                return

            invalid_count = conn.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM dbo.job_postings
                    WHERE duplicate_cluster_id IS NOT NULL
                      AND BTRIM(duplicate_cluster_id::text) <> ''
                      AND NOT (duplicate_cluster_id::text ~* :uuid_regex)
                    """
                ),
                {"uuid_regex": _UUID_REGEX},
            ).scalar()
            invalid_count = int(invalid_count or 0)
            if invalid_count:
                log.warning(
                    "migration_duplicate_cluster_id_invalid_values_reset_to_null",
                    invalid_count=invalid_count,
                )

            conn.execute(
                text(
                    """
                    ALTER TABLE dbo.job_postings
                    ALTER COLUMN duplicate_cluster_id TYPE UUID
                    USING CASE
                        WHEN duplicate_cluster_id IS NULL THEN NULL
                        WHEN BTRIM(duplicate_cluster_id::text) = '' THEN NULL
                        WHEN duplicate_cluster_id::text ~* :uuid_regex THEN duplicate_cluster_id::uuid
                        ELSE NULL
                    END
                    """
                ),
                {"uuid_regex": _UUID_REGEX},
            )
    except Exception as exc:
        log.warning(
            "migration_duplicate_cluster_id_uuid_skipped",
            error=str(exc),
        )


def run_migrations(engine: Engine) -> None:
    """Create agent tables and add Phase 1 columns. Safe to run multiple times."""
    log.info("migrations_start")

    # 0. Ensure the dbo schema exists (required by ORM models)
    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS dbo"))

    # 0b. Drop legacy SERIAL-key employer_profiles before create_all (PostgreSQL only)
    _drop_legacy_employer_profiles_if_serial_pk(engine)

    # 1. Create agent-managed tables via SQLAlchemy metadata
    Base.metadata.create_all(engine)
    log.info("migrations_tables_created")

    # 1b. Seed analytics pipeline state singleton (id=1) for DB-backed watermark
    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        """
                        INSERT INTO dbo.analytics_pipeline_state (id, last_successful_run_at, updated_at)
                        VALUES (1, NULL, NOW())
                        ON CONFLICT (id) DO NOTHING
                        """
                    )
                )
            log.info("migrations_analytics_pipeline_state_seeded")
        except Exception as exc:
            log.warning(
                "migration_analytics_pipeline_state_seed_skipped",
                error=str(exc),
            )

    # 2. Create extracted_intelligence table (DDL may add indexes idempotently)
    with engine.begin() as conn:
        conn.execute(text(_EXTRACTED_INTELLIGENCE_DDL))
    log.info("migrations_extracted_intelligence_created")

    for stmt in _EXTRACTED_INTELLIGENCE_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_extracted_intelligence_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

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

    # 4. employer_profiles is created via Base.metadata.create_all (UUID PK, FK to companies)

    # 4b. Create naics reference table (PostgreSQL DDL; other dialects rely on create_all)
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            conn.execute(text(_NAICS_DDL))
        log.info("migrations_naics_created")

    # 4c. Week 7 analytics aggregate tables (PostgreSQL DDL; ORM also registers via create_all)
    if engine.dialect.name == "postgresql":
        try:
            with engine.begin() as conn:
                conn.execute(text(_WEEK7_ANALYTICS_AGGREGATES_DDL))
            log.info("migrations_week7_analytics_aggregates_created")
        except Exception as exc:
            log.warning(
                "migration_week7_analytics_aggregates_skipped",
                error=str(exc),
            )

    # 5. Add enrichment columns to dbo.job_postings (and related).
    #    Each ALTER runs in its own transaction so a single failure
    #    (e.g. job_postings not yet created) doesn't abort the rest.
    for stmt in _JOB_POSTINGS_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

    _ensure_duplicate_cluster_id_uuid(engine)
    _sync_agent_serial_sequences(engine)

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

    for stmt in _COMPANIES_LOCATION_ALTER_STATEMENTS:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_companies_location_alter_skipped",
                statement=stmt,
                error=str(exc),
            )

    # 6. Drop legacy Prisma FK constraints and make NOT NULL columns nullable (#159).
    #    Pipeline stores location directly on job_postings, not via company_addresses.
    for stmt in _JOB_POSTINGS_LEGACY_CLEANUP:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception as exc:
            log.warning(
                "migration_legacy_cleanup_skipped",
                statement=stmt,
                error=str(exc),
            )

    log.info("migrations_complete")
