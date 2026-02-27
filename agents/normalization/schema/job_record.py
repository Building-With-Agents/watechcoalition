# agents/normalization/schema/job_record.py
"""Canonical JobRecord and SkillRecord. Phase 1 only — no Phase 2 fields."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SkillRecord(BaseModel):
    skill_id: Optional[str] = None
    label: str
    type: str  # Technical | Domain | Soft | Certification | Tool
    confidence: float
    field_source: str  # title | description | requirements | responsibilities
    required_flag: Optional[bool] = None


class JobRecord(BaseModel):
    """Phase 1 schema. Do not add Phase 2 columns (enrichment_quality_score, soc_code, etc.)."""

    external_id: str
    source: str
    ingestion_run_id: str
    raw_payload_hash: str

    title: str
    company: str
    location: Optional[str] = None
    salary_raw: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[str] = None
    employment_type: Optional[str] = None
    date_posted: Optional[datetime] = None
    description: Optional[str] = None

    skills: list[SkillRecord] = []
    extraction_status: Optional[str] = None

    seniority: Optional[str] = None
    role_classification: Optional[str] = None
    sector_id: Optional[int] = None
    quality_score: Optional[float] = None
    is_spam: Optional[bool] = None
    spam_score: Optional[float] = None
    ai_relevance_score: Optional[float] = None
    company_id: Optional[int] = None
    location_id: Optional[int] = None
    overall_confidence: Optional[float] = None
    field_confidence: Optional[dict] = None
