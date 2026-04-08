"""Unit tests for async Pass 2 extractors."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
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


# ---------------------------------------------------------------------------
# Tasks async — retry / 429 backoff
# ---------------------------------------------------------------------------

def test_extract_tasks_async_retries_on_429_with_backoff(dummy_job: JobRecord) -> None:
    """Tasks async extractor should await backoff then retry after a 429."""
    rate_limit_meta = {
        "success": False,
        "extraction_failed": True,
        "is_rate_limit": True,
        "retry_after_seconds": 8,
        "error_reason": "429: Rate limit reached",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 40,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }
    success_root = _TasksLLMRoot(
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
    success_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 80,
        "cost_usd": 0.005,
        "latency_ms": 400,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }
    sleep_mock = AsyncMock()

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=[(None, rate_limit_meta), (success_root, success_meta)]),
        ),
        patch("agents.skills_extraction.extractors.tasks.asyncio.sleep", new=sleep_mock),
        patch("agents.skills_extraction.extractors.tasks.random.uniform", return_value=0.5),
    ):
        tasks, meta = asyncio.run(extract_tasks_async(dummy_job))

    assert len(tasks) == 1
    assert tasks[0].task_description == "Design APIs"
    assert meta["success"] is True
    assert meta["extraction_failed"] is False
    sleep_mock.assert_any_await(8.5)


def test_extract_tasks_async_returns_empty_on_persistent_failure(dummy_job: JobRecord) -> None:
    """Tasks async extractor returns ``([], metadata)`` on permanent failure without raising."""
    failed_meta = {
        "success": False,
        "extraction_failed": True,
        "error_reason": "llm_timeout",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 10,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }

    with patch(
        "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
        new=AsyncMock(return_value=(None, failed_meta)),
    ):
        tasks, meta = asyncio.run(extract_tasks_async(dummy_job))

    assert tasks == []
    assert meta["extraction_failed"] is True


# ---------------------------------------------------------------------------
# Responsibilities async — retry / 429 backoff
# ---------------------------------------------------------------------------

def test_extract_responsibilities_async_retries_on_429_with_backoff(dummy_job: JobRecord) -> None:
    """Responsibilities async extractor should await backoff then retry after a 429."""
    rate_limit_meta = {
        "success": False,
        "extraction_failed": True,
        "is_rate_limit": True,
        "retry_after_seconds": 12,
        "error_reason": "429: Rate limit reached",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 50,
        "provider": "azure-openai",
        "model": "resp-deployment",
    }
    success_root = _ResponsibilitiesLLMRoot(
        responsibilities=[
            {
                "responsibility_description": "Own backend delivery",
                "scope": "team",
                "requires_ai_competency": False,
                "confidence": 0.88,
                "source_span": {
                    "text": "Own backend delivery.",
                    "field_source": "responsibilities",
                    "start_char": 0,
                    "end_char": 21,
                },
            }
        ]
    )
    success_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 90,
        "cost_usd": 0.008,
        "latency_ms": 450,
        "provider": "azure-openai",
        "model": "resp-deployment",
    }
    sleep_mock = AsyncMock()

    with (
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=[(None, rate_limit_meta), (success_root, success_meta)]),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.asyncio.sleep",
            new=sleep_mock,
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.random.uniform",
            return_value=0.5,
        ),
    ):
        rows, meta = asyncio.run(extract_responsibilities_async(dummy_job))

    assert len(rows) == 1
    assert rows[0].responsibility_description == "Own backend delivery"
    assert meta["success"] is True
    assert meta["extraction_failed"] is False
    sleep_mock.assert_any_await(12.5)


def test_extract_responsibilities_async_returns_empty_on_persistent_failure(
    dummy_job: JobRecord,
) -> None:
    """Responsibilities async extractor returns ``([], metadata)`` on permanent failure."""
    failed_meta = {
        "success": False,
        "extraction_failed": True,
        "error_reason": "structured_output_empty",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 10,
        "provider": "azure-openai",
        "model": "resp-deployment",
    }

    with patch(
        "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
        new=AsyncMock(return_value=(None, failed_meta)),
    ):
        rows, meta = asyncio.run(extract_responsibilities_async(dummy_job))

    assert rows == []
    assert meta["extraction_failed"] is True


# ---------------------------------------------------------------------------
# process_async() — async public entrypoint
# ---------------------------------------------------------------------------

def _make_normalization_event(batch_id: str = "b-async-1") -> EventEnvelope:
    return EventEnvelope(
        correlation_id="corr-async-test",
        agent_id="normalization-agent",
        payload={"batch_id": batch_id, "record_count": 1, "records": []},
    )


def test_process_async_returns_skills_extracted_event(dummy_job: JobRecord) -> None:
    """process_async() should return a valid SkillsExtracted EventEnvelope."""
    from agents.skills_extraction.agent import SkillsExtractionAgent

    mock_work_item = MagicMock()
    mock_work_item.job_id = "job-async-1"
    mock_work_item.posting_id = None
    mock_work_item.normalized_job_id = 1
    mock_work_item.title = "Senior Engineer"
    mock_work_item.company = "Acme"
    mock_work_item.job_record = dummy_job

    mock_loader = MagicMock()
    mock_loader.load.return_value = [mock_work_item]

    mock_store = MagicMock()

    success_root = _SkillsLLMRoot(
        skills=[
            _LLMSkill(
                skill_name="Python",
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
    success_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 80,
        "cost_usd": 0.01,
        "latency_ms": 300,
        "provider": "azure-openai",
        "model": "skills-deployment",
    }
    tasks_root = _TasksLLMRoot(tasks=[])
    resp_root = _ResponsibilitiesLLMRoot(responsibilities=[])
    dim_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 20,
        "cost_usd": 0.002,
        "latency_ms": 100,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }

    agent = SkillsExtractionAgent(
        work_item_loader=mock_loader,
        extraction_store=mock_store,
    )

    event = _make_normalization_event()

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(tasks_root, dim_meta)),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(resp_root, dim_meta)),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(success_root, success_meta)),
        ),
        patch(
            "agents.skills_extraction.extractors.taxonomy.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
        patch(
            "agents.skills_extraction.agent.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
    ):
        result_event = asyncio.run(agent.process_async(event))

    assert isinstance(result_event, EventEnvelope)
    assert result_event.agent_id == "skills-extraction-agent"
    assert result_event.correlation_id == "corr-async-test"
    assert "batch_id" in result_event.payload


def test_process_async_uses_parallel_path_from_async_context(dummy_job: JobRecord) -> None:
    """process_async() must NOT fall back to serial even when an event loop is running."""
    from agents.skills_extraction.agent import SkillsExtractionAgent

    mock_work_item = MagicMock()
    mock_work_item.job_id = "job-loop-1"
    mock_work_item.posting_id = None
    mock_work_item.normalized_job_id = 2
    mock_work_item.title = "Engineer"
    mock_work_item.company = "Corp"
    mock_work_item.job_record = dummy_job

    mock_loader = MagicMock()
    mock_loader.load.return_value = [mock_work_item]
    mock_store = MagicMock()

    tasks_root = _TasksLLMRoot(tasks=[])
    resp_root = _ResponsibilitiesLLMRoot(responsibilities=[])
    dim_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 10,
        "cost_usd": 0.001,
        "latency_ms": 50,
        "provider": "azure-openai",
        "model": "m",
    }

    agent = SkillsExtractionAgent(
        work_item_loader=mock_loader,
        extraction_store=mock_store,
    )
    event = _make_normalization_event("b-loop-1")

    parallel_batch_calls: list[str] = []

    original_batch = agent._extract_batch_parallel

    async def tracking_batch(work_items, *, concurrency, correlation_id=None):
        parallel_batch_calls.append("parallel")
        return await original_batch(work_items, concurrency=concurrency, correlation_id=correlation_id)

    agent._extract_batch_parallel = tracking_batch  # type: ignore[method-assign]

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(tasks_root, dim_meta)),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(resp_root, dim_meta)),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(_SkillsLLMRoot(skills=[]), dim_meta)),
        ),
        patch(
            "agents.skills_extraction.agent.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
    ):
        asyncio.run(agent.process_async(event))

    assert parallel_batch_calls == ["parallel"], (
        "process_async() must call _extract_batch_parallel, not the serial fallback"
    )
