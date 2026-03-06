"""Abstract base class for ingestion source adapters.

Contract type: Architectural (Fixed) — students implement concrete adapters
but do NOT modify this interface.

Each adapter fetches raw job postings from a single external source and
returns them as typed ``RawJobRecord`` Pydantic models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig


class SourceAdapter(ABC):
    """All source adapters (JSearch, Crawl4AI, etc.) implement this interface."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Canonical source identifier (e.g. 'jsearch', 'crawl4ai')."""
        ...

    @abstractmethod
    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch raw job postings from the source for the given region.

        Returns a list of ``RawJobRecord`` Pydantic models.
        """

    @abstractmethod
    async def health_check(self) -> dict:
        """Return a dict describing adapter readiness.

        Expected shape::

            {"reachable": True/False, "source": self.source_name}
        """
