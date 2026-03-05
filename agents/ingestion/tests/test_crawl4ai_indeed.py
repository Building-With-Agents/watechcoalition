"""Tests for the Crawl4AI Indeed adapter."""

from __future__ import annotations

import asyncio

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.crawl4ai_indeed import (
    Crawl4AIIndeedAdapter,
    _build_indeed_url,
    _extract_jobs_from_html,
)


def _default_region() -> RegionConfig:
    return RegionConfig(
        region_id="wa-default",
        display_name="Washington State",
        query_location="Washington state",
        radius_miles=50,
        states=["WA"],
        countries=["US"],
        sources=["crawl4ai_indeed"],
        keywords=["software engineer"],
        role_categories=[],
    )


class TestBuildIndeedURL:
    def test_builds_url_with_keywords(self) -> None:
        region = _default_region()
        url = _build_indeed_url(region)
        assert "indeed.com/jobs" in url
        assert "software+engineer" in url
        assert "Washington+state" in url

    def test_builds_url_no_keywords(self) -> None:
        region = RegionConfig(
            region_id="test",
            display_name="Test",
            query_location="Seattle, WA",
            radius_miles=50,
            states=["WA"],
            countries=["US"],
            sources=["crawl4ai_indeed"],
            keywords=[],
            role_categories=[],
        )
        url = _build_indeed_url(region)
        assert "software+engineer" in url  # default keyword


class TestExtractJobsFromHTML:
    def test_extracts_from_html_with_job_cards(self) -> None:
        """Parser extracts records from HTML with Indeed-style data attributes."""
        html = """
        <div data-jk="abc123">
            <span id="jobTitle-abc123"><span>Software Engineer</span></span>
            <span data-testid="company-name">Acme Corp</span>
            <div data-testid="text-location">Seattle, WA</div>
        </div>
        <div data-jk="def456">
            <span id="jobTitle-def456"><span>Data Scientist</span></span>
            <span data-testid="company-name">BigCo</span>
            <div data-testid="text-location">Remote</div>
        </div>
        """
        records = _extract_jobs_from_html(html, "wa-default")
        assert len(records) == 2
        assert records[0].external_id == "indeed-abc123"
        assert records[0].source == "crawl4ai_indeed"
        assert records[0].title == "Software Engineer"
        assert records[0].company == "Acme Corp"
        assert records[0].city == "Seattle"
        assert records[0].state == "WA"
        assert records[1].is_remote is True

    def test_empty_html_returns_empty(self) -> None:
        records = _extract_jobs_from_html("", "test")
        assert records == []

    def test_no_job_cards_returns_empty(self) -> None:
        records = _extract_jobs_from_html("<html><body>No jobs here</body></html>", "test")
        assert records == []


class TestCrawl4AIIndeedAdapter:
    def test_source_name(self) -> None:
        adapter = Crawl4AIIndeedAdapter()
        assert adapter.source_name == "crawl4ai_indeed"

    def test_health_check(self) -> None:
        adapter = Crawl4AIIndeedAdapter()
        result = asyncio.run(adapter.health_check())
        assert "reachable" in result
        assert result["source"] == "crawl4ai_indeed"

    def test_fetch_returns_list(self) -> None:
        """Fetch returns a list (may be empty if crawl4ai not installed)."""
        adapter = Crawl4AIIndeedAdapter()
        records = asyncio.run(adapter.fetch(_default_region()))
        assert isinstance(records, list)
