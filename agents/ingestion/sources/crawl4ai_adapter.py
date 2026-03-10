"""Crawl4AI source adapter — scaffold for .gov and border-region job scraping.

Contract: implements SourceAdapter. Output is list[RawJobRecord].
Lead note: Crawl4AI tends to work better on .gov sites; may break on sites like Indeed.
"""

from __future__ import annotations

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter


class Crawl4AIAdapter(SourceAdapter):
    """Concrete adapter for Crawl4AI / browser-use–driven job scraping."""

    def __init__(self, target_urls: list[str] | None = None) -> None:
        # TODO: Crawl4AI/browser-use integration; config for .gov target URLs.
        self._target_urls = target_urls or []

    @property
    def source_name(self) -> str:
        return "crawl4ai"

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        # TODO: .gov target testing (e.g. El Paso, Las Cruces border region).
        # TODO: Field mapping from scraped HTML/JSON into RawJobRecord.
        # TODO: Error handling / parser fragility (Crawl4AI may break on some sites).
        # Stub: return empty list until integration is implemented (test expects non-empty).
        return []

    async def health_check(self) -> dict:
        # TODO: Actually probe Crawl4AI / browser availability.
        return {
            "reachable": False,
            "source": self.source_name,
            "status": "stub",
        }
