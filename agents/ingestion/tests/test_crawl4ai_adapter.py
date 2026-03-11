"""Tests for Crawl4AIAdapter — El Paso GovernmentJobs portal (mocked, no live site)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.common.types.raw_job_record import RawJobRecord
from agents.common.types.region_config import RegionConfig
from agents.ingestion.sources.crawl4ai_adapter import (
    Crawl4AIAdapter,
    Crawl4AIAdapterError,
    EL_PASO_PORTAL_BASE,
)


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


def _make_mock_result(*, success: bool, html: str | None = None, error_message: str | None = None):
    """Build a mock CrawlResult for patching."""
    r = MagicMock()
    r.success = success
    r.html = html
    r.cleaned_html = html
    r.error_message = error_message
    return r


@patch("crawl4ai.AsyncWebCrawler")
class TestCrawl4AIAdapterFetch:
    """Tests for fetch() with mocked Crawl4AI."""

    def test_fetch_returns_list_of_raw_job_records_with_source_and_required_fields(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """fetch(region) returns list[RawJobRecord]; each has source crawl4ai; required fields populated."""
        html = "x" * 600 + 'href="/careers/elpaso/jobs/123/test-job"'
        mock_result = _make_mock_result(success=True, html=html)
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        records = asyncio.run(adapter.fetch(region))

        assert isinstance(records, list)
        assert all(isinstance(r, RawJobRecord) for r in records)
        assert all(r.source == "crawl4ai" for r in records)
        if records:
            r = records[0]
            assert r.external_id == "123"
            assert r.title
            assert r.company == "City of El Paso"
            assert r.region_id == region.region_id
            assert r.raw_payload_hash != ""
            assert r.description == ""
            assert r.source_url != ""
            assert r.job_url is not None and r.job_url.startswith("https://")
            assert "governmentjobs.com" in r.job_url and "/careers/elpaso/jobs/123" in r.job_url

    def test_fetch_raises_when_target_unreachable(self, mock_crawler_cls: MagicMock) -> None:
        """Unreachable target raises Crawl4AIAdapterError with clear message."""
        mock_result = _make_mock_result(success=False, error_message="Connection timeout")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        with pytest.raises(Crawl4AIAdapterError) as exc_info:
            asyncio.run(adapter.fetch(region))
        assert "unreachable" in str(exc_info.value).lower()
        assert "timeout" in str(exc_info.value).lower()

    def test_fetch_returns_empty_list_when_page_has_no_openings_signal(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """Zero job links with explicit no-openings signal returns []."""
        html = "x" * 400 + " 0 jobs found " + "y" * 200
        mock_result = _make_mock_result(success=True, html=html)
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        records = asyncio.run(adapter.fetch(region))
        assert records == []

    def test_fetch_raises_parser_breakage_when_large_page_has_no_links_and_no_no_openings_signal(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """Large HTML with no job links and no no-openings signal raises Crawl4AIAdapterError."""
        html = "x" * 600  # Valid length, no job links, no "0 jobs found" etc.
        mock_result = _make_mock_result(success=True, html=html)
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        with pytest.raises(Crawl4AIAdapterError) as exc_info:
            asyncio.run(adapter.fetch(region))
        assert "parser breakage" in str(exc_info.value).lower()

    def test_fetch_raises_when_content_too_small(self, mock_crawler_cls: MagicMock) -> None:
        """Broken page / tiny content raises Crawl4AIAdapterError."""
        mock_result = _make_mock_result(success=True, html="")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        with pytest.raises(Crawl4AIAdapterError) as exc_info:
            asyncio.run(adapter.fetch(region))
        assert "too small" in str(exc_info.value).lower()

    def test_fetch_raises_when_crawl4ai_raises(self, mock_crawler_cls: MagicMock) -> None:
        """Crawl4AI init or arun exception is wrapped in Crawl4AIAdapterError."""
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(side_effect=RuntimeError("Browser crashed"))
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        with pytest.raises(Crawl4AIAdapterError) as exc_info:
            asyncio.run(adapter.fetch(region))
        assert "init/fetch failed" in str(exc_info.value).lower()

    def test_fetch_raises_when_no_html_in_result(self, mock_crawler_cls: MagicMock) -> None:
        """Result with no html/cleaned_html raises Crawl4AIAdapterError."""
        mock_result = _make_mock_result(success=True, html=None)
        mock_result.html = None
        mock_result.cleaned_html = None

        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        with pytest.raises(Crawl4AIAdapterError) as exc_info:
            asyncio.run(adapter.fetch(region))
        msg = str(exc_info.value).lower()
        assert "missing" in msg or "html" in msg


@patch("crawl4ai.AsyncWebCrawler")
class TestCrawl4AIAdapterHealthCheck:
    """Tests for health_check()."""

    def test_health_check_returns_full_structured_dict_including_extractable_structure(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """health_check() returns full structured dict: initialized, target_configured, reachable, extractable_structure, status, source, error."""
        mock_result = _make_mock_result(
            success=True, html='<a href="/careers/elpaso/jobs/123/test">Job</a>'
        )
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        expected_keys = {
            "initialized",
            "target_configured",
            "reachable",
            "extractable_structure",
            "status",
            "source",
            "error",
        }
        assert set(result.keys()) == expected_keys
        assert result["source"] == "crawl4ai"
        assert result["reachable"] is True
        assert result["extractable_structure"] is True
        assert result["status"] == "operational"
        assert result["error"] is None

    def test_health_check_extractable_structure_true_when_job_links_present(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """extractable_structure is True when HTML contains expected job-link pattern."""
        mock_result = _make_mock_result(
            success=True, html='<body> <a href="/careers/elpaso/jobs/99/engineer">Link</a> </body>'
        )
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is True
        assert result["extractable_structure"] is True

    def test_health_check_extractable_structure_true_when_no_openings_signal(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """extractable_structure is True when HTML contains no-openings signal only."""
        mock_result = _make_mock_result(success=True, html="<body> 0 jobs found </body>")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is True
        assert result["extractable_structure"] is True

    def test_health_check_status_reachable_but_unextractable_when_no_structure(
        self, mock_crawler_cls: MagicMock
    ) -> None:
        """When reachable but no job-link/no-openings signal: status is reachable_but_unextractable, error set."""
        mock_result = _make_mock_result(success=True, html="<body><p>Some other content</p></body>")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is True
        assert result["extractable_structure"] is False
        assert result["status"] == "reachable_but_unextractable"
        assert result["error"] is not None

    def test_health_check_when_crawl_fails(self, mock_crawler_cls: MagicMock) -> None:
        """When target is unreachable: reachable and extractable_structure False, status crawl_failed, error set."""
        mock_result = _make_mock_result(success=False, error_message="timeout")
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(return_value=mock_result)
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is False
        assert result["extractable_structure"] is False
        assert result["status"] == "crawl_failed"
        assert result["error"] is not None

    def test_health_check_when_exception_raised(self, mock_crawler_cls: MagicMock) -> None:
        """When crawl raises: status error, reachable and extractable_structure False, error set."""
        mock_crawler = AsyncMock()
        mock_crawler.arun = AsyncMock(side_effect=RuntimeError("Browser failed"))
        mock_crawler.__aenter__ = AsyncMock(return_value=mock_crawler)
        mock_crawler.__aexit__ = AsyncMock(return_value=None)
        mock_crawler_cls.return_value = mock_crawler

        adapter = Crawl4AIAdapter()
        result = asyncio.run(adapter.health_check())
        assert result["reachable"] is False
        assert result["extractable_structure"] is False
        assert result["status"] == "error"
        assert result["error"] is not None


class TestCrawl4AIAdapterUnit:
    """Unit tests for adapter and _to_raw_job_record (no Crawl4AI mocking)."""

    def test_source_name_is_crawl4ai(self) -> None:
        """source_name property returns 'crawl4ai'."""
        adapter = Crawl4AIAdapter()
        assert adapter.source_name == "crawl4ai"

    def test_to_raw_job_record_populates_required_fields(self) -> None:
        """_to_raw_job_record sets required fields from card; optional unavailable fields not passed."""
        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        card = {
            "external_id": "5257914",
            "title": "Construction Inspector",
            "job_url": "https://www.governmentjobs.com/careers/elpaso/jobs/5257914/construction-inspector",
        }
        rec = adapter._to_raw_job_record(card, region, 0)
        assert rec.external_id == "5257914"
        assert rec.source == "crawl4ai"
        assert rec.title == "Construction Inspector"
        assert rec.company == "City of El Paso"
        assert rec.region_id == region.region_id
        assert rec.raw_payload_hash != ""
        assert rec.description == ""
        assert rec.source_url != ""

    def test_to_raw_job_record_unavailable_optional_fields_are_none(self) -> None:
        """Unavailable optional fields (city, state, dates, salary, etc.) are explicitly None."""
        adapter = Crawl4AIAdapter()
        region = _border_region_config()
        card = {"external_id": "1", "title": "Test Job", "job_url": "https://example.com/jobs/1"}
        rec = adapter._to_raw_job_record(card, region, 0)
        assert rec.city is None
        assert rec.state is None
        assert rec.country is None
        assert rec.is_remote is None
        assert rec.date_posted is None
        assert rec.salary_raw is None
        assert rec.salary_min is None
        assert rec.salary_max is None
        assert rec.salary_currency is None
        assert rec.salary_period is None
        assert rec.employment_type is None
        assert rec.experience_level is None


class TestCrawl4AIAdapterExtractionQuality:
    """Extraction behavior: dedup, URL normalization, title fallback (no network)."""

    def test_duplicate_job_links_deduplicated_by_external_id(self) -> None:
        """Duplicate job links in HTML yield a single card per external_id."""
        adapter = Crawl4AIAdapter()
        html = (
            'href="/careers/elpaso/jobs/99/dup-job" '
            'href="/careers/elpaso/jobs/99/dup-job" '
            'href="https://www.governmentjobs.com/careers/elpaso/jobs/99/dup-job"'
        )
        cards = adapter._extract_job_cards(html, EL_PASO_PORTAL_BASE)
        assert len(cards) == 1
        assert cards[0]["external_id"] == "99"
        assert cards[0]["title"] == "Dup Job"

    def test_relative_job_links_normalized_to_absolute_urls(self) -> None:
        """Relative job hrefs are normalized to absolute URLs with correct base."""
        adapter = Crawl4AIAdapter()
        html = 'href="/careers/elpaso/jobs/42/software-engineer"'
        cards = adapter._extract_job_cards(html, EL_PASO_PORTAL_BASE)
        assert len(cards) == 1
        assert cards[0]["job_url"].startswith("https://")
        assert "governmentjobs.com" in cards[0]["job_url"]
        assert cards[0]["job_url"].endswith("/careers/elpaso/jobs/42/software-engineer")

    def test_title_fallback_when_slug_missing(self) -> None:
        """Job link without slug uses title 'Job {id}'."""
        adapter = Crawl4AIAdapter()
        html = 'href="/careers/elpaso/jobs/777"'
        cards = adapter._extract_job_cards(html, EL_PASO_PORTAL_BASE)
        assert len(cards) == 1
        assert cards[0]["title"] == "Job 777"
        assert cards[0]["external_id"] == "777"
