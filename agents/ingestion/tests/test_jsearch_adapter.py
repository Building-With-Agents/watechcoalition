"""Tests for the JSearch source adapter (all mocked — no real API calls)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.jsearch_adapter import JSearchAdapter, _map_jsearch_record


def _default_region() -> RegionConfig:
    return RegionConfig(
        region_id="wa-default",
        display_name="Washington State",
        query_location="Washington state",
        radius_miles=50,
        states=["WA"],
        countries=["US"],
        sources=["jsearch"],
        role_categories=[],
        keywords=["software engineer"],
    )


class TestJSearchFieldMapping:
    """Test field mapping from JSearch API response to canonical record."""

    def test_map_complete_record(self) -> None:
        raw = {
            "job_id": "abc123",
            "job_title": "Software Engineer",
            "employer_name": "Acme Corp",
            "job_city": "Seattle",
            "job_state": "WA",
            "job_description": "Build things.",
            "job_apply_link": "https://acme.com/apply",
            "job_posted_at_datetime_utc": "2026-01-15T00:00:00Z",
        }
        result = _map_jsearch_record(raw, "wa-default")
        assert result.external_id == "abc123"
        assert result.source == "jsearch"
        assert result.title == "Software Engineer"
        assert result.company == "Acme Corp"
        assert result.city == "Seattle"
        assert result.state == "WA"
        assert result.description == "Build things."
        assert result.job_url == "https://acme.com/apply"
        assert result.date_posted is not None

    def test_map_missing_city(self) -> None:
        raw = {"job_id": "x", "job_title": "Dev", "employer_name": "Co", "job_state": "WA"}
        result = _map_jsearch_record(raw, "test")
        assert result.city is None
        assert result.state == "WA"

    def test_map_empty_response(self) -> None:
        result = _map_jsearch_record({}, "test")
        assert result.external_id == ""
        assert result.source == "jsearch"


class TestJSearchAdapter:
    """Test adapter behavior."""

    def test_no_api_key_returns_empty(self) -> None:
        """Without JSEARCH_API_KEY, fetch returns empty list."""
        with patch.dict("os.environ", {}, clear=False):
            adapter = JSearchAdapter()
            adapter._api_key = ""
            result = asyncio.run(adapter.fetch(_default_region()))
            assert result == []

    def test_health_check_with_key(self) -> None:
        adapter = JSearchAdapter()
        adapter._api_key = "test-key"
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is True
        assert result["source"] == "jsearch"

    def test_health_check_without_key(self) -> None:
        adapter = JSearchAdapter()
        adapter._api_key = ""
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is False

    def test_source_name(self) -> None:
        adapter = JSearchAdapter()
        assert adapter.source_name == "jsearch"
