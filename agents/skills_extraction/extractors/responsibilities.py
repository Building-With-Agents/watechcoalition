"""Responsibilities extraction — dimension 4 of 6 (Pass 2, Sonnet-class LLM).

Structured JSON via LangChain ``with_structured_output``. Infers scope
(individual → organization) and flags AI/ML competency requirements.

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent.
"""

from __future__ import annotations

from typing import Any

import structlog
from pydantic import BaseModel, Field

from agents.common.llm_client import (
    ainvoke_structured_extraction_llm,
    invoke_structured_extraction_llm,
)
from agents.common.types import ContextSignal, JobRecord, ResponsibilityRecord
from agents.skills_extraction.extractors.context import _format_pass1_context_for_prompt

log = structlog.get_logger()

AGENT_RESPONSIBILITIES = "skills-extraction-responsibilities"

_RESP_DEPLOYMENT_KEYS = (
    "EXTRACTION_DEPLOYMENT_RESPONSIBILITIES",
    "EXTRACTION_MODEL_RESPONSIBILITIES",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)


class _ResponsibilitiesLLMRoot(BaseModel):
    """Root schema for structured LLM output (list of ResponsibilityRecord)."""

    responsibilities: list[ResponsibilityRecord] = Field(default_factory=list)


def _base_responsibilities_metadata() -> dict[str, Any]:
    """Standard metadata payload shared by sync and async responsibility extraction."""
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


def _responsibilities_extraction_metadata(call_meta: dict[str, Any]) -> dict[str, Any]:
    """Normalize responsibility extractor metadata for downstream aggregation."""
    return {
        "extraction_version": "week5-responsibilities-pass2",
        "model_used": call_meta.get("model", ""),
        "model_tier": "sonnet",
        "tokens_used": call_meta.get("tokens_used", 0),
        "cost_usd": call_meta.get("cost_usd", 0.0),
        "extraction_duration_ms": call_meta.get("latency_ms", 0),
        "pass2_llm_dimensions": ["responsibilities"],
        "pass2_llm_calls": 1,
        "extraction_warnings": [],
    }


def _build_responsibilities_prompt(
    job_record: JobRecord,
    pass1_context: list[ContextSignal] | None,
) -> str:
    """Build user prompt with scope heuristics and Pass 1 context."""
    ctx_block = _format_pass1_context_for_prompt(pass1_context)
    title = job_record.title or ""
    description = job_record.description or ""
    requirements = job_record.requirements or ""
    responsibilities = job_record.responsibilities or ""

    return f"""You extract high-level RESPONSIBILITIES (ownership areas, not granular tasks) from a job posting.
Output JSON matching the schema: a "responsibilities" array. Each item must include:
- responsibility_description: concise ownership statement
- scope: one of individual | team | department | organization (infer from language)
- requires_ai_competency: true if the responsibility involves AI, ML, LLMs, generative AI, or data science models; false otherwise
- confidence: 0.0-1.0
- source_span: exact substring from the job with field_source one of title, description, requirements, responsibilities; start_char/end_char are offsets within THAT field only; span text length must equal end_char - start_char.

Scope inference examples:
- "own the data platform" for a product/engineering team → scope: team
- "drive technical strategy across the organization" → scope: organization
- "deliver your assigned features" → scope: individual
- "lead the department's security practice" → scope: department

Pass 1 context signals:
{ctx_block}

Job text:

--- TITLE ---
{title}

--- DESCRIPTION ---
{description}

--- REQUIREMENTS ---
{requirements}

--- RESPONSIBILITIES ---
{responsibilities}
"""


def extract_responsibilities(
    job_record: JobRecord,
    pass1_context: list[ContextSignal] | None = None,
) -> tuple[list[ResponsibilityRecord], dict[str, Any]]:
    """Extract responsibilities using a Sonnet-class Azure deployment.

    Parameters
    ----------
    job_record
        Normalized job record.
    pass1_context
        Optional Pass 1 context from ``extract_context``.

    Returns
    -------
    tuple[list[ResponsibilityRecord], dict]
        Responsibilities and call metadata. On failure returns ``[]`` and
        sets extraction_failed — never raises.
    """
    metadata = _base_responsibilities_metadata()

    try:
        prompt = _build_responsibilities_prompt(job_record, pass1_context)
    except Exception as e:
        log.error(
            "responsibilities_extraction_prompt_build_failed",
            error_type=type(e).__name__,
        )
        metadata["error_reason"] = type(e).__name__
        return [], metadata

    try:
        parsed, call_meta = invoke_structured_extraction_llm(
            prompt,
            _ResponsibilitiesLLMRoot,
            agent_name=AGENT_RESPONSIBILITIES,
            deployment_env_keys=_RESP_DEPLOYMENT_KEYS,
            model_tier_for_cost="sonnet",
        )
        metadata.update(call_meta)
        metadata["extraction_metadata"] = _responsibilities_extraction_metadata(call_meta)

        if parsed is None or call_meta.get("extraction_failed"):
            log.error(
                "responsibilities_extraction_llm_failed",
                extraction_failed=True,
                error_reason=call_meta.get("error_reason"),
            )
            metadata["extraction_failed"] = True
            return [], metadata

        out = list(parsed.responsibilities)
        metadata["extraction_failed"] = False
        metadata["success"] = True
        log.info("responsibilities_extraction_complete", responsibility_count=len(out))
        return out, metadata
    except Exception as e:
        log.error("responsibilities_extraction_unhandled", error_type=type(e).__name__)
        metadata["extraction_failed"] = True
        metadata["error_reason"] = type(e).__name__
        return [], metadata


async def extract_responsibilities_async(
    job_record: JobRecord,
    pass1_context: list[ContextSignal] | None = None,
) -> tuple[list[ResponsibilityRecord], dict[str, Any]]:
    """Async counterpart to ``extract_responsibilities`` with identical output shape."""
    metadata = _base_responsibilities_metadata()

    try:
        prompt = _build_responsibilities_prompt(job_record, pass1_context)
    except Exception as e:
        log.error(
            "responsibilities_extraction_prompt_build_failed",
            error_type=type(e).__name__,
        )
        metadata["error_reason"] = type(e).__name__
        return [], metadata

    try:
        parsed, call_meta = await ainvoke_structured_extraction_llm(
            prompt,
            _ResponsibilitiesLLMRoot,
            agent_name=AGENT_RESPONSIBILITIES,
            deployment_env_keys=_RESP_DEPLOYMENT_KEYS,
            model_tier_for_cost="sonnet",
        )
        metadata.update(call_meta)
        metadata["extraction_metadata"] = _responsibilities_extraction_metadata(call_meta)

        if parsed is None or call_meta.get("extraction_failed"):
            log.error(
                "responsibilities_extraction_llm_failed",
                extraction_failed=True,
                error_reason=call_meta.get("error_reason"),
            )
            metadata["extraction_failed"] = True
            return [], metadata

        out = list(parsed.responsibilities)
        metadata["extraction_failed"] = False
        metadata["success"] = True
        log.info("responsibilities_extraction_complete", responsibility_count=len(out))
        return out, metadata
    except Exception as e:
        log.error("responsibilities_extraction_unhandled", error_type=type(e).__name__)
        metadata["extraction_failed"] = True
        metadata["error_reason"] = type(e).__name__
        return [], metadata
