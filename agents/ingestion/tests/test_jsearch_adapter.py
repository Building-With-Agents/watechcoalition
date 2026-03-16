"""Tests for the JSearch source adapter (all mocked — no real API calls)."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

from agents.ingestion.sources.jsearch_adapter import JSearchAdapter, _map_jsearch_record


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
        result = _map_jsearch_record(raw)
        assert result["external_id"] == "abc123"
        assert result["source"] == "jsearch"
        assert result["title"] == "Software Engineer"
        assert result["company"] == "Acme Corp"
        assert result["location"] == "Seattle, WA"
        assert result["raw_text"] == "Build things."
        assert result["url"] == "https://acme.com/apply"
        assert result["date_posted"] == "2026-01-15T00:00:00Z"

    def test_map_missing_city(self) -> None:
        raw = {"job_id": "x", "job_title": "Dev", "employer_name": "Co", "job_state": "WA"}
        result = _map_jsearch_record(raw)
        assert result["location"] == "WA"

    def test_map_empty_response(self) -> None:
        result = _map_jsearch_record({})
        assert result["external_id"] == ""
        assert result["source"] == "jsearch"


class TestJSearchAdapter:
    """Test adapter behavior."""

    def test_no_api_key_returns_empty(self) -> None:
        """Without JSEARCH_API_KEY, fetch returns empty list."""
        with patch.dict("os.environ", {}, clear=False):
            adapter = JSearchAdapter()
            adapter._api_key = ""
            result = asyncio.run(adapter.fetch(limit=5))
            assert result == []

    def test_health_check_with_key(self) -> None:
        adapter = JSearchAdapter()
        adapter._api_key = "test-key"
        assert asyncio.run(adapter.health_check()) is True

    def test_health_check_without_key(self) -> None:
        adapter = JSearchAdapter()
        adapter._api_key = ""
        assert asyncio.run(adapter.health_check()) is False
