"""Abstract adapter interfaces — Phase 2 swaps in live HTTP clients without changing callers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.enrichment.adapters.models import OccupationProfile, RegionalProfile, SOCMatch, WageEstimate


class AbstractBLSAdapter(ABC):
    """Bureau of Labor Statistics wage / employment data."""

    @abstractmethod
    async def get_wage_data(self, soc_code: str, region: str) -> WageEstimate | None:
        """Return wage statistics or ``None`` if SOC/region unsupported or on failure. Never raises."""


class AbstractONETAdapter(ABC):
    """O*NET occupation details and SOC crosswalk."""

    @abstractmethod
    async def get_occupation_details(self, soc_code: str) -> OccupationProfile | None:
        """Return occupation profile or ``None``. Never raises."""

    @abstractmethod
    async def get_soc_crosswalk(self, title: str) -> list[SOCMatch]:
        """Return ranked SOC matches for a free-text job title; empty list on failure. Never raises."""


class AbstractCensusAdapter(ABC):
    """Census / ACS regional demographics."""

    @abstractmethod
    async def get_regional_demographics(self, region: str) -> RegionalProfile | None:
        """Return regional profile or ``None``. Never raises."""
