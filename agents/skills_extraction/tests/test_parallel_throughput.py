"""Throughput benchmark: proves parallel extraction is faster than serial.

These tests use mocked LLM calls with a simulated per-call latency so the
wall-clock timing is deterministic and environment-independent.  They serve
as a regression guard for the acceptance criterion:

    "Tasks, responsibilities, and skills extraction run concurrently for each
     job (intra-job parallelism). Multiple jobs processed concurrently with
     configurable concurrency limit (inter-job parallelism)."

The tests do NOT make real Azure OpenAI calls.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord
from agents.skills_extraction.extractors.responsibilities import _ResponsibilitiesLLMRoot
from agents.skills_extraction.extractors.skills import _LLMSkill, _SkillsLLMRoot
from agents.skills_extraction.extractors.tasks import _TasksLLMRoot

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SIMULATED_LLM_LATENCY_S = 0.05  # 50 ms per mock LLM call — fast but still measurable


def _make_job(n: int) -> JobRecord:
    return JobRecord(
        source="bench",
        external_id=f"bench-job-{n}",
        title=f"Engineer {n}",
        company="Bench Corp",
        description="Design systems and mentor the team.",
        requirements="Python required.",
        responsibilities="Own backend.",
    )


def _make_event(n_records: int = 1) -> EventEnvelope:
    return EventEnvelope(
        correlation_id="corr-bench",
        agent_id="normalization-agent",
        payload={"batch_id": "bench-batch", "record_count": n_records, "records": []},
    )


def _make_work_item(n: int) -> MagicMock:
    item = MagicMock()
    item.job_id = f"job-{n}"
    item.posting_id = None
    item.normalized_job_id = n
    item.title = f"Engineer {n}"
    item.company = "Bench Corp"
    item.job_record = _make_job(n)
    return item


def _dim_meta(success: bool = True) -> dict:
    return {
        "success": success,
        "extraction_failed": not success,
        "tokens_used": 30,
        "cost_usd": 0.003,
        "latency_ms": int(_SIMULATED_LLM_LATENCY_S * 1000),
        "provider": "azure-openai",
        "model": "bench-deployment",
        "error_reason": None,
    }


async def _slow_tasks_invoke(*_args, **_kwargs):
    await asyncio.sleep(_SIMULATED_LLM_LATENCY_S)
    return _TasksLLMRoot(tasks=[]), _dim_meta()


async def _slow_resp_invoke(*_args, **_kwargs):
    await asyncio.sleep(_SIMULATED_LLM_LATENCY_S)
    return _ResponsibilitiesLLMRoot(responsibilities=[]), _dim_meta()


async def _slow_skills_invoke(*_args, **_kwargs):
    await asyncio.sleep(_SIMULATED_LLM_LATENCY_S)
    return _SkillsLLMRoot(skills=[]), _dim_meta()


# ---------------------------------------------------------------------------
# Intra-job parallelism: three LLM calls per job run concurrently
# ---------------------------------------------------------------------------


def test_intra_job_parallel_faster_than_serial() -> None:
    """Three intra-job LLM calls (tasks + responsibilities + skills) must run
    concurrently: wall time ≈ 1× latency, not 3× latency."""
    from agents.skills_extraction.agent import SkillsExtractionAgent

    item = _make_work_item(1)
    mock_loader = MagicMock()
    mock_loader.load.return_value = [item]
    mock_store = MagicMock()

    agent = SkillsExtractionAgent(work_item_loader=mock_loader, extraction_store=mock_store)
    in_flight = 0
    max_in_flight = 0

    async def _tracked(root):
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        try:
            await asyncio.sleep(_SIMULATED_LLM_LATENCY_S)
            return root, _dim_meta()
        finally:
            in_flight -= 1

    async def _tracked_tasks(*_args, **_kwargs):
        return await _tracked(_TasksLLMRoot(tasks=[]))

    async def _tracked_resp(*_args, **_kwargs):
        return await _tracked(_ResponsibilitiesLLMRoot(responsibilities=[]))

    async def _tracked_skills(*_args, **_kwargs):
        return await _tracked(_SkillsLLMRoot(skills=[]))

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_tracked_tasks),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_tracked_resp),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_tracked_skills),
        ),
        patch(
            "agents.skills_extraction.agent.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
    ):
        start = time.perf_counter()
        asyncio.run(agent.process_async(_make_event(1)))
        elapsed = time.perf_counter() - start

    serial_lower_bound = 3 * _SIMULATED_LLM_LATENCY_S
    parallel_upper_bound = _SIMULATED_LLM_LATENCY_S * 2.2
    assert max_in_flight == 3, (
        f"Expected all three intra-job LLM calls to overlap, but observed only {max_in_flight} concurrent call(s)."
    )
    assert elapsed < parallel_upper_bound, (
        f"Intra-job parallel took {elapsed:.3f}s — expected < {parallel_upper_bound:.3f}s "
        f"(serial lower bound is {serial_lower_bound:.3f}s). "
        "Tasks/responsibilities/skills are not running concurrently."
    )


# ---------------------------------------------------------------------------
# Inter-job parallelism: N jobs processed concurrently
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("n_jobs,concurrency", [(5, 5), (10, 5)])
def test_inter_job_parallel_faster_than_serial(n_jobs: int, concurrency: int) -> None:
    """N jobs processed with concurrency C must complete in roughly N/C × per-job
    time, not N × per-job time (serial)."""
    from agents.skills_extraction.agent import SkillsExtractionAgent

    items = [_make_work_item(i) for i in range(n_jobs)]
    mock_loader = MagicMock()
    mock_loader.load.return_value = items
    mock_store = MagicMock()

    agent = SkillsExtractionAgent(work_item_loader=mock_loader, extraction_store=mock_store)

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_slow_tasks_invoke),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_slow_resp_invoke),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_slow_skills_invoke),
        ),
        patch(
            "agents.skills_extraction.agent.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
        patch.dict("os.environ", {"SKILLS_EXTRACTION_CONCURRENCY": str(concurrency)}),
    ):
        start = time.perf_counter()
        asyncio.run(agent.process_async(_make_event(n_jobs)))
        elapsed = time.perf_counter() - start

    # Serial lower bound: n_jobs × per-job latency (single LLM call dominates).
    serial_lower_bound = n_jobs * _SIMULATED_LLM_LATENCY_S
    # Parallel upper bound: ceil(n_jobs / concurrency) × per-job latency × 2.5 (CI jitter).
    import math

    parallel_expected = math.ceil(n_jobs / concurrency) * _SIMULATED_LLM_LATENCY_S * 2.5

    assert elapsed < serial_lower_bound, (
        f"Inter-job parallel ({n_jobs} jobs, concurrency={concurrency}) took {elapsed:.3f}s "
        f"but serial lower bound is {serial_lower_bound:.3f}s — parallelism not working."
    )
    assert elapsed < parallel_expected, (
        f"Parallel run ({n_jobs} jobs, concurrency={concurrency}) took {elapsed:.3f}s, "
        f"expected < {parallel_expected:.3f}s."
    )


# ---------------------------------------------------------------------------
# Partial failure: one failed dimension does not block others
# ---------------------------------------------------------------------------


def test_failed_dimension_does_not_block_other_dimensions() -> None:
    """A 429 on tasks must not prevent responsibilities and skills from returning results."""
    from agents.skills_extraction.agent import SkillsExtractionAgent

    item = _make_work_item(1)
    mock_loader = MagicMock()
    mock_loader.load.return_value = [item]
    mock_store = MagicMock()

    agent = SkillsExtractionAgent(work_item_loader=mock_loader, extraction_store=mock_store)

    tasks_429_meta = {
        "success": False,
        "extraction_failed": True,
        "is_rate_limit": True,
        "retry_after_seconds": None,
        "error_reason": "429: Rate limit",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 5,
        "provider": "azure-openai",
        "model": "tasks-deployment",
    }

    async def _fail_tasks(*_args, **_kwargs):
        return None, tasks_429_meta

    skills_root = _SkillsLLMRoot(
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

    with (
        patch(
            "agents.skills_extraction.extractors.tasks.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_fail_tasks),
        ),
        patch(
            "agents.skills_extraction.extractors.tasks.asyncio.sleep",
            new=AsyncMock(),
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.ainvoke_structured_extraction_llm",
            new=AsyncMock(side_effect=_slow_resp_invoke),
        ),
        patch(
            "agents.skills_extraction.extractors.skills.ainvoke_structured_extraction_llm",
            new=AsyncMock(return_value=(skills_root, _dim_meta())),
        ),
        patch(
            "agents.skills_extraction.agent.resolve_taxonomy_batch",
            side_effect=lambda labels: [None] * len(labels),
        ),
    ):
        result_event = asyncio.run(agent.process_async(_make_event(1)))

    assert isinstance(result_event, EventEnvelope)
    payload = result_event.payload
    assert payload["failed_count"] == 0
    assert payload["skills_count"] == 1
    assert payload["extraction_status"] == "degraded"
    assert len(payload["records"]) == 1
    assert payload["records"][0]["extraction_status"] == "degraded"
