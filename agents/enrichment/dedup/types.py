"""Typed results for fuzzy deduplication (IMP-018 / Week 6)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class FuzzyDedupResult(BaseModel):
    """Outcome of comparing one posting against same-company survivors in a rolling window."""

    model_config = ConfigDict(frozen=True)

    is_duplicate: bool = Field(
        description="True when this posting is merged into an existing cluster (non-survivor).",
    )
    duplicate_cluster_id: str | None = Field(
        default=None,
        description="Cluster id (UUID string) shared by near-duplicate rows; null if not a duplicate.",
    )
    survivor_job_posting_id: str | None = Field(
        default=None,
        description="job_posting_id of the survivor row when is_duplicate is True.",
    )
    stub: bool = Field(
        default=False,
        description="True while implementation is a no-op stub (Phase 0); remove when live.",
    )
