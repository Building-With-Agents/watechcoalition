"""Schema validation unit tests for context, task, and responsibility extraction stubs."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter

from agents.common.types import JobRecord
from agents.common.types.extraction_types import ResponsibilityRecord, TaskRecord
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import extract_responsibilities
from agents.skills_extraction.extractors.tasks import extract_tasks
from agents.common.types.extraction_types import ContextSignal, SpanRecord


@pytest.fixture
def dummy_job() -> JobRecord:
    """Minimal valid JobRecord for use as extraction input."""
    return JobRecord(
        source="test",
        external_id="1",
        title="Test Job",
        company="Test Co",
    )


# --- ContextSignal schema and extract_context (Pair B) ---


def test_span_record_schema() -> None:
    """SpanRecord accepts required fields and validates."""
    span = SpanRecord(
        text="remote work",
        field_source="description",
        start_char=0,
        end_char=11,
    )
    assert span.text == "remote work"
    assert span.field_source == "description"
    assert span.start_char == 0
    assert span.end_char == 11


def test_context_signal_schema() -> None:
    """ContextSignal accepts signal_type, value, confidence, optional source_span."""
    span = SpanRecord(
        text="hybrid",
        field_source="description",
        start_char=10,
        end_char=16,
    )
    sig = ContextSignal(
        signal_type="remote_policy",
        value="hybrid",
        confidence=0.9,
        source_span=span,
    )
    assert sig.signal_type == "remote_policy"
    assert sig.value == "hybrid"
    assert sig.confidence == 0.9
    assert sig.source_span is not None
    assert sig.source_span.text == "hybrid"

    # Optional source_span (stub can return without span)
    sig2 = ContextSignal(signal_type="team_size", value="5-10", confidence=0.8, source_span=None)
    assert sig2.source_span is None


def test_extract_context_returns_empty_and_is_schema_valid() -> None:
    """extract_context takes a dict, returns [], and result is schema-valid list[ContextSignal]."""
    job_record = {"event_type": "NormalizationComplete", "normalized_count": 5}
    result = extract_context(job_record)
    assert result == []
    TypeAdapter(list[ContextSignal]).validate_python(result)


# --- Task and responsibility stubs ---


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
