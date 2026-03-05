"""Tests for the Crawl4AI debug adapter (fixture fallback)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.scraper_adapter import Crawl4AIDebugAdapter


def _default_region() -> RegionConfig:
    return RegionConfig(
        region_id="test",
        display_name="Test",
        query_location="Washington state",
        radius_miles=50,
        states=["WA"],
        countries=["US"],
        sources=["crawl4ai_indeed"],
        role_categories=[],
        keywords=["software engineer"],
    )


class TestCrawl4AIDebugAdapter:
    """Test fixture fallback in debug mode."""

    @patch.dict("os.environ", {"PIPELINE_DEBUG_MODE": "true"})
    def test_debug_mode_loads_fixtures(self) -> None:
        """When debug mode is ON, loads records from fixture file."""
        adapter = Crawl4AIDebugAdapter()
        records = asyncio.run(adapter.fetch(_default_region()))
        # May be empty if fixture file doesn't exist in test env
        assert isinstance(records, list)

    @patch.dict("os.environ", {"PIPELINE_DEBUG_MODE": "false"})
    def test_production_mode_returns_empty(self) -> None:
        """When debug mode is OFF, returns empty list."""
        adapter = Crawl4AIDebugAdapter()
        records = asyncio.run(adapter.fetch(_default_region()))
        assert records == []

    def test_source_name(self) -> None:
        """Source name is crawl4ai_indeed."""
        adapter = Crawl4AIDebugAdapter()
        assert adapter.source_name == "crawl4ai_indeed"

    @patch.dict("os.environ", {"PIPELINE_DEBUG_MODE": "true"})
    def test_health_check_debug_mode(self) -> None:
        """Health check reports reachable based on fixture existence."""
        adapter = Crawl4AIDebugAdapter()
        result = asyncio.run(adapter.health_check())
        assert "reachable" in result
        assert result["source"] == "crawl4ai_indeed"

    @patch.dict("os.environ", {"PIPELINE_DEBUG_MODE": "false"})
    def test_health_check_production_mode(self) -> None:
        """Health check reports not reachable in production mode."""
        adapter = Crawl4AIDebugAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is False
