"""Tests for the Pydantic JobRecord schema validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agents.normalization.schema.job_record import JobRecord


class TestJobRecord:
    def _base_record(self, **overrides) -> dict:
        defaults = {
            "external_id": "1",
            "source": "jsearch",
            "ingestion_run_id": "run-001",
            "raw_payload_hash": "abc123",
            "title": "Software Engineer",
            "company": "Acme Corp",
        }
        defaults.update(overrides)
        return defaults

    def test_valid_minimal_record(self) -> None:
        record = JobRecord(**self._base_record())
        assert record.title == "Software Engineer"

    def test_valid_full_record(self) -> None:
        record = JobRecord(**self._base_record(
            location="Seattle, WA",
            normalized_location="Seattle, WA",
            employment_type="full_time",
            date_posted=datetime(2026, 1, 15, tzinfo=timezone.utc),
            salary_raw="$120k-$160k/year",
            salary_min=120000.0,
            salary_max=160000.0,
            salary_currency="USD",
            salary_period="annual",
        ))
        assert record.salary_min == 120000.0

    def test_empty_title_fails(self) -> None:
        with pytest.raises(ValidationError, match="title must not be empty"):
            JobRecord(**self._base_record(title=""))

    def test_whitespace_title_fails(self) -> None:
        with pytest.raises(ValidationError, match="title must not be empty"):
            JobRecord(**self._base_record(title="   "))

    def test_empty_company_fails(self) -> None:
        with pytest.raises(ValidationError, match="company must not be empty"):
            JobRecord(**self._base_record(company=""))

    def test_salary_max_less_than_min_fails(self) -> None:
        with pytest.raises(ValidationError, match="salary_max.*salary_min"):
            JobRecord(**self._base_record(salary_min=100000, salary_max=50000))

    def test_salary_max_equals_min_passes(self) -> None:
        record = JobRecord(**self._base_record(salary_min=100000, salary_max=100000))
        assert record.salary_min == record.salary_max
