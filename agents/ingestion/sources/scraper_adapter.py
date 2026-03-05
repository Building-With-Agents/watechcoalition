"""Crawl4AI scraper adapter — debug-mode fixture fallback.

In production (default), this module provides only backward-compatibility
aliases.  The real adapters are ``Crawl4AIIndeedAdapter`` and
``Crawl4AIUSAJobsAdapter``.

When ``PIPELINE_DEBUG_MODE=true`` is set, the ``Crawl4AIDebugAdapter``
loads fixture data from ``agents/data/fixtures/fallback_scrape_sample.json``
for local pipeline debugging without live scraping or a running database.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import structlog

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.base_adapter import SourceAdapter
from agents.ingestion.sources.crawl4ai_indeed import Crawl4AIIndeedAdapter

log = structlog.get_logger()

_FALLBACK_SCRAPE = (
    Path(__file__).parent.parent.parent  # agents/
    / "data"
    / "fixtures"
    / "fallback_scrape_sample.json"
)


def _is_debug_mode() -> bool:
    """Check if pipeline debug mode is enabled via env var."""
    return os.getenv("PIPELINE_DEBUG_MODE", "false").lower() in ("true", "1", "yes")


def _map_fixture_record(raw: dict, region_id: str) -> RawJobRecord:
    """Map a fallback fixture record to a typed RawJobRecord."""
    return RawJobRecord(
        external_id=str(raw.get("posting_id", "")),
        source="crawl4ai_indeed",
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


class Crawl4AIDebugAdapter(SourceAdapter):
    """Debug-only adapter that loads fixture data.

    Only active when ``PIPELINE_DEBUG_MODE=true``.
    In production, use ``Crawl4AIIndeedAdapter`` or ``Crawl4AIUSAJobsAdapter``.
    """

    @property
    def source_name(self) -> str:
        return "crawl4ai_indeed"

    async def fetch(self, region: RegionConfig) -> list[RawJobRecord]:
        """Load job postings from the fallback fixture file."""
        if not _is_debug_mode():
            log.warning(
                "debug_adapter_called_without_debug_mode",
                note="PIPELINE_DEBUG_MODE is not set — returning empty",
            )
            return []

        if not _FALLBACK_SCRAPE.exists():
            log.warning("scraper_fixture_missing", path=str(_FALLBACK_SCRAPE))
            return []

        raw_list: list[dict] = json.loads(_FALLBACK_SCRAPE.read_text(encoding="utf-8"))
        records = [_map_fixture_record(r, region.region_id) for r in raw_list]
        log.info(
            "debug_fixture_loaded",
            count=len(records),
            path=str(_FALLBACK_SCRAPE),
        )
        return records

    async def health_check(self) -> dict:
        """Return adapter readiness status."""
        if not _is_debug_mode():
            return {"reachable": False, "source": self.source_name}
        return {"reachable": _FALLBACK_SCRAPE.exists(), "source": self.source_name}

