"""Tests for normalization field mappers."""

from __future__ import annotations

import pytest

from agents.normalization.field_mappers.jsearch_mapper import JSearchMapper
from agents.normalization.field_mappers.scraper_mapper import ScraperMapper


class TestJSearchMapper:
    def test_maps_core_fields(self) -> None:
        raw = {
            "external_id": "abc",
            "source": "jsearch",
            "title": "Engineer",
            "company": "Acme",
            "location": "Seattle, WA",
            "raw_text": "Job description here.",
            "date_posted": "2026-01-15T00:00:00Z",
            "raw_payload": {"job_employment_type": "FULLTIME", "job_salary": "$120k"},
        }
        mapper = JSearchMapper()
        result = mapper.map(raw)
        assert result["title"] == "Engineer"
        assert result["company"] == "Acme"
        assert result["source"] == "jsearch"
        assert result["salary_raw"] == "$120k"
        assert result["employment_type_raw"] == "FULLTIME"

    def test_missing_payload(self) -> None:
        raw = {"external_id": "x", "title": "Dev", "company": "Co", "source": "jsearch"}
        mapper = JSearchMapper()
        result = mapper.map(raw)
        assert result["salary_raw"] is None


class TestScraperMapper:
    def test_maps_core_fields(self) -> None:
        raw = {
            "external_id": "1",
            "source": "crawl4ai",
            "title": "Data Scientist",
            "company": "BigCo",
            "location": "Redmond, WA",
            "raw_text": "Great job.",
            "timestamp": "2026-02-24T08:15:00Z",
        }
        mapper = ScraperMapper()
        result = mapper.map(raw)
        assert result["title"] == "Data Scientist"
        assert result["source"] == "crawl4ai"
        assert result["date_posted"] == "2026-02-24T08:15:00Z"

    def test_handles_missing_fields(self) -> None:
        mapper = ScraperMapper()
        result = mapper.map({})
        assert result["title"] == ""
        assert result["source"] == "crawl4ai"
