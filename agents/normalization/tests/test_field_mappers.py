"""Tests for normalization field mappers."""

from __future__ import annotations

from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.field_mappers.jsearch_mapper import JSearchMapper
from agents.normalization.field_mappers.scraper_mapper import ScraperMapper


class TestJSearchMapper:
    def test_maps_core_fields(self) -> None:
        raw = RawJobRecord(
            external_id="abc",
            source="jsearch",
            title="Engineer",
            company="Acme",
            description="Job description here.",
            date_posted="2026-01-15T00:00:00Z",
            salary_raw="$120k",
            employment_type="FULLTIME",
        )
        mapper = JSearchMapper()
        result = mapper.map(raw)
        assert result.title == "Engineer"
        assert result.company == "Acme"
        assert result.source == "jsearch"
        assert result.salary_raw == "$120k"
        assert result.employment_type is not None

    def test_missing_payload(self) -> None:
        raw = RawJobRecord(
            external_id="x",
            title="Dev",
            company="Co",
            source="jsearch",
        )
        mapper = JSearchMapper()
        result = mapper.map(raw)
        assert result.salary_min is None
        assert result.salary_raw is None


class TestScraperMapper:
    def test_maps_core_fields(self) -> None:
        raw = RawJobRecord(
            external_id="1",
            source="crawl4ai",
            title="Data Scientist",
            company="BigCo",
            description="Great job.",
            date_posted="2026-02-24T08:15:00Z",
        )
        mapper = ScraperMapper()
        result = mapper.map(raw)
        assert result.title == "Data Scientist"
        assert result.source == "crawl4ai"

    def test_handles_missing_fields(self) -> None:
        raw = RawJobRecord(
            external_id="empty",
            source="crawl4ai",
            title="Untitled",
            company="Unknown",
        )
        mapper = ScraperMapper()
        result = mapper.map(raw)
        assert result.title == "Untitled"
        assert result.source == "crawl4ai"
