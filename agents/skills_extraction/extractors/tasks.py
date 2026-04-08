"""Tasks extraction — dimension 3 of 6 (Pass 2, Haiku-class LLM).

Structured JSON via LangChain ``with_structured_output``. Consumes Pass 1
context signals as optional prompt context (no extra tokens for context
beyond prompt text).

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import structlog
from pydantic import BaseModel, Field

from agents.common.llm_client import (
    ainvoke_structured_extraction_llm,
    invoke_structured_extraction_llm,
)
from agents.common.types import ContextSignal, JobRecord, TaskRecord
from agents.skills_extraction.extractors._retry import (
    RATE_LIMIT_BACKOFF_SECS,
    RATE_LIMIT_MAX_CYCLES,
)
from agents.skills_extraction.extractors._retry import (
    is_rate_limited as _is_rate_limited,
)
from agents.skills_extraction.extractors._retry import (
    merge_retry_metadata as _merge_retry_metadata,
)
from agents.skills_extraction.extractors.context import _format_pass1_context_for_prompt

log = structlog.get_logger()

AGENT_TASKS = "skills-extraction-tasks"

_TASKS_DEPLOYMENT_KEYS = (
    "EXTRACTION_DEPLOYMENT_TASKS",
    "EXTRACTION_MODEL_TASKS",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)


class _TasksLLMRoot(BaseModel):
    """Root schema for structured LLM output (list of TaskRecord)."""

    tasks: list[TaskRecord] = Field(default_factory=list)


def _base_tasks_metadata() -> dict[str, Any]:
    """Standard metadata payload shared by sync and async task extraction."""
    return {
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "success": False,
        "extraction_failed": True,
        "error_reason": None,
        "provider": "azure-openai",
        "model": "",
        "extraction_metadata": {},
    }


def _tasks_extraction_metadata(call_meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize task extractor metadata for downstream aggregation."""
    return {
        "extraction_version": "week5-tasks-pass2",
        "model_used": call_meta.get("model", ""),
        "model_tier": "haiku",
        "tokens_used": call_meta.get("tokens_used", 0),
        "cost_usd": call_meta.get("cost_usd", 0.0),
        "extraction_duration_ms": call_meta.get("latency_ms", 0),
        "pass2_llm_dimensions": ["tasks"],
        "pass2_llm_calls": 1,
        "extraction_warnings": [],
    }


def _build_tasks_prompt(job_record: JobRecord, pass1_context: list[ContextSignal] | None) -> str:
    """Build user prompt with instructions and few-shot examples (no employer PII in examples)."""
    ctx_block = _format_pass1_context_for_prompt(pass1_context)
    title = job_record.title or ""
    description = job_record.description or ""
    requirements = job_record.requirements or ""
    responsibilities = job_record.responsibilities or ""

    return f"""You extract discrete, actionable TASKS from a job posting. Output JSON matching the schema: a "tasks" array. Each task must include:
- task_description: short verb phrase
- task_category: one of core | supporting | management | technical
- seniority_signal: one of entry | mid | senior | lead | any
- confidence: 0.0-1.0
- source_span: exact substring from the job text with field_source one of title, description, requirements, responsibilities; start_char and end_char are character offsets in THAT field only (0-based, end exclusive); span text length must equal end_char - start_char.

Pass 1 context signals (use to disambiguate seniority when helpful):
{ctx_block}

Few-shot examples (mapping phrase → seniority_signal, task_category):
1) "mentor junior engineers" → seniority_signal: lead (or senior), task_category: management
2) "assist with testing" → seniority_signal: entry or mid, task_category: supporting
3) "design system architecture" → seniority_signal: senior, task_category: technical

Job fields follow. Extract all clearly stated tasks; do not invent work not implied by the text.

--- TITLE ---
{title}

--- DESCRIPTION ---
{description}

--- REQUIREMENTS ---
{requirements}

--- RESPONSIBILITIES ---
{responsibilities}
"""


