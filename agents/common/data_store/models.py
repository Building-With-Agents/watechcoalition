"""SQLAlchemy ORM models for all database tables.

SQLAlchemy is the single database authority. All tables live in the ``dbo``
schema. Reference tables (companies, industry_sectors, etc.) were originally
seeded via pgloader from MSSQL and are now agent-owned with full read+write.
Prisma/MSSQL is being phased out.

Agent-created tables: raw_ingested_jobs, job_ingestion_runs, normalized_jobs,
    normalization_quarantine, extracted_intelligence, llm_audit_log,
    employer_profiles, analytics_pipeline_state, sector_summary_weekly, geo_demand_weekly,
    skill_demand_weekly, tool_demand_weekly, skill_velocity, skill_co_occurrence.
Reference tables (seeded, agent-owned): companies, industry_sectors,
    technology_areas, skills, socc, naics, job_postings.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
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
    naics_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    employer_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
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

    One row per ``companies.company_id``; job postings reference via ``employer_profile_id``.
    """

    __tablename__ = "employer_profiles"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_employer_profiles_company_id"),
        Index("ix_employer_profiles_company_id", "company_id"),
        {"schema": "dbo"},
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("dbo.companies.company_id", ondelete="CASCADE"),
        nullable=False,
    )
    company_size: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    ai_maturity_signal: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_known_employer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Analytics aggregate tables (Week 7 — Pair A)
# Frozen column contract: .cursor/rules/skill-tool-demand.mdc (IMP-021).
# ---------------------------------------------------------------------------


class SkillDemandWeekly(Base):
    """Weekly skill demand counts (Analytics step 2).

    ``employer_count`` stores distinct employers for the skill in the week
    (``func.count(func.distinct(company_id))`` pattern in SQL — IMP-021).
    """

    __tablename__ = "skill_demand_weekly"
    __table_args__ = (
        UniqueConstraint("skill_label", "week_start", name="uq_skill_demand_week"),
        Index("ix_skill_demand_weekly_week", "week_start"),
        Index("ix_skill_demand_weekly_skill", "skill_label"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_label: Mapped[str] = mapped_column(Text, nullable=False)
    esco_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    posting_count: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ToolDemandWeekly(Base):
    """Weekly tool demand counts (Analytics step 3)."""

    __tablename__ = "tool_demand_weekly"
    __table_args__ = (
        UniqueConstraint("tool_label", "week_start", name="uq_tool_demand_week"),
        Index("ix_tool_demand_weekly_week", "week_start"),
        Index("ix_tool_demand_weekly_tool", "tool_label"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_label: Mapped[str] = mapped_column(Text, nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    posting_count: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SkillVelocity(Base):
    """Skill demand velocity / trend (Analytics step 8).

    Python attribute ``velocity_week`` maps to DB column ``week`` (reserved name).
    """

    __tablename__ = "skill_velocity"
    __table_args__ = (
        UniqueConstraint("skill_label", "week", name="uq_skill_velocity_week"),
        Index("ix_skill_velocity_week", "week"),
        Index("ix_skill_velocity_skill", "skill_label"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_label: Mapped[str] = mapped_column(Text, nullable=False)
    esco_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    velocity_week: Mapped[date] = mapped_column("week", Date, nullable=False)
    demand_count: Mapped[int] = mapped_column(Integer, nullable=False)
    week_over_week_change: Mapped[float] = mapped_column(Float, nullable=False)
    four_week_trend: Mapped[str] = mapped_column(Text, nullable=False)
    trend_confidence: Mapped[float] = mapped_column(Float, nullable=False)


class SkillCoOccurrence(Base):
    """Skill pair co-occurrence within a week (Analytics step 9)."""

    __tablename__ = "skill_co_occurrence"
    __table_args__ = (
        UniqueConstraint("skill_a", "skill_b", "week_start", name="uq_skill_co_occurrence_week"),
        Index("ix_skill_co_occurrence_week", "week_start"),
        Index("ix_skill_co_occurrence_skills", "skill_a", "skill_b"),
        {"schema": "dbo"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_a: Mapped[str] = mapped_column(Text, nullable=False)
    skill_b: Mapped[str] = mapped_column(Text, nullable=False)
    co_occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


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


class NAICS(Base):
    """NAICS 2022 US taxonomy — agent-owned.

    Primary key is the official NAICS code (2–6 digit hierarchical code).
    Seeded from ``data/naics-2022-taxonomy-reference.xlsx``.
    """

    __tablename__ = "naics"
    __table_args__ = {"schema": "dbo"}

    naics_code: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    seq_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    createdat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updatedat: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Analytics pipeline state (Week 7 — minimum-data guard watermark)
# ---------------------------------------------------------------------------


class AnalyticsPipelineState(Base):
    """Singleton row ``id = 1``: last time analytics completed and emitted ``AnalyticsRefreshed``.

    The analytics agent reads ``last_successful_run_at`` to count new ``job_postings``
    rows since the previous successful run. Updated only after the guard passes and
    the pipeline finishes (same session as downstream aggregate writes in Week 7).
    """

    __tablename__ = "analytics_pipeline_state"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_successful_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Analytics aggregates (Week 7 — Pair B)
# ---------------------------------------------------------------------------


class SectorSummaryWeekly(Base):
    """Weekly aggregates by industry sector (Pair B — Analytics Step 6).

    ``avg_salary`` stores the salary **median (p50)** (same basis as
    :func:`agents.analytics.aggregators.salary_percentiles.compute_salary_percentiles`).
    ``top_skills`` is the top 10 most frequent extracted ``skill_name`` values for the sector-week.
    """

    __tablename__ = "sector_summary_weekly"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    sector: Mapped[str] = mapped_column(Text, nullable=False)
    posting_count: Mapped[int] = mapped_column(Integer, nullable=False)
    employer_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class GeoDemandWeekly(Base):
    """Weekly job counts by enrichment ``borderplex_subregion``."""

    __tablename__ = "geo_demand_weekly"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    borderplex_subregion: Mapped[str] = mapped_column(String(32), nullable=False)
    posting_count: Mapped[int] = mapped_column(Integer, nullable=False)
