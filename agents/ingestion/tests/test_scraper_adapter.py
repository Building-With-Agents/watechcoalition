"""Tests for the Crawl4AI scraper adapter."""

from __future__ import annotations

import asyncio

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.scraper_adapter import ScraperAdapter

_TEST_REGION = RegionConfig(
    region_id="test-region",
    display_name="Test",
    query_location="Test City",
    radius_miles=50,
    states=["TX"],
    countries=["US"],
    sources=["crawl4ai"],
    role_categories=["Software Engineering"],
    keywords=["software engineer"],
)


class TestScraperAdapter:
    """Test fixture fallback mode."""

    def test_fixture_fallback_loads_records(self) -> None:
        """When no SCRAPING_TARGETS set, loads from fixture file."""
        adapter = ScraperAdapter()
        adapter._targets = []
        records = asyncio.run(adapter.fetch(region=_TEST_REGION))
        assert len(records) > 0

    def test_fixture_field_mapping(self) -> None:
        """Fixture records are mapped to RawJobRecord with canonical fields."""
        adapter = ScraperAdapter()
        adapter._targets = []
        records = asyncio.run(adapter.fetch(region=_TEST_REGION))
        assert len(records) >= 1
        r = records[0]
        assert r.external_id
        assert r.source == "crawl4ai"
        assert r.title
        assert r.company

    def test_health_check_fixture_mode(self) -> None:
        """Health check returns reachable: True in fixture fallback mode."""
        adapter = ScraperAdapter()
        adapter._targets = []
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is True
