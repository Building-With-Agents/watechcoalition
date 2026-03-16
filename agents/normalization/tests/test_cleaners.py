"""Tests for normalization cleaners / utility functions."""

from __future__ import annotations

from agents.normalization.cleaners import (
    clean_text,
    clean_whitespace,
    normalize_date,
    normalize_employment_type,
    normalize_location,
    parse_salary,
    strip_html,
)


class TestStripHtml:
    def test_removes_tags(self) -> None:
        assert strip_html("<p>Hello <b>world</b></p>") == "Hello world"

    def test_empty_string(self) -> None:
        assert strip_html("") == ""

    def test_no_tags(self) -> None:
        assert strip_html("plain text") == "plain text"


class TestCleanWhitespace:
    def test_collapses_runs(self) -> None:
        assert clean_whitespace("hello   world") == "hello world"

    def test_strips_edges(self) -> None:
        assert clean_whitespace("  hello  ") == "hello"

    def test_newlines(self) -> None:
        assert clean_whitespace("hello\n\nworld") == "hello world"


class TestCleanText:
    def test_html_and_whitespace(self) -> None:
        assert clean_text("<p>  Hello   <b>world</b>  </p>") == "Hello world"


class TestParseSalary:
    def test_range_with_dollar(self) -> None:
        result = parse_salary("$120,000 - $160,000/year")
        assert result["salary_min"] == 120000.0
        assert result["salary_max"] == 160000.0
        assert result["salary_currency"] == "USD"
        assert result["salary_period"] == "annual"

    def test_single_value(self) -> None:
        result = parse_salary("$50/hr")
        assert result["salary_min"] == 50.0
        assert result["salary_currency"] == "USD"
        assert result["salary_period"] == "hourly"

    def test_none_input(self) -> None:
        result = parse_salary(None)
        assert result["salary_min"] is None
        assert result["salary_max"] is None

    def test_empty_string(self) -> None:
        result = parse_salary("")
        assert result["salary_min"] is None

    def test_competitive(self) -> None:
        """Non-parseable salary strings return all None."""
        result = parse_salary("Competitive")
        assert result["salary_min"] is None
        assert result["salary_max"] is None


class TestNormalizeDate:
    def test_iso_utc(self) -> None:
        dt = normalize_date("2026-02-24T08:15:00Z")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 24

    def test_date_only(self) -> None:
        dt = normalize_date("2026-01-15")
        assert dt is not None
        assert dt.tzinfo is not None

    def test_none_input(self) -> None:
        assert normalize_date(None) is None

    def test_empty_string(self) -> None:
        assert normalize_date("") is None

    def test_unparseable(self) -> None:
        assert normalize_date("not a date") is None


class TestNormalizeEmploymentType:
    def test_full_time(self) -> None:
        assert normalize_employment_type("Full-Time") == "full_time"
        assert normalize_employment_type("full_time") == "full_time"
        assert normalize_employment_type("FULLTIME") == "full_time"

    def test_part_time(self) -> None:
        assert normalize_employment_type("Part-Time") == "part_time"

    def test_contract(self) -> None:
        assert normalize_employment_type("Contract") == "contract"
        assert normalize_employment_type("Freelance") == "contract"

    def test_unknown(self) -> None:
        assert normalize_employment_type("") == "unknown"
        assert normalize_employment_type(None) == "unknown"
        assert normalize_employment_type("something weird") == "unknown"

    def test_prisma_default(self) -> None:
        """Handle Prisma's default format N'full-time'."""
        assert normalize_employment_type("N'full-time'") == "full_time"


class TestNormalizeLocation:
    def test_basic_cleanup(self) -> None:
        assert normalize_location("  Seattle,  WA  ") == "Seattle, WA"

    def test_empty(self) -> None:
        assert normalize_location("") == ""
        assert normalize_location(None) == ""
