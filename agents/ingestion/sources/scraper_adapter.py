"""Crawl4AI scraper adapter with fixture fallback.

When ``SCRAPING_TARGETS`` is empty (or unset), falls back to the fixture
file at ``agents/data/fixtures/fallback_scrape_sample.json``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import structlog

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter

log = structlog.get_logger()

_FALLBACK_SCRAPE = (
    Path(__file__).parent.parent.parent  # agents/
    / "data"
    / "fixtures"
    / "fallback_scrape_sample.json"
)


def _map_fixture_record(raw: dict, region_id: str) -> RawJobRecord:
    """Map a fallback fixture record to a typed RawJobRecord."""
    return RawJobRecord(
        external_id=str(raw.get("posting_id", "")),
        source="crawl4ai",
        region_id=region_id,
        title=raw.get("title", ""),
        company=raw.get("company", ""),
        description=raw.get("raw_text", ""),
        city=raw.get("city"),
        state=raw.get("state"),
        country=raw.get("country"),
        is_remote=raw.get("is_remote"),
        date_posted=raw.get("timestamp"),
        job_url=raw.get("url", ""),
        raw_payload=raw,
    )


class Crawl4AIAdapter(SourceAdapter):
    """Fetches job postings via Crawl4AI or fixture fallback."""

    @property
    def source_name(self) -> str:
        return "crawl4ai"

    def __init__(self) -> None:
        targets = os.getenv("SCRAPING_TARGETS", "")
        self._targets = [t.strip() for t in targets.split(",") if t.strip()]

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch job postings for the given region."""
        if self._targets:
            return await self._fetch_live(region)
        return self._fetch_fixture(region)

    async def _fetch_live(self, region: RegionConfig) -> list[RawJobRecord]:
        """Fetch from real scraping targets using Crawl4AI."""
        records: list[RawJobRecord] = []
        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                for url in self._targets:
                    try:
                        result = await crawler.arun(url=url)
                        if result.success and result.markdown:
                            records.append(
                                RawJobRecord(
                                    external_id=url,
                                    source="crawl4ai",
                                    region_id=region.region_id,
                                    title="",
                                    company="",
                                    description=result.markdown,
                                    job_url=url,
                                    raw_payload={"url": url, "markdown_length": len(result.markdown)},
                                )
                            )
                    except Exception as exc:
                        log.warning("scraper_target_failed", url=url, error=str(exc))

        except ImportError:
            log.warning("crawl4ai_not_installed", note="falling back to fixture")
            return self._fetch_fixture(region)

        log.info("scraper_live_fetch_complete", count=len(records))
        return records

    def _fetch_fixture(self, region: RegionConfig) -> list[RawJobRecord]:
        """Load job postings from the fallback fixture file."""
        if not _FALLBACK_SCRAPE.exists():
            log.warning("scraper_fixture_missing", path=str(_FALLBACK_SCRAPE))
            return []

        raw_list: list[dict] = json.loads(_FALLBACK_SCRAPE.read_text(encoding="utf-8"))
        records = [_map_fixture_record(r, region.region_id) for r in raw_list]
        log.info("scraper_fixture_loaded", count=len(records), path=str(_FALLBACK_SCRAPE))
        return records

    async def health_check(self) -> dict:
        """Return adapter readiness status."""
        if self._targets:
            return {"reachable": True, "source": self.source_name}
        return {"reachable": _FALLBACK_SCRAPE.exists(), "source": self.source_name}


# Backward-compatibility alias
ScraperAdapter = Crawl4AIAdapter
