"""RegionConfig — typed configuration for a geographic search region.

Used by the Ingestion Agent to parameterise source adapter fetches.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RegionConfig(BaseModel):
    """Configuration for a single geographic search region."""

    region_id: str
    display_name: str
    query_location: str
    radius_miles: int
    states: list[str]
    countries: list[str]
    sources: list[str]
    role_categories: list[str]
    keywords: list[str]
    zip_codes: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("radius_miles")
    @classmethod
    def radius_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("radius_miles must be > 0")
        return v

    @field_validator("sources")
    @classmethod
    def sources_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("sources must contain at least one entry")
        return v
