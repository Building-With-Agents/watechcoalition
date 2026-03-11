"""Tests for Crawl4AIAdapter — U.S.–Mexico border region (El Paso, Las Cruces) scope."""

from __future__ import annotations

import asyncio

import pytest

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.crawl4ai_adapter import Crawl4AIAdapter


def _border_region_config() -> RegionConfig:
    """Sample RegionConfig for U.S.–Mexico border: El Paso, TX and Las Cruces, NM."""
    return RegionConfig(
        region_id="border-el-paso-lascruces",
        display_name="El Paso / Las Cruces Border Region",
        query_location="El Paso, TX",
        radius_miles=75,
        states=["TX", "NM"],
        countries=["US"],
        sources=["crawl4ai"],
        role_categories=["Technology", "Government"],
        keywords=["jobs", "employment", "careers"],
        zip_codes=["79901", "88001"],
        is_active=True,
    )


class TestCrawl4AIAdapter:
    """Contract and behavior tests for Crawl4AIAdapter."""

    def test_source_name_is_crawl4ai(self) -> None:
        """Adapter exposes source_name 'crawl4ai'."""
        adapter = Crawl4AIAdapter()
        assert adapter.source_name == "crawl4ai"

    def test_health_check_reports_expected_shape(self) -> None:
        """health_check returns dict with reachable, source, and expected keys."""
        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert "reachable" in result
        assert "source" in result
        assert result["source"] == "crawl4ai"

    def test_fetch_returns_raw_job_records_for_region(self) -> None:
        """fetch(region) returns a non-empty list of RawJobRecord for the border region.

        Fails until Crawl4AI integration and field mapping are implemented.
        """
        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        records = asyncio.run(adapter.fetch(region))
        assert isinstance(records, list)
        assert len(records) > 0, "fetch should return at least one RawJobRecord for the border region"
        from agents.common.types.raw_job_record import RawJobRecord
        for r in records:
            assert isinstance(r, RawJobRecord)
            assert r.source == "crawl4ai"
