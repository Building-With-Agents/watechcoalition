"""Unit tests for async Pass 2 extractors."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.common.types import JobRecord
from agents.skills_extraction.extractors.responsibilities import (
    _ResponsibilitiesLLMRoot,
    extract_responsibilities,
    extract_responsibilities_async,
)
from agents.skills_extraction.extractors.skills import (
    _LLMSkill,
    _SkillsLLMRoot,
    extract_skills_no_taxonomy,
    extract_skills_no_taxonomy_async,
)
from agents.skills_extraction.extractors.tasks import (
    _TasksLLMRoot,
    extract_tasks,
    extract_tasks_async,
)


@pytest.fixture
def dummy_job() -> JobRecord:
    """Minimal valid JobRecord for async extraction tests."""
    return JobRecord(
        source="test",
        external_id="job-async-1",
        title="Senior Engineer",
        company="Acme",
        description="Design APIs with Python and mentor the team.",
        requirements="Python experience required.",
        responsibilities="Own backend delivery.",
    )


def test_extract_tasks_async_matches_sync_contract(dummy_job: JobRecord) -> None:
    """Async tasks extraction should preserve the sync result and metadata shape."""
    root = _TasksLLMRoot(
        tasks=[
            {
                "task_description": "Design APIs",
                "task_category": "technical",
                "seniority_signal": "senior",
                "confidence": 0.91,
                "source_span": {
                    "text": "Design APIs",
                    "field_source": "description",
                    "start_char": 0,
                    "end_char": 11,
                },
            }
        ]
    )
    call_meta = {
        "tokens_used": 22,
        "cost_usd": 0.01,
        "latency_ms": 250,
        "success": True,
        "extraction_failed": False,
        "error_reason": None,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.invoke_structured_extraction_llm",
            return_value=(root, call_meta),
        ),
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(root, call_meta)),
        ),
    ):
        sync_tasks, sync_meta = extract_tasks(dummy_job)
        async_tasks, async_meta = asyncio.run(extract_tasks_async(dummy_job))

    assert [task.model_dump() for task in async_tasks] == [task.model_dump() for task in sync_tasks]
    assert async_meta == sync_meta


def test_extract_responsibilities_async_matches_sync_contract(dummy_job: JobRecord) -> None:
    """Async responsibilities extraction should preserve the sync result and metadata shape."""
    root = _ResponsibilitiesLLMRoot(
        responsibilities=[
            {
                "responsibility_description": "Own backend delivery",
                "scope": "team",
                "requires_ai_competency": False,
                "confidence": 0.89,
                "source_span": {
                    "text": "Own backend delivery.",
                    "field_source": "responsibilities",
                    "start_char": 0,
                    "end_char": 21,
                },
            }
        ]
    )
    call_meta = {
        "tokens_used": 18,
        "cost_usd": 0.02,
        "latency_ms": 300,
        "success": True,
        "extraction_failed": False,
        "error_reason": None,
        "provider": "azure-openai",
        "model": "responsibilities-deployment",
    }

    with (
        patch(
            "agents.skills_extraction.extractors.responsibilities.invoke_structured_extraction_llm",
            return_value=(root, call_meta),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(root, call_meta)),
        ),
    ):
        sync_rows, sync_meta = extract_responsibilities(dummy_job)
        async_rows, async_meta = asyncio.run(extract_responsibilities_async(dummy_job))

    assert [row.model_dump() for row in async_rows] == [row.model_dump() for row in sync_rows]
    assert async_meta == sync_meta


def test_extract_skills_no_taxonomy_async_matches_sync_contract(dummy_job: JobRecord) -> None:
    """Async skills extraction should preserve the sync no-taxonomy contract."""
    root = _SkillsLLMRoot(
        skills=[
            _LLMSkill(
                label="Python",
                type="Technical",
                confidence=0.92,
                source_span={
                    "text": "Python",
                    "field_source": "requirements",
                    "start_char": 0,
                    "end_char": 6,
                },
            )
        ]
    )
    call_meta = {
        "tokens_used": 50,
        "cost_usd": 0.03,
        "latency_ms": 450,
        "success": True,
        "extraction_failed": False,
        "error_reason": None,
        "provider": "azure-openai",
        "model": "skills-deployment",
    }

    with (
        patch(
            "agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm",
            return_value=(root, call_meta),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(root, call_meta)),
        ),
    ):
        sync_skills, sync_meta = extract_skills_no_taxonomy(dummy_job)
        async_skills, async_meta = asyncio.run(extract_skills_no_taxonomy_async(dummy_job))

    assert [skill.model_dump() for skill in async_skills] == [skill.model_dump() for skill in sync_skills]
    assert async_meta == sync_meta


def test_extract_skills_no_taxonomy_async_retries_on_429_with_async_backoff(
    dummy_job: JobRecord,
) -> None:
    """The async skills extractor should await backoff and retry after 429s."""
    rate_limit_meta = {
        "success": False,
        "extraction_failed": True,
        "is_rate_limit": True,
        "retry_after_seconds": 10,
        "error_reason": "429: Rate limit reached",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 50,
        "provider": "azure-openai",
        "model": "skills-deployment",
    }
    success_root = _SkillsLLMRoot(
        skills=[
            _LLMSkill(
                label="Python",
                type="Technical",
                confidence=0.9,
                source_span={
                    "text": "Python",
                    "field_source": "requirements",
                    "start_char": 0,
                    "end_char": 6,
                },
            )
        ]
    )
    success_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 100,
        "cost_usd": 0.01,
        "latency_ms": 500,
        "provider": "azure-openai",
        "model": "skills-deployment",
    }
    sleep_mock = AsyncMock()

    with (
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=[(None, rate_limit_meta), (success_root, success_meta)]),
        ),
        patch("agents.skills_extraction.extractors.skills.asyncio.sleep", new=sleep_mock),
        patch("agents.skills_extraction.extractors.skills.random.uniform", return_value=0.5),
    ):
        skills, meta = asyncio.run(extract_skills_no_taxonomy_async(dummy_job))

    assert len(skills) == 1
    assert skills[0].skill_name == "Python"
    assert meta["success"] is True
    assert meta["extraction_failed"] is False
    sleep_mock.assert_any_await(10.5)


def test_extract_skills_no_taxonomy_async_returns_empty_on_failed_dimension(
    dummy_job: JobRecord,
) -> None:
    """Failed async extraction should return ``([], metadata)`` without raising."""
    failed_meta = {
        "success": False,
        "extraction_failed": True,
        "error_reason": "structured_output_empty",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 10,
        "provider": "azure-openai",
        "model": "skills-deployment",
    }

    with patch(
        "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
        new=AsyncMock(return_value=(None, failed_meta)),
    ):
        skills, meta = asyncio.run(extract_skills_no_taxonomy_async(dummy_job))

    assert skills == []
    assert meta["extraction_failed"] is True
    assert meta["error_reason"] == "structured_output_empty"
