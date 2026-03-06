"""JobRecord — typed representation of a normalized job posting.

Produced by normalization mappers.
Stored in normalized_jobs table.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class JobRecord(BaseModel):
    """A single normalized job record ready for storage."""

    # References
    raw_job_id: int = 0
    ingestion_run_id: str = ""
    region_id: str = ""

    # Identity
    source: str
    external_id: str

    # Core fields
    title: str
    company: str
    description: str | None = None
    job_url: str | None = None

    # Location (structured)
    city: str | None = None
    state_province: str | None = None
    country: str | None = None
    work_arrangement: str | None = None
    is_remote: bool | None = None

    # Dates
    date_posted: datetime | None = None

    # Salary
    salary_raw: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None

    # Classification
    employment_type: str | None = None
    experience_level: str | None = None
    occupation_code: str | None = None

    # Mapper provenance
    mapper_used: str = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("company")
    @classmethod
    def company_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("company must not be empty")
        return v.strip()

    @field_validator("salary_max")
    @classmethod
    def salary_max_gte_min(cls, v: float | None, info) -> float | None:
        if v is not None and info.data.get("salary_min") is not None and v < info.data["salary_min"]:
            raise ValueError("salary_max must be >= salary_min")
        return v
