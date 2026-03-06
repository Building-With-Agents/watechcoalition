"""RawJobRecord — typed representation of a raw job posting from any source.

Produced by source adapters in the ingestion layer.
Consumed by the deduplicator and stored in raw_ingested_jobs.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RawJobRecord(BaseModel):
    """A single raw job posting as returned by a source adapter."""

    # Identity
    external_id: str
    source: str
    region_id: str = ""
    raw_payload_hash: str = ""

    # Core fields
    title: str
    company: str
    description: str = ""

    # Location (structured)
    city: str | None = None
    state: str | None = None
    country: str | None = None
    is_remote: bool | None = None

    # Dates
    date_posted: datetime | None = None
    date_ingested: datetime = Field(default_factory=datetime.utcnow)

    # Salary
    salary_raw: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    salary_period: str | None = None

    # Classification
    employment_type: str | None = None
    experience_level: str | None = None

    # URLs
    job_url: str | None = None
    source_url: str = ""

    # Raw payload (full API response)
    raw_payload: dict = Field(default_factory=dict)
