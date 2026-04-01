"""U.S. Census Bureau API adapter — regional demographics (Phase 1 mock).

Phase 2: use ``httpx`` against ``https://api.census.gov``; API key from
``os.getenv("CENSUS_API_KEY")`` when required — never hardcode credentials.
"""

from __future__ import annotations

import asyncio

import structlog

from agents.enrichment.adapters.base import AbstractCensusAdapter
from agents.enrichment.adapters.models import RegionalProfile

log = structlog.get_logger()

# Borderplex-relevant mock ACS-style snapshots (not official published tables).
_BORDERPLEX_MOCKS: dict[str, RegionalProfile] = {
    "el_paso": RegionalProfile(
        region="el_paso",
        population=678_815,
        median_household_income=55_710,
        industry_mix_top={
            "healthcare_social": 0.14,
            "retail_trade": 0.12,
            "education": 0.11,
            "manufacturing": 0.09,
            "professional_services": 0.08,
        },
        education_bachelors_or_higher_pct=24.8,
        source="mock",
    ),
    "juarez_proxy": RegionalProfile(
        region="juarez_proxy",
        population=1_512_000,
        median_household_income=12_500,
        industry_mix_top={
            "manufacturing": 0.28,
            "retail_trade": 0.18,
            "transportation": 0.12,
        },
        education_bachelors_or_higher_pct=18.2,
        source="mock",
    ),
    "borderplex": RegionalProfile(
        region="borderplex",
        population=2_190_000,
        median_household_income=48_200,
        industry_mix_top={
            "manufacturing": 0.20,
            "trade_transport": 0.16,
            "healthcare_social": 0.13,
            "education": 0.10,
        },
        education_bachelors_or_higher_pct=22.0,
        source="mock",
    ),
}


def _region_key(region: str) -> str:
    r = (region or "").strip().lower().replace(" ", "_").replace("-", "_")
    if not r:
        return ""
    if r in _BORDERPLEX_MOCKS:
        return r
    if "el" in r and "paso" in r:
        return "el_paso"
    if "juarez" in r or "juárez" in region.lower():
        return "juarez_proxy"
    return "borderplex"


class MockCensusAdapter(AbstractCensusAdapter):
    """Phase 1 mock Census/ACS data; implements :class:`AbstractCensusAdapter`."""

    async def get_regional_demographics(self, region: str) -> RegionalProfile | None:
        await asyncio.sleep(0)
        try:
            key = _region_key(region)
            if not key:
                log.warning(
                    "census_adapter_get_regional_demographics_invalid_input",
                    reason="empty_region",
                )
                return None
            profile = _BORDERPLEX_MOCKS.get(key)
            if profile is None:
                profile = _BORDERPLEX_MOCKS["borderplex"].model_copy(update={"region": key})
            else:
                profile = profile.model_copy()
            return profile
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "census_adapter_get_regional_demographics_failed",
                region=region,
                error=str(exc),
            )
            return None


CensusAdapter = MockCensusAdapter
