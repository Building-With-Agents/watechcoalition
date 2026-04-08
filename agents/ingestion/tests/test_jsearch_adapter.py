"""Tests for the JSearch source adapter (all mocked — no real API calls)."""

from __future__ import annotations

import asyncio
import os
from unittest.mock import patch

import pytest

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.jsearch_adapter import (
    JSearchAdapter,
    _job_to_raw_record,
    jsearch_extract_description,
    jsearch_num_pages_from_env,
)

_TEST_REGION = RegionConfig(
    region_id="test-region",
    display_name="Test",
    query_location="Test City",
    radius_miles=50,
    states=["WA"],
    countries=["US"],
    sources=["jsearch"],
    role_categories=["Software Engineering"],
    keywords=["software engineer"],
)


class TestJSearchFieldMapping:
    """Test field mapping from JSearch API response to canonical RawJobRecord."""

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
        result = _job_to_raw_record(raw, "test-region")
        assert result.external_id == "abc123"
        assert result.source == "jsearch"
        assert result.title == "Software Engineer"
        assert result.company == "Acme Corp"
        assert result.city == "Seattle"
        assert result.state == "WA"
        assert result.description == "Build things."
        assert result.job_url == "https://acme.com/apply"

    def test_map_missing_city(self) -> None:
        raw = {"job_id": "x", "job_title": "Dev", "employer_name": "Co", "job_state": "WA"}
        result = _job_to_raw_record(raw, "test-region")
        assert result.city is None
        assert result.state == "WA"

    def test_map_empty_response(self) -> None:
        result = _job_to_raw_record({}, "test-region")
        assert result.source == "jsearch"
        assert result.title == "Untitled"
        assert result.company == "Unknown"


class TestJsearchExtractDescription:
    """Shared extractor for search and detail payloads."""

    def test_extract_from_job_description(self) -> None:
        assert jsearch_extract_description({"job_description": "A"}) == "A"

    def test_extract_from_highlights_dict(self) -> None:
        d = {"Qualifications": ["q1"], "Responsibilities": ["r1"]}
        assert "q1" in jsearch_extract_description({"job_highlights": d})


class TestJSearchNumPages:
    """``JSEARCH_MAX_PAGES`` + ``BATCH_SIZE`` drive pagination volume."""

    def test_default_matches_legacy_cap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("JSEARCH_MAX_PAGES", raising=False)
        monkeypatch.setenv("BATCH_SIZE", "300")
        assert jsearch_num_pages_from_env() == 10

    def test_max_pages_allows_thirty_with_batch(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BATCH_SIZE", "300")
        monkeypatch.setenv("JSEARCH_MAX_PAGES", "30")
        assert jsearch_num_pages_from_env() == 30

    def test_ceiling_fifty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BATCH_SIZE", "1000")
        monkeypatch.setenv("JSEARCH_MAX_PAGES", "200")
        assert jsearch_num_pages_from_env() == 50

    def test_batch_smaller_than_max(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BATCH_SIZE", "50")
        monkeypatch.setenv("JSEARCH_MAX_PAGES", "30")
        assert jsearch_num_pages_from_env() == 5


class TestJSearchAdapter:
    """Test adapter behavior."""

    def test_fetch_logs_search_complete(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Regression: fetch completes and emits jsearch_search_* observability keys."""
        monkeypatch.setenv("JSEARCH_API_KEY", "test-key")
        monkeypatch.setenv("BATCH_SIZE", "10")
        monkeypatch.setenv("JSEARCH_MAX_PAGES", "1")

        captured: dict = {}

        def capture_info(_event: str, **kw: object) -> None:
            captured.update(kw)

        class FakeResponse:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self):
                return {"data": []}

        class FakeClient:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return None

            async def get(self, *a, **k):
                return FakeResponse()

        monkeypatch.setattr("agents.ingestion.sources.jsearch_adapter.log.info", capture_info)
        monkeypatch.setattr("httpx.AsyncClient", FakeClient)

        adapter = JSearchAdapter()
        asyncio.run(adapter.fetch(region=_TEST_REGION))
        assert "jsearch_search_requests_total" in captured
        assert "jsearch_search_pages_fetched" in captured
        assert "search_unique_records_staged" in captured

    def test_no_api_key_raises(self) -> None:
        """Without JSEARCH_API_KEY, fetch raises ValueError."""
        with patch.dict(os.environ, {"JSEARCH_API_KEY": ""}, clear=False):
            adapter = JSearchAdapter()
            with pytest.raises(ValueError):
                asyncio.run(adapter.fetch(region=_TEST_REGION))

    def test_health_check_without_key(self) -> None:
        with patch.dict(os.environ, {"JSEARCH_API_KEY": ""}, clear=False):
            adapter = JSearchAdapter()
            result = asyncio.run(adapter.health_check())
            assert result["reachable"] is False
