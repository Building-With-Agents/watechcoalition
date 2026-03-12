from __future__ import annotations

"""
SQLAlchemy ORM models for agent-managed tables in the Job Intelligence Engine.

This module defines the canonical Phase 1 tables:
    - raw_ingested_jobs
    - normalized_jobs
    - job_ingestion_runs

These tables live alongside the existing Prisma-managed schema and are owned
exclusively by the Python agents. They are designed for PostgreSQL via
SQLAlchemy (psycopg2) and should be created via the migration scripts in
`agents/common/data_store/migrations/`.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RawIngestedJob(Base):
    """
    ORM model for the `raw_ingested_jobs` ingestion staging table.

    Each row represents a single raw job posting as ingested from an external
    source (JSearch API or web scraping) before normalization. Deduplication is
    performed against `raw_payload_hash`, which is enforced as a unique index.
    """

    __tablename__ = "raw_ingested_jobs"

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source: str = Column(Text, nullable=False)
    external_id: str = Column(Text, nullable=False)
    raw_payload_hash: str = Column(Text, nullable=False, unique=True)
    ingestion_run_id: str = Column(Text, nullable=False)
    raw_text: str = Column(Text, nullable=False)
    raw_metadata_json: dict = Column(JSONB, nullable=False)
    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    error_reason: str | None = Column(Text, nullable=True)

    __table_args__ = (
        Index(
            "ux_raw_ingested_jobs_raw_payload_hash",
            "raw_payload_hash",
            unique=True,
        ),
    )


class NormalizedJob(Base):
    """
    ORM model for the `normalized_jobs` table.

    Records in this table represent source-agnostic JobRecord instances after
    schema validation and normalization. Quarantined records are retained with
    a `validation_status` of \"quarantined\" and an accompanying
    `quarantine_reason`.
    """

    __tablename__ = "normalized_jobs"

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    external_id: str = Column(Text, nullable=False)
    source: str = Column(Text, nullable=False)
    ingestion_run_id: str = Column(Text, nullable=False)
    raw_payload_hash: str = Column(Text, nullable=False)

    title: str = Column(Text, nullable=False)
    company: str = Column(Text, nullable=False)
    location: str | None = Column(Text, nullable=True)

    salary_min: float | None = Column(Float, nullable=True)
    salary_max: float | None = Column(Float, nullable=True)
    salary_currency: str | None = Column(Text, nullable=True)
    salary_period: str | None = Column(Text, nullable=True)

    employment_type: str | None = Column(Text, nullable=True)
    date_posted: datetime | None = Column(DateTime(timezone=True), nullable=True)

    description: str | None = Column(Text, nullable=True)

    validation_status: str = Column(String(length=32), nullable=False)
    quarantine_reason: str | None = Column(Text, nullable=True)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class JobIngestionRun(Base):
    """
    ORM model for the `job_ingestion_runs` table.

    Each row tracks a single ingestion batch run, including counts for ingested
    records, deduplicated records, and errors, along with status transitions
    and timestamps.
    """

    __tablename__ = "job_ingestion_runs"

    id: uuid.UUID = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source: str = Column(Text, nullable=False)
    status: str = Column(String(length=32), nullable=False)

    record_count: int = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    dedup_count: int = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    error_count: int = Column(
        Integer,
        nullable=False,
        server_default="0",
    )

    started_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: datetime | None = Column(
        DateTime(timezone=True),
        nullable=True,
    )

