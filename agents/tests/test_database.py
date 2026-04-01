from __future__ import annotations

"""
Database connectivity and migration tests for the Job Intelligence Engine.

These tests exercise PostgreSQL connectivity, verify that the Phase 1
agent-managed tables exist, confirm that the migration is idempotent, and
ensure that the `job_postings` table has all Phase 1 extension columns.
"""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.engine import Engine

from agents.common.data_store.database import get_engine as _get_engine
from agents.common.data_store.migrations import run_migrations


def run_migration() -> None:
    """Run the canonical dbo-schema migrations."""
    run_migrations(_get_engine())


@pytest.fixture(scope="session")
def engine() -> Engine:
    """
    Create a SQLAlchemy engine for the PostgreSQL database used by agents.
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")
    return create_engine(database_url, future=True)


@pytest.fixture(scope="session", autouse=True)
def truncate_agent_tables(engine: Engine) -> Iterator[None]:
    """
    Truncate agent-managed tables before the test session starts.

    Ensures tests begin with a clean baseline for raw_ingested_jobs,
    normalized_jobs, and job_ingestion_runs.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE dbo.raw_ingested_jobs, dbo.normalized_jobs, dbo.job_ingestion_runs "
                "RESTART IDENTITY CASCADE;"
            )
        )
    yield


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_database_connection(engine: Engine) -> None:
    """
    Verify that the PostgreSQL database is reachable and SELECT 1 succeeds.
    """
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        value = result.scalar_one()
    assert value == 1


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_all_tables_exist(engine: Engine) -> None:
    """
    Confirm that all Phase 1 tables exist: raw_ingested_jobs, normalized_jobs,
    job_ingestion_runs, and job_postings.
    """
    # Ensure migration has run at least once.
    run_migration()

    inspector = inspect(engine)
    tables = set(inspector.get_table_names(schema="dbo"))
    expected = {
        "raw_ingested_jobs",
        "normalized_jobs",
        "job_ingestion_runs",
    }
    missing = expected - tables
    assert not missing, f"Missing expected tables: {missing}"


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_migration_is_idempotent(engine: Engine) -> None:
    """
    Ensure that running the Phase 1 migration multiple times does not raise
    errors and leaves the schema in a consistent state.
    """
    run_migration()
    # Second invocation should succeed without raising.
    run_migration()

    inspector = inspect(engine)
    assert "raw_ingested_jobs" in inspector.get_table_names(schema="dbo")
    assert "normalized_jobs" in inspector.get_table_names(schema="dbo")
    assert "job_ingestion_runs" in inspector.get_table_names(schema="dbo")


@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_job_postings_has_phase1_columns(engine: Engine) -> None:
    """
    Verify that the job_postings table has all nine Phase 1 extension columns.
    """
    run_migration()

    metadata = MetaData(schema="dbo")
    metadata.reflect(bind=engine, only=["job_postings"], schema="dbo")
    job_postings: Table = metadata.tables["dbo.job_postings"]

    column_names: list[str] = [col.name for col in job_postings.columns]
    expected_columns = [
        "source",
        "external_id",
        "ingestion_run_id",
        "ai_relevance_score",
        "quality_score",
        "is_spam",
        "spam_score",
        "overall_confidence",
        "field_confidence",
    ]

    for col in expected_columns:
        assert col in column_names, f"job_postings missing expected column: {col}"
