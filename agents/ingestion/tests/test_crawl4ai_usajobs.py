"""Tests for the Crawl4AI USAJobs adapter."""

from __future__ import annotations

import asyncio

from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.crawl4ai_usajobs import (
    Crawl4AIUSAJobsAdapter,
    _build_usajobs_url,
    _extract_jobs_from_html,
)


def _default_region() -> RegionConfig:
    return RegionConfig(
        region_id="wa-default",
        display_name="Washington State",
        query_location="Washington",
        radius_miles=50,
        states=["WA"],
        countries=["US"],
        sources=["crawl4ai_usajobs"],
        keywords=["software engineer"],
        role_categories=[],
    )


class TestBuildUSAJobsURL:
    def test_builds_url_with_keywords(self) -> None:
        region = _default_region()
        url = _build_usajobs_url(region)
        assert "usajobs.gov/Search/Results" in url
        assert "software+engineer" in url
        assert "Washington" in url


class TestExtractJobsFromHTML:
    def test_extracts_from_html_with_job_cards(self) -> None:
        """Parser extracts records from HTML with USAJobs-style data attributes."""
        html = """
        <div data-control-number="123456">
            <h3 class="usajobs-search-result--item__title">
                <a href="/job/123456">IT Specialist</a>
            </h3>
            <span class="usajobs-search-result--item__department">
                Department of Defense
            </span>
            <span class="usajobs-search-result--item__location">
                Seattle, Washington
            </span>
            <span class="usajobs-search-result--item__salary">
                $90,000 - $120,000
            </span>
        </div>
        <div data-control-number="789012">
            <h3 class="usajobs-search-result--item__title">
                <a href="/job/789012">Cybersecurity Analyst</a>
            </h3>
            <span class="usajobs-search-result--item__department">
                Department of Homeland Security
            </span>
            <span class="usajobs-search-result--item__location">
                Anywhere in the U.S. (remote job)
            </span>
        </div>
        """
        records = _extract_jobs_from_html(html, "wa-default")
        assert len(records) == 2
        assert records[0].external_id == "usajobs-123456"
        assert records[0].source == "crawl4ai_usajobs"
        assert records[0].title == "IT Specialist"
        assert records[0].company == "Department of Defense"
        assert records[0].city == "Seattle"
        assert records[0].state == "Washington"
        assert records[0].salary_raw == "$90,000 - $120,000"
        assert records[1].is_remote is True

    def test_empty_html_returns_empty(self) -> None:
        records = _extract_jobs_from_html("", "test")
        assert records == []


class TestCrawl4AIUSAJobsAdapter:
    def test_source_name(self) -> None:
        adapter = Crawl4AIUSAJobsAdapter()
        assert adapter.source_name == "crawl4ai_usajobs"

    def test_health_check(self) -> None:
        adapter = Crawl4AIUSAJobsAdapter()
        result = asyncio.run(adapter.health_check())
        assert "reachable" in result
        assert result["source"] == "crawl4ai_usajobs"

    def test_fetch_returns_list(self) -> None:
        """Fetch returns a list (may be empty if crawl4ai not installed)."""
        adapter = Crawl4AIUSAJobsAdapter()
        records = asyncio.run(adapter.fetch(_default_region()))
        assert isinstance(records, list)
