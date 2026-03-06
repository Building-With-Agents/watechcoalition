"""Canonical JobRecord Pydantic model.

This is the validated output of the Normalization Agent. Records that fail
validation against this schema are quarantined — they never proceed downstream.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, field_validator


class EmploymentType(StrEnum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    temporary = "temporary"
    internship = "internship"
    unknown = "unknown"


class SalaryPeriod(StrEnum):
    annual = "annual"
    hourly = "hourly"
    monthly = "monthly"


class JobRecord(BaseModel):
    """Canonical normalized job record schema."""

    # Identity (carried from Ingestion Agent)
    external_id: str
    source: str
    ingestion_run_id: str
    raw_payload_hash: str

    # Core fields (normalized by Normalization Agent)
    title: str
    company: str
    location: str | None = None
    normalized_location: str | None = None
    employment_type: EmploymentType | None = None
    date_posted: datetime | None = None
    description: str | None = None

    # Salary (parsed by cleaners.parse_salary)
    salary_raw: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: SalaryPeriod | None = None

    @field_validator("salary_max")
    @classmethod
    def salary_max_gte_min(cls, v: float | None, info) -> float | None:
        """Ensure salary_max >= salary_min when both are present."""
        if v is not None and info.data.get("salary_min") is not None and v < info.data["salary_min"]:
            msg = f"salary_max ({v}) < salary_min ({info.data['salary_min']})"
            raise ValueError(msg)
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("company")
    @classmethod
    def company_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("company must not be empty")
        return v.strip()
