"""Unit tests for context (Pass 1), tasks, and responsibilities extractors."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from pydantic import TypeAdapter

from agents.common.types import (
    ContextSignal,
    JobRecord,
    ResponsibilityRecord,
    SpanRecord,
    TaskRecord,
)
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import (
    _ResponsibilitiesLLMRoot,
    extract_responsibilities,
)
from agents.skills_extraction.extractors.tasks import _TasksLLMRoot, extract_tasks


@pytest.fixture
def dummy_job() -> JobRecord:
    """Minimal valid JobRecord for use as extraction input."""
    return JobRecord(
        source="test",
        external_id="1",
        title="Test Job",
        company="Test Co",
    )


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
    """ContextSignal requires signal_type, value, confidence, source_span."""
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
    assert sig.source_span.text == "hybrid"


def test_extract_context_empty_when_no_matches(dummy_job: JobRecord) -> None:
    """extract_context returns schema-valid list when no regex matches."""
    signals, meta = extract_context(dummy_job)
    assert meta.get("tokens_used") == 0
    TypeAdapter(list[ContextSignal]).validate_python(signals)


def test_extract_context_finds_hybrid() -> None:
    """Pattern match for remote_policy / hybrid."""
    job = JobRecord(
        source="test",
        external_id="2",
        title="Engineer",
        company="Acme",
        description="We offer a hybrid schedule for this role.",
    )
    signals, meta = extract_context(job)
    assert meta.get("tokens_used") == 0
    assert any(s.signal_type == "remote_policy" for s in signals)


@patch("agents.skills_extraction.extractors.tasks.invoke_structured_extraction_llm")
def test_extract_tasks_returns_empty_on_llm_failure(
    mock_invoke: object,
    dummy_job: JobRecord,
) -> None:
    """On LLM failure extract_tasks returns [] and marks extraction_failed."""
    mock_invoke.return_value = (None, {"extraction_failed": True, "error_reason": "test"})
    tasks, meta = extract_tasks(dummy_job)
    assert tasks == []
    assert meta.get("extraction_failed") is True
    TypeAdapter(list[TaskRecord]).validate_python(tasks)


@patch("agents.skills_extraction.extractors.tasks.invoke_structured_extraction_llm")
def test_extract_tasks_validates_schema_on_success(
    mock_invoke: object,
    dummy_job: JobRecord,
) -> None:
    """Structured output with empty tasks list is schema-valid."""
    mock_invoke.return_value = (
        _TasksLLMRoot(tasks=[]),
        {
            "extraction_failed": False,
            "tokens_used": 10,
            "cost_usd": 0.0,
            "model": "test-deployment",
        },
    )
    tasks, meta = extract_tasks(dummy_job)
    assert meta.get("extraction_failed") is False
    TypeAdapter(list[TaskRecord]).validate_python(tasks)


@patch("agents.skills_extraction.extractors.responsibilities.invoke_structured_extraction_llm")
def test_extract_responsibilities_returns_empty_on_llm_failure(
    mock_invoke: object,
    dummy_job: JobRecord,
) -> None:
    mock_invoke.return_value = (None, {"extraction_failed": True, "error_reason": "test"})
    rows, meta = extract_responsibilities(dummy_job)
    assert rows == []
    assert meta.get("extraction_failed") is True
    TypeAdapter(list[ResponsibilityRecord]).validate_python(rows)


@patch("agents.skills_extraction.extractors.responsibilities.invoke_structured_extraction_llm")
def test_extract_responsibilities_validates_schema_on_success(
    mock_invoke: object,
    dummy_job: JobRecord,
) -> None:
    mock_invoke.return_value = (
        _ResponsibilitiesLLMRoot(responsibilities=[]),
        {
            "extraction_failed": False,
            "tokens_used": 12,
            "cost_usd": 0.0,
            "model": "test-deployment",
        },
    )
    rows, meta = extract_responsibilities(dummy_job)
    assert meta.get("extraction_failed") is False
    TypeAdapter(list[ResponsibilityRecord]).validate_python(rows)
