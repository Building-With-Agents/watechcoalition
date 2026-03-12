from __future__ import annotations

"""
SQLAlchemy ORM model tests for the Job Intelligence Engine.

These tests exercise basic CRUD behavior for the Phase 1 agent-managed
tables: raw_ingested_jobs, normalized_jobs, and job_ingestion_runs.
"""

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from agents.common.data_store.models import (
    Base,
    JobIngestionRun,
    NormalizedJob,
    RawIngestedJob,
)


@pytest.fixture(scope="session")
def engine() -> Engine:
    """
    Create a SQLAlchemy engine for the PostgreSQL database used by agents.
    """
    database_url = os.getenv("PYTHON_DATABASE_URL")
    if not database_url:
        raise RuntimeError("PYTHON_DATABASE_URL is not set")
    engine = create_engine(database_url, future=True)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="session", autouse=True)
def truncate_agent_tables(engine: Engine) -> Iterator[None]:
    """
    Truncate agent-managed tables before the test session starts.

    Provides a clean baseline and avoids cross-test contamination.
    """
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE raw_ingested_jobs, normalized_jobs, job_ingestion_runs "
                "RESTART IDENTITY CASCADE;"
            )
        )
    yield


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    """
    Provide a SQLAlchemy Session for model tests.
    """
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as session:
        yield session



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_insert_raw_ingested_job(session: Session) -> None:
    """
    Insert a RawIngestedJob row and read it back, verifying that core fields
    round-trip correctly.
    """
    ingestion_run_id = "test_models_raw_ingested"
    job = RawIngestedJob(
        source="test_source",
        external_id="ext-1",
        raw_payload_hash="hash-1",
        ingestion_run_id=ingestion_run_id,
        raw_text="test raw text",
        raw_metadata_json={"foo": "bar"},
    )
    session.add(job)
    session.commit()

    fetched = (
        session.execute(
            select(RawIngestedJob).where(RawIngestedJob.raw_payload_hash == "hash-1")
        )
        .scalars()
        .one()
    )
    assert fetched.source == "test_source"
    assert fetched.external_id == "ext-1"
    assert fetched.raw_metadata_json["foo"] == "bar"

    session.execute(
        delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
    )
    session.commit()



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_insert_normalized_job(session: Session) -> None:
    """
    Insert a NormalizedJob row and read it back, verifying the validation_status
    field is persisted correctly.
    """
    ingestion_run_id = "test_models_normalized"
    job = NormalizedJob(
        external_id="ext-2",
        source="test_source",
        ingestion_run_id=ingestion_run_id,
        raw_payload_hash="hash-2",
        title="Title",
        company="Company",
        location=None,
        salary_min=None,
        salary_max=None,
        salary_currency=None,
        salary_period=None,
        employment_type=None,
        date_posted=None,
        description=None,
        validation_status="valid",
        quarantine_reason=None,
    )
    session.add(job)
    session.commit()

    fetched = (
        session.execute(
            select(NormalizedJob).where(NormalizedJob.raw_payload_hash == "hash-2")
        )
        .scalars()
        .one()
    )
    assert fetched.validation_status == "valid"

    session.execute(
        delete(NormalizedJob).where(NormalizedJob.ingestion_run_id == ingestion_run_id)
    )
    session.commit()



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_insert_job_ingestion_run(session: Session) -> None:
    """
    Insert a JobIngestionRun row and update its status from 'running' to
    'complete', verifying that the update persists.
    """
    run = JobIngestionRun(
        source="test_source",
        status="running",
        record_count=0,
        dedup_count=0,
        error_count=0,
    )
    session.add(run)
    session.commit()

    run_id = run.id
    fetched = session.get(JobIngestionRun, run_id)
    assert fetched is not None
    assert fetched.status == "running"

    fetched.status = "complete"
    session.commit()

    updated = session.get(JobIngestionRun, run_id)
    assert updated is not None
    assert updated.status == "complete"

    session.execute(delete(JobIngestionRun).where(JobIngestionRun.id == run_id))
    session.commit()



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_raw_payload_hash_unique(session: Session) -> None:
    """
    Verify that raw_payload_hash is enforced as unique in raw_ingested_jobs by
    attempting to insert two rows with the same hash and expecting an
    IntegrityError.
    """
    ingestion_run_id = "test_models_unique"
    job1 = RawIngestedJob(
        source="test_source",
        external_id="ext-a",
        raw_payload_hash="dup-hash",
        ingestion_run_id=ingestion_run_id,
        raw_text="text1",
        raw_metadata_json={},
    )
    session.add(job1)
    session.commit()

    job2 = RawIngestedJob(
        source="test_source",
        external_id="ext-b",
        raw_payload_hash="dup-hash",
        ingestion_run_id=ingestion_run_id,
        raw_text="text2",
        raw_metadata_json={},
    )
    session.add(job2)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()
    session.execute(
        delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
    )
    session.commit()



@pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
def test_unicode_fields(session: Session) -> None:
    """
    Insert a RawIngestedJob with Unicode content in raw_metadata_json and read
    it back, verifying that the Unicode fields round-trip without corruption.
    """
    ingestion_run_id = "test_models_unicode"
    meta = {
        "title": "シニアデータエンジニア",
        "company": "شركة التقنية الحديثة",
        "location": "Seattle 🚀",
    }
    job = RawIngestedJob(
        source="test_source",
        external_id="ext-unicode",
        raw_payload_hash="hash-unicode",
        ingestion_run_id=ingestion_run_id,
        raw_text="unicode test",
        raw_metadata_json=meta,
    )
    session.add(job)
    session.commit()

    fetched = (
        session.execute(
            select(RawIngestedJob).where(RawIngestedJob.raw_payload_hash == "hash-unicode")
        )
        .scalars()
        .one()
    )
    assert fetched.raw_metadata_json == meta

    session.execute(
        delete(RawIngestedJob).where(RawIngestedJob.ingestion_run_id == ingestion_run_id)
    )
    session.commit()

