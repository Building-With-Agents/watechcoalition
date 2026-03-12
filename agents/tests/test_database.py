from __future__ import annotations

"""
Database connectivity and migration tests for the Job Intelligence Engine.

These tests exercise PostgreSQL connectivity, verify that the Phase 1
agent-managed tables exist, confirm that the migration is idempotent, and
ensure that the `job_postings` table has all Phase 1 extension columns.
"""

import importlib.util
import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import MetaData, Table, create_engine, inspect, text
from sqlalchemy.engine import Engine


def _load_run_migration():
    """
    Dynamically load the Phase 1 migration module from its file path.

    The migration file is named `001_phase1_tables.py`, which is not a valid
    Python identifier for direct imports, so we load it via importlib.
    """
    root = Path(__file__).resolve().parents[1]
    path = root / "common" / "data_store" / "migrations" / "001_phase1_tables.py"
    spec = importlib.util.spec_from_file_location("phase1_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load migration module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[assignment]
    return module.run_migration


run_migration = _load_run_migration()


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
                "TRUNCATE TABLE raw_ingested_jobs, normalized_jobs, job_ingestion_runs "
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
    tables = set(inspector.get_table_names())
    expected = {
        "raw_ingested_jobs",
        "normalized_jobs",
        "job_ingestion_runs",
        "job_postings",
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
    assert "raw_ingested_jobs" in inspector.get_table_names()
    assert "normalized_jobs" in inspector.get_table_names()
    assert "job_ingestion_runs" in inspector.get_table_names()



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_job_postings_has_phase1_columns(engine: Engine) -> None:
    """
    Verify that the job_postings table has all nine Phase 1 extension columns.
    """
    run_migration()

    metadata = MetaData()
    metadata.reflect(bind=engine, only=["job_postings"])
    job_postings: Table = metadata.tables["job_postings"]

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

