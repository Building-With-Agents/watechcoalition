"""Pydantic schemas for enrichment output (Week 6 external data integration).

``EnrichedJobProfile`` aggregates job context with optional BLS / O*NET / Census payloads.
``job_record`` is typed as ``dict`` to avoid circular imports with ``JobRecord``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EnrichedJobProfile(BaseModel):
    """Enriched view of a job with optional external reference data."""

    job_record: dict[str, Any] = Field(
        ...,
        description="Canonical job row as dict (JobRecord serialized for now).",
    )
    temporal_period: str | None = None
    borderplex_subregion: str | None = None
    employer_profile: dict[str, Any] | None = None
    soc_code: str | None = None
    naics_code: str | None = None
    is_duplicate: bool = False
    duplicate_cluster_id: str | None = None
    bls_data: dict[str, Any] | None = None
    onet_data: dict[str, Any] | None = None
    census_data: dict[str, Any] | None = None
