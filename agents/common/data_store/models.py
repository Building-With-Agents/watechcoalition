"""SQLAlchemy ORM models for agent-managed tables.

All tables live in the ``dbo`` schema to match pgloader-migrated tables.
These tables are created by agents (via migrations.py), NOT by Prisma.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all agent models."""

    pass


# ---------------------------------------------------------------------------
# Ingestion tables
# ---------------------------------------------------------------------------


class RawIngestedJob(Base):
    """Staging table for raw job postings before normalization."""

    __tablename__ = "raw_ingested_jobs"
    __table_args__ = (
        UniqueConstraint("raw_payload_hash", name="uq_raw_ingested_jobs_hash"),
        Index("ix_raw_ingested_jobs_run_id", "ingestion_run_id"),
        Index("ix_raw_ingested_jobs_source_eid", "source", "external_id"),
        Index("ix_raw_ingested_jobs_status", "processing_status"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ingestion_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    region_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured location (replaces single ``location`` column)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_remote: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # URLs
    job_url: Mapped[str | None] = mapped_column(String(2083), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(2083), nullable=True)

    # Date & classification
    date_posted: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Salary (raw extraction)
    salary_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Raw payload
    raw_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Processing state
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class JobIngestionRun(Base):
    """Tracks each ingestion batch run for auditing and observability."""

    __tablename__ = "job_ingestion_runs"
    __table_args__ = (
        Index("ix_job_ingestion_runs_status", "status"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    region_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="running")
    total_fetched: Mapped[int] = mapped_column(Integer, default=0)
    staged_count: Mapped[int] = mapped_column(Integer, default=0)
    dedup_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


# ---------------------------------------------------------------------------
# Normalization tables
# ---------------------------------------------------------------------------


class NormalizedJob(Base):
    """Post-normalization canonical job records."""

    __tablename__ = "normalized_jobs"
    __table_args__ = (
        Index("ix_normalized_jobs_run_id", "ingestion_run_id"),
        Index("ix_normalized_jobs_source_eid", "source", "external_id"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingestion_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    region_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Core fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured location (replaces location / normalized_location)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    work_arrangement: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_remote: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # URL
    job_url: Mapped[str | None] = mapped_column(String(2083), nullable=True)

    # Classification
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    occupation_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mapper_used: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Date
    date_posted: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Salary
    salary_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    salary_period: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Quality
    normalization_status: Mapped[str] = mapped_column(String(50), default="success")
    normalization_errors: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))


class NormalizationQuarantine(Base):
    """Records that failed normalization validation."""

    __tablename__ = "normalization_quarantine"
    __table_args__ = (
        Index("ix_norm_quarantine_run_id", "ingestion_run_id"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    raw_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingestion_run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    quarantined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
