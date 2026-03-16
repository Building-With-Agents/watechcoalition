"""Tests for the Crawl4AI scraper adapter."""

from __future__ import annotations

import asyncio

from agents.ingestion.sources.scraper_adapter import ScraperAdapter


class TestScraperAdapter:
    """Test fixture fallback mode."""

    def test_fixture_fallback_loads_records(self) -> None:
        """When no SCRAPING_TARGETS set, loads from fixture file."""
        adapter = ScraperAdapter()
        adapter._targets = []
        records = asyncio.run(adapter.fetch(limit=5))
        assert len(records) > 0
        assert len(records) <= 5

    def test_fixture_field_mapping(self) -> None:
        """Fixture records are mapped to canonical field names."""
        adapter = ScraperAdapter()
        adapter._targets = []
        records = asyncio.run(adapter.fetch(limit=1))
        assert len(records) == 1
        r = records[0]
        assert "external_id" in r
        assert r["source"] == "crawl4ai"
        assert "title" in r
        assert "company" in r
        assert "raw_text" in r

    def test_health_check_fixture_mode(self) -> None:
        """Health check returns True in fixture fallback mode."""
        adapter = ScraperAdapter()
        adapter._targets = []
        assert asyncio.run(adapter.health_check()) is True