def extract_tasks(
    job_record: JobRecord,
    pass1_context: list[ContextSignal] | None = None,
) -> tuple[list[TaskRecord], dict[str, Any]]:
    """Extract tasks using a Haiku-class Azure deployment and structured output.

    Parameters
    ----------
    job_record
        Normalized job record.
    pass1_context
        Pass 1 ``ContextSignal`` list from ``extract_context`` (optional).

    Returns
    -------
    tuple[list[TaskRecord], dict]
        Tasks and metadata (tokens_used, cost_usd, extraction_failed, etc.).
        On LLM failure: empty list, extraction_failed True, error logged — never raises.
    """
    metadata = _base_tasks_metadata()

    try:
        prompt = _build_tasks_prompt(job_record, pass1_context)
    except Exception as e:
        log.error("tasks_extraction_prompt_build_failed", error_type=type(e).__name__)
        metadata["error_reason"] = type(e).__name__
        return [], metadata

    try:
        parsed, call_meta = invoke_structured_extraction_llm(
            prompt,
            _TasksLLMRoot,
            agent_name=AGENT_TASKS,
            deployment_env_keys=_TASKS_DEPLOYMENT_KEYS,
            model_tier_for_cost="haiku",
        )
        metadata.update(call_meta)
        metadata["extraction_metadata"] = _tasks_extraction_metadata(call_meta)

        if parsed is None or call_meta.get("extraction_failed"):
            log.error(
                "tasks_extraction_llm_failed",
                extraction_failed=True,
                error_reason=call_meta.get("error_reason"),
            )
            metadata["extraction_failed"] = True
            return [], metadata

        tasks = list(parsed.tasks)
        metadata["extraction_failed"] = False
        metadata["success"] = True
        log.info("tasks_extraction_complete", task_count=len(tasks))
        return tasks, metadata
    except Exception as e:
        log.error("tasks_extraction_unhandled", error_type=type(e).__name__)
        metadata["extraction_failed"] = True
        metadata["error_reason"] = type(e).__name__
        return [], metadata


async def extract_tasks_async(
    job_record: JobRecord,
    pass1_context: list[ContextSignal] | None = None,
) -> tuple[list[TaskRecord], dict[str, Any]]:
    """Async counterpart to ``extract_tasks`` with timeout retry and 429 backoff.

    Retry strategy mirrors ``extract_skills_no_taxonomy_async``:
    - One timeout retry after 0.5 s.
    - Up to ``RATE_LIMIT_MAX_CYCLES`` backoff cycles on 429, with jitter.
    - A failed call returns ``([], metadata)`` — never raises.
    """
    metadata = _base_tasks_metadata()

    try:
        prompt = _build_tasks_prompt(job_record, pass1_context)
    except Exception as e:
        log.error("tasks_extraction_prompt_build_failed", error_type=type(e).__name__)
        metadata["error_reason"] = type(e).__name__
        return [], metadata

    async def _do_invoke() -> tuple[_TasksLLMRoot | None, dict[str, Any]]:
        return await ainvoke_structured_extraction_llm(
            prompt,
            _TasksLLMRoot,
            agent_name=AGENT_TASKS,
            deployment_env_keys=_TASKS_DEPLOYMENT_KEYS,
            model_tier_for_cost="haiku",
        )

    parsed: _TasksLLMRoot | None = None
    meta: dict[str, Any] = {}

    # Level 1: one timeout retry
    for timeout_attempt in range(2):
        try:
            parsed, meta = await _do_invoke()
            metadata.update(meta)
            break
        except Exception as e:
            err_str = str(e).lower()
            if ("timeout" in err_str or isinstance(e, TimeoutError)) and timeout_attempt == 0:
                await asyncio.sleep(0.5)
                continue
            metadata["error_reason"] = str(e)
            metadata["extraction_failed"] = True
            return [], metadata

    # Level 2: rate-limit backoff
    if _is_rate_limited(meta):
        for cycle, fallback_delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_tasks_extraction"] = True
                return [], metadata
            server_delay = meta.get("retry_after_seconds")
            base_delay = server_delay if server_delay else fallback_delay
            jitter = random.uniform(0.5, min(base_delay * 0.3, 5.0))
            actual_delay = base_delay + jitter
            log.info(
                "tasks_extraction_429_backoff",
                cycle=cycle,
                delay_seconds=round(actual_delay, 1),
                server_retry_after=server_delay,
            )
            await asyncio.sleep(actual_delay)
            try:
                parsed, meta = await _do_invoke()
                _merge_retry_metadata(metadata, meta)
                if meta.get("success") and parsed is not None:
                    metadata.update(meta)
                    break
            except Exception as e:
                metadata["error_reason"] = str(e)
        else:
            metadata["alert_tasks_extraction"] = True
            return [], metadata

    if not meta.get("success") or parsed is None:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        metadata["extraction_failed"] = True
        return [], metadata

    metadata["extraction_metadata"] = _tasks_extraction_metadata(meta)
    tasks = list(parsed.tasks)
    metadata["extraction_failed"] = False
    metadata["success"] = True
    log.info("tasks_extraction_complete", task_count=len(tasks))
    return tasks, metadata
