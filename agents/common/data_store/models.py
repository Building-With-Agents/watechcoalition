"""SQLAlchemy ORM models for all database tables.

SQLAlchemy is the single database authority. All tables live in the ``dbo``
schema. Reference tables (companies, industry_sectors, etc.) were originally
seeded via pgloader from MSSQL and are now agent-owned with full read+write.
Prisma/MSSQL is being phased out.

Agent-created tables: raw_ingested_jobs, job_ingestion_runs, normalized_jobs,
    normalization_quarantine, extracted_intelligence, llm_audit_log,
    employer_profiles.
Reference tables (seeded, agent-owned): companies, industry_sectors,
    technology_areas, skills, socc, job_postings.
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
from typing import Literal

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Shared declarative base for all agent models."""

    pass


FRESH_THRESHOLD_DAYS = int(os.getenv("FRESH_THRESHOLD_DAYS", "30"))
STALE_THRESHOLD_DAYS = int(os.getenv("STALE_THRESHOLD_DAYS", "90"))


def classify_freshness(days: int) -> Literal["fresh", "stale", "expired"]:
    """Classify posting age in whole days using FRESH_THRESHOLD_DAYS and STALE_THRESHOLD_DAYS."""
    if days <= FRESH_THRESHOLD_DAYS:
        return "fresh"
    if days <= STALE_THRESHOLD_DAYS:
        return "stale"
    return "expired"


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
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
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
    date_ingested: Mapped[datetime] = mapped_column(
        "ingestion_timestamp",
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


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
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
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
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    responsibilities: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Structured location (replaces location / normalized_location)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state_province: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


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
    quarantined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Extraction tables (Week 4)
# ---------------------------------------------------------------------------


class ExtractedIntelligence(Base):
    """Extraction results for the 6-dimension model (skills, tools, tasks,
    responsibilities, context) plus cost and quality metadata.

    Source of truth: ARCHITECTURE_DEEP.md § extracted_intelligence table.
    """

    __tablename__ = "extracted_intelligence"
    __table_args__ = (
        Index("ix_extracted_intelligence_norm_id", "normalized_job_id"),
        Index("ix_extracted_intelligence_failed", "extraction_failed"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalized_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dbo.normalized_jobs.id"),
        nullable=False,
    )
    extraction_version: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    extraction_model: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    extraction_cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # 6-dimension JSONB columns
    skills: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    tools: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    tasks: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    responsibilities: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    context: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    # Quality metadata
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    extraction_failed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Full ExtractionMetadata blob for audit/debugging (from guardrails branch)
    extraction_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ---------------------------------------------------------------------------
# LLM Audit Log
# ---------------------------------------------------------------------------


class LLMAuditLog(Base):
    """Centralized audit log for every LLM call across all agents.

    Columns: id (PK; checklist: log_id), agent_name, prompt_hash, model, provider,
    latency_ms, input_tokens, output_tokens, token_count, cost_usd, success,
    error_reason, created_at.
    """

    __tablename__ = "llm_audit_log"
    __table_args__ = (
        Index("ix_llm_audit_log_agent_name", "agent_name"),
        Index("ix_llm_audit_log_created_at", "created_at"),
        Index("ix_llm_audit_log_success", "success"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Enrichment tables (Week 5)
# ---------------------------------------------------------------------------


class EmployerProfile(Base):
    """Company-level enrichment: size, AI maturity, sector, known-employer flag.

    Source of truth: ARCHITECTURE_DEEP.md § EmployerProfile.
    """

    __tablename__ = "employer_profiles"
    __table_args__ = (
        Index("ix_employer_profiles_company_id", "company_id"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[str] = mapped_column(Text, nullable=False)
    company_size: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_maturity_signal: Mapped[str | None] = mapped_column(Text, nullable=True)
    sector: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_known_employer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class JobPosting(Base):
    """Minimal ORM anchor for ``dbo.job_postings`` PK so :class:`PostingFreshness` FK resolves.

    The live table is pgloader-seeded with many columns; only ``job_posting_id`` is mapped for
    SQLAlchemy metadata and ``create_all`` dependency ordering.
    """

    __tablename__ = "job_postings"
    __table_args__ = {"schema": "dbo"}

    job_posting_id: Mapped[str] = mapped_column(Text, primary_key=True)


# ---------------------------------------------------------------------------
# Analytics (Week 7) — posting freshness
# ---------------------------------------------------------------------------


class PostingFreshness(Base):
    """Per-job-posting freshness snapshot for analytics (dbo.posting_freshness)."""

    __tablename__ = "posting_freshness"
    __table_args__ = (
        Index("ix_posting_freshness_job_posting_id", "job_posting_id"),
        {"schema": "dbo"},
    )

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    job_posting_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("dbo.job_postings.job_posting_id"),
        nullable=False,
    )
    last_seen_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    days_since_posted: Mapped[int] = mapped_column(Integer, nullable=False)
    freshness_status: Mapped[str] = mapped_column(String(16), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


# ===========================================================================
# Reference tables — seeded via pgloader, now agent-owned (full read+write).
#
# These models match the existing pgloader-seeded table structures exactly.
# create_all() with checkfirst=True will skip creation if tables exist.
# ===========================================================================


class Company(Base):
    """Companies table — originally Prisma-managed, now agent-owned.

    Agents can read existing companies and write placeholders during
    enrichment (company resolution).
    """

    __tablename__ = "companies"
    __table_args__ = {"schema": "dbo"}

    company_id: Mapped[str] = mapped_column(Text, primary_key=True)
    industry_sector_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_name: Mapped[str] = mapped_column(Text, nullable=False)
    # HQ / geo (schema consolidation #110; added via run_migrations if missing)
    city: Mapped[str | None] = mapped_column(Text, nullable=True)
    state: Mapped[str | None] = mapped_column(Text, nullable=True)
    normalized_location: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    about_us: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    year_founded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    company_website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_video_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_mission: Mapped[str | None] = mapped_column(Text, nullable=True)
    company_vision: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[str | None] = mapped_column(Text, default="1-10")
    estimated_annual_hires: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    createdby: Mapped[str | None] = mapped_column(Text, nullable=True)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    contact_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    engagementtype: Mapped[str | None] = mapped_column(String(1000), default="Lead")


class IndustrySector(Base):
    """Industry sectors reference table — agent-owned."""

    __tablename__ = "industry_sectors"
    __table_args__ = {"schema": "dbo"}

    industry_sector_id: Mapped[str] = mapped_column(Text, primary_key=True)
    sector_title: Mapped[str] = mapped_column(Text, nullable=False)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TechnologyArea(Base):
    """Technology areas reference table — agent-owned."""

    __tablename__ = "technology_areas"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Skill(Base):
    """Skills reference table — agent-owned.

    Note: The ``embedding`` column (pgvector vector(1536)) is not mapped here
    because SQLAlchemy needs the pgvector extension. Access it via raw SQL if
    needed for similarity search.
    """

    __tablename__ = "skills"
    __table_args__ = {"schema": "dbo"}

    skill_id: Mapped[str] = mapped_column(Text, primary_key=True)
    skill_subcategory_id: Mapped[str] = mapped_column(Text, nullable=False)
    skill_name: Mapped[str] = mapped_column(Text, nullable=False)
    skill_info_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    skill_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SOCC(Base):
    """Standard Occupational Classification Codes — agent-owned.

    Used by enrichment for SOC code classification.
    """

    __tablename__ = "socc"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    code: Mapped[str] = mapped_column(String(1000), nullable=False)
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PostalGeoData(Base):
    """US zip code reference — read-only lookup table.

    Provides city, county, state, lat/lng for zip code resolution.
    Used by normalization to resolve zip_code from city+state when
    the source posting doesn't include a zip. County and other fields
    are always looked up via JOIN, never stored redundantly on job tables.
    """

    __tablename__ = "postal_geo_data"
    __table_args__ = {"schema": "dbo"}

    zip: Mapped[str] = mapped_column(String(5), primary_key=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    county: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
