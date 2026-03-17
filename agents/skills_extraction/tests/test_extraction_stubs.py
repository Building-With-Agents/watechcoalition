"""Schema validation unit tests for the task and responsibility extraction stubs."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter

from agents.common.types import JobRecord
from agents.common.types.extraction_types import ResponsibilityRecord, TaskRecord
from agents.skills_extraction.extractors.responsibilities import extract_responsibilities
from agents.skills_extraction.extractors.tasks import extract_tasks


@pytest.fixture
def dummy_job() -> JobRecord:
    """Minimal valid JobRecord for use as extraction input."""
    return JobRecord(
        source="test",
        external_id="1",
        title="Test Job",
        company="Test Co",
    )


def test_extract_tasks_returns_empty_and_is_schema_valid(dummy_job: JobRecord) -> None:
    """extract_tasks returns [] and the result is schema-valid list[TaskRecord]."""
    result = extract_tasks(dummy_job)
    assert result == []
    TypeAdapter(list[TaskRecord]).validate_python(result)


def test_extract_responsibilities_returns_empty_and_is_schema_valid(dummy_job: JobRecord) -> None:
    """extract_responsibilities returns [] and the result is schema-valid list[ResponsibilityRecord]."""
    result = extract_responsibilities(dummy_job)
    assert result == []
    TypeAdapter(list[ResponsibilityRecord]).validate_python(result)
