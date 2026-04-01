"""Pydantic return types for external data adapters (BLS, O*NET, Census)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WageEstimate(BaseModel):
    """OEWS-style wage statistics (Phase 1 mock; Phase 2 from BLS API)."""

    soc_code: str
    region: str
    median_wage: float
    percentile_25: float
    percentile_75: float
    source: str = Field(description='e.g. "mock" in Phase 1, "bls_api" in Phase 2')


class SOCMatch(BaseModel):
    """Single SOC title/code match from a crosswalk query."""

    soc_code: str
    title: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class OccupationProfile(BaseModel):
    """O*NET-style occupation summary (Phase 1 mock; Phase 2 from O*NET Web Services)."""

    soc_code: str
    title: str
    description: str
    tasks: list[str]
    skills: list[str]
    education: str
    source: str = Field(default="mock", description='e.g. "mock" or "onet_api"')


class RegionalProfile(BaseModel):
    """ACS-style regional demographics (Phase 1 mock; Phase 2 from Census API)."""

    region: str
    population: int
    median_household_income: int
    industry_mix_top: dict[str, float] = Field(
        default_factory=dict,
        description="Share or index by broad industry bucket (mock keys).",
    )
    education_bachelors_or_higher_pct: float = Field(
        ge=0.0,
        le=100.0,
        description="Percent of adults 25+ with bachelor's or higher (mock).",
    )
    source: str = Field(default="mock", description='e.g. "mock" or "census_api"')
