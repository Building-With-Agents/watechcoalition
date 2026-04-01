"""Pydantic schemas for enrichment output (Week 6 external data integration).

``EnrichedJobProfile`` aggregates job context with optional BLS / O*NET / Census payloads.
``job_record`` is a ``dict`` for pipeline compatibility (same shape as a serialized
:class:`~agents.common.types.job_record.JobRecord` plus extraction fields where present).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from agents.enrichment.adapters.models import OccupationProfile, RegionalProfile, WageEstimate


class EnrichedJobProfile(BaseModel):
    """Enriched view of a job with optional external reference data."""

    job_record: dict[str, Any] = Field(
        ...,
        description="Canonical job row as dict (JobRecord-compatible plus enrichment fields).",
    )
    temporal_period: str | None = None
    borderplex_subregion: str | None = None
    employer_profile: dict[str, Any] | None = None
    soc_code: str | None = None
    naics_code: str | None = None
    is_duplicate: bool = False
    duplicate_cluster_id: str | None = None
    wage_estimate: WageEstimate | None = None
    occupation_profile: OccupationProfile | None = None
    regional_profile: RegionalProfile | None = None
