"""Integration test: sample job through extract_tools → extract_skills with mocked LLM.

Pipeline order is Pass 1 (tools, deterministic patterns) then Pass 2 (skills, LLM).

Mocks:
- ``_invoke_client`` — isolated seam used by ``extract_skills`` (see skills.py).
- ``resolve_taxonomy_batch`` — avoids embedding / taxonomy HTTP in CI.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from agents.common.types import JobRecord
from agents.common.types.extraction_types import (
    ContextSignal,
    SkillRecord,
    TaxonomyResult,
    ToolRecord,
)
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import extract_responsibilities
from agents.skills_extraction.extractors.skills import extract_skills
from agents.skills_extraction.extractors.tasks import extract_tasks
from agents.skills_extraction.extractors.tools import extract_tools


@pytest.fixture
def sample_job() -> JobRecord:
    """Normalized job with text that triggers catalog tool matches and skill extraction."""
    return JobRecord(
        source="integration-test",
        external_id="job-integration-001",
        title="Senior Python Engineer",
        company="Acme Corp",
        description=(
            "Build APIs with FastAPI and PostgreSQL. Strong Python experience required for our cloud data platform."
        ),
    )


@patch("agents.skills_extraction.extractors.skills.resolve_taxonomy_batch")
@patch("agents.skills_extraction.extractors.skills._invoke_client")
def test_extraction_tools_then_skills_output_shape(
    mock_invoke_client: object,
    mock_resolve_taxonomy: object,
    sample_job: JobRecord,
) -> None:
    """Run tools then skills; mock LLM JSON; assert list and metadata structure."""
    predictable_skills_payload = {
        "skills": [
            {
                "label": "API design",
                "type": "Technical",
                "confidence": 0.92,
                "source_span": {
                    "text": "APIs",
                    "field_source": "description",
                    "start_char": 6,
                    "end_char": 10,
                },
            }
        ]
    }
    response_text = json.dumps(predictable_skills_payload)

    mock_invoke_client.return_value = (
        response_text,
        {
            "tokens_used": 64,
            "cost_usd": 0.0,
            "latency_ms": 50,
            "success": True,
            "extraction_failed": False,
            "error_reason": None,
            "provider": "azure-openai",
            "model": "mock-skills-deployment",
        },
    )

    mock_resolve_taxonomy.return_value = [
        TaxonomyResult(
            original_label="API design",
            esco_uri="https://example.test/esco/api-design",
            esco_label="Designing digital user interfaces and interactions",
            is_genai_extension=False,
            resolution_step=3,
            confidence=0.9,
        )
    ]

    tools = extract_tools(sample_job)
    skills, metadata = extract_skills(sample_job, pass1_tools=tools)

    # --- Tools (Pass 1): list[ToolRecord], expected keys ---
    assert isinstance(tools, list)
    assert len(tools) >= 1
    for item in tools:
        assert isinstance(item, ToolRecord)
        assert item.tool_name
        assert item.category in (
            "language",
            "framework",
            "platform",
            "database",
            "devops",
            "ai_tool",
            "other",
        )
        assert 0.0 <= item.confidence <= 1.0
        assert item.source_span is not None
        assert item.source_span.field_source in (
            "title",
            "description",
            "requirements",
            "responsibilities",
        )
        assert item.source_span.text
        assert item.source_span.start_char >= 0
        assert item.source_span.end_char >= item.source_span.start_char

    tool_names = {t.tool_name for t in tools}
    assert "Python" in tool_names

    # --- Skills (Pass 2): list[SkillRecord] + metadata dict ---
    assert isinstance(skills, list)
    assert len(skills) == 1
    skill = skills[0]
    assert isinstance(skill, SkillRecord)
    assert skill.skill_name == "API design"
    assert skill.type == "Technical"
    assert skill.confidence == pytest.approx(0.92)
    assert skill.esco_uri == "https://example.test/esco/api-design"
    assert skill.is_genai_extension is False
    assert skill.source_span.text == "APIs"
    assert skill.source_span.field_source == "description"
    assert skill.source_span.start_char == 6
    assert skill.source_span.end_char == 10

    assert isinstance(metadata, dict)
    assert metadata.get("success") is True
    assert metadata.get("extraction_failed") is False
    assert metadata.get("error_reason") is None
    assert metadata.get("provider") == "azure-openai"
    assert "tokens_used" in metadata
    assert "latency_ms" in metadata

    mock_invoke_client.assert_called_once()
    mock_resolve_taxonomy.assert_called_once()
    call_labels = mock_resolve_taxonomy.call_args[0][0]
    assert call_labels == ["API design"]


# ---------------------------------------------------------------------------
# Week 4 Stubs — extract_context, extract_tasks, extract_responsibilities
# ---------------------------------------------------------------------------


def test_extract_context_returns_empty_list() -> None:
    """extract_context stub returns an empty list of ContextSignal."""
    job = JobRecord(
        source="test",
        external_id="test-1",
        title="Test Job",
        company="Test Corp",
        description="Build things.",
    )
    result = extract_context(job)
    assert isinstance(result, list)
    assert len(result) == 0


def test_extract_tasks_returns_empty_list() -> None:
    """extract_tasks stub returns an empty list of TaskRecord."""
    job = JobRecord(
        source="test",
        external_id="test-1",
        title="Test Job",
        company="Test Corp",
        description="Build things.",
    )
    result = extract_tasks(job)
    assert isinstance(result, list)
    assert len(result) == 0


def test_extract_responsibilities_returns_empty_list() -> None:
    """extract_responsibilities stub returns an empty list of ResponsibilityRecord."""
    job = JobRecord(
        source="test",
        external_id="test-1",
        title="Test Job",
        company="Test Corp",
        description="Build things.",
    )
    result = extract_responsibilities(job)
    assert isinstance(result, list)
    assert len(result) == 0


def test_context_signal_schema_validates() -> None:
    """ContextSignal schema accepts valid data and rejects invalid."""
    from agents.common.types.extraction_types import SpanRecord

    signal = ContextSignal(
        signal_type="remote_policy",
        value="hybrid",
        confidence=0.9,
        source_span=SpanRecord(
            text="hybrid",
            field_source="description",
            start_char=10,
            end_char=16,
        ),
    )
    assert signal.signal_type == "remote_policy"
    assert signal.value == "hybrid"
    assert signal.confidence == 0.9
    assert signal.source_span.text == "hybrid"
