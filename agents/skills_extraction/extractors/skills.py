"""Skills extraction — Pass 2 (LLM-based).

Extracts nuanced skills from normalized job postings using a Sonnet-class LLM.
Each skill is linked to the ESCO digital skills taxonomy via the 6-step
resolution order, with GenAI Extension Layer checked first.

Uses ``invoke_structured_extraction_llm`` with a Pydantic root model
(``_SkillsLLMRoot``) for consistent structured output across all extraction
dimensions (matching tasks.py and responsibilities.py).  SpanRecord
auto-correction happens at the Pydantic validator level.

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — Hybrid Extraction.
"""

from __future__ import annotations

import asyncio
import os
import random
import time
from typing import Any

import structlog
from pydantic import BaseModel, Field

from agents.common.llm_client import (
    ainvoke_structured_extraction_llm,
    invoke_structured_extraction_llm,
)
from agents.common.types import JobRecord, SkillRecord, TaxonomyResult, ToolRecord
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy_batch
from agents.skills_extraction.prompts import build_skills_prompt

log = structlog.get_logger()

# Back-off delays for 429 in seconds. Azure OpenAI typically asks for 10-30s.
# Jitter added at runtime to prevent thundering herd.
RATE_LIMIT_BACKOFF_SECS = (5, 15, 30, 60)
RATE_LIMIT_MAX_CYCLES = 4

DEFAULT_SKILL_CONFIDENCE_THRESHOLD = 0.75

AGENT_SKILLS = "skills-extraction-agent"

_SKILLS_DEPLOYMENT_KEYS = (
    "EXTRACTION_DEPLOYMENT_SKILLS",
    "EXTRACTION_MODEL_SKILLS",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
)


# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output
# ---------------------------------------------------------------------------

class _LLMSkill(BaseModel):
    """Single skill from LLM structured output.

    Uses ``label`` (the prompt field name) and maps to ``skill_name`` on
    SkillRecord during post-processing.
    """

    label: str = ""
    type: str = "Technical"
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    required_flag: bool | None = None
    source_span: dict[str, Any] = Field(default_factory=dict)


class _SkillsLLMRoot(BaseModel):
    """Root schema for structured LLM output (list of skills)."""

    skills: list[_LLMSkill] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _skill_confidence_threshold() -> float:
    """Minimum confidence for a skill to be kept; skills below this are discarded."""
    try:
        return float(os.getenv("SKILL_CONFIDENCE_THRESHOLD", str(DEFAULT_SKILL_CONFIDENCE_THRESHOLD)))
    except (TypeError, ValueError):
        return DEFAULT_SKILL_CONFIDENCE_THRESHOLD


def _llm_skill_to_record(raw: _LLMSkill) -> SkillRecord | None:
    """Convert an LLM skill to a SkillRecord. SpanRecord auto-corrects offsets."""
    from pydantic import ValidationError

    from agents.common.types.extraction_types import SpanRecord

    try:
        span_dict = raw.source_span
        if not span_dict or not isinstance(span_dict, dict):
            return None
        source_span = SpanRecord(
            text=str(span_dict.get("text", "")),
            field_source=span_dict.get("field_source", "description"),
            start_char=int(span_dict.get("start_char", 0)),
            end_char=int(span_dict.get("end_char", 0)),
        )
        return SkillRecord(
            skill_name=raw.label.strip() or "unknown",
            type=raw.type,
            confidence=raw.confidence,
            required_flag=raw.required_flag,
            source_span=source_span,
        )
    except (ValidationError, TypeError, ValueError, KeyError):
        return None


def _build_skills_prompt_for_job(
    job_record: JobRecord,
    pass1_tools: list[ToolRecord] | None = None,
) -> str:
    """Build the shared skills prompt, excluding already extracted tools."""
    already_tools = [t.tool_name for t in (pass1_tools or [])]
    return build_skills_prompt(
        title=job_record.title or "",
        description=job_record.description or "",
        requirements=job_record.requirements or "",
        responsibilities=job_record.responsibilities or "",
        already_extracted_tool_names=already_tools,
    )


def _base_skills_metadata() -> dict[str, Any]:
    """Standard metadata payload shared by sync and async skills extraction."""
    return {
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "success": False,
        "extraction_failed": True,
        "error_reason": None,
        "provider": "azure-openai",
        "model": "",
        "extraction_warnings": [],
    }


def _is_rate_limited(meta: dict[str, Any]) -> bool:
    """Return True when the LLM metadata indicates rate limiting."""
    return not meta.get("success") and (
        meta.get("is_rate_limit")
        or meta.get("retry_after_seconds") is not None
        or "429" in str(meta.get("error_reason", ""))
    )


def _merge_retry_metadata(metadata: dict[str, Any], meta: dict[str, Any]) -> None:
    """Accumulate retry metadata while keeping the latest provider/model labels."""
    metadata["tokens_used"] = metadata.get("tokens_used", 0) + meta.get("tokens_used", 0)
    metadata["cost_usd"] = metadata.get("cost_usd", 0.0) + meta.get("cost_usd", 0.0)
    metadata["latency_ms"] = metadata.get("latency_ms", 0) + meta.get("latency_ms", 0)
    metadata["provider"] = meta.get("provider", metadata["provider"])
    metadata["model"] = meta.get("model", metadata["model"])


def _post_process_llm_skills(
    parsed: _SkillsLLMRoot,
    metadata: dict[str, Any],
) -> list[SkillRecord]:
    """Convert structured LLM output into filtered SkillRecords."""
    if not parsed.skills:
        log.warning("skills_extraction_empty_skills_array")
        metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
            "LLM response had no valid skills array"
        ]
        metadata["extraction_failed"] = True
        return []

    skills: list[SkillRecord] = []
    for raw in parsed.skills:
        rec = _llm_skill_to_record(raw)
        if rec is None:
            log.warning("skills_extraction_skip_invalid_skill", label=raw.label)
            metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
                f"Invalid skill skipped: {raw.label}"
            ]
            continue
        skills.append(rec)

    threshold = _skill_confidence_threshold()
    n_before = len(skills)
    skills = [s for s in skills if s.confidence >= threshold]
    if len(skills) < n_before:
        log.info(
            "skills_extraction_below_confidence_threshold",
            threshold=threshold,
            discarded=n_before - len(skills),
            kept=len(skills),
        )

    if not skills:
        metadata["extraction_failed"] = True
        return []

    return skills


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def extract_skills(
    job_record: JobRecord,
    pass1_tools: list[ToolRecord] | None = None,
) -> tuple[list[SkillRecord], dict[str, Any]]:
    """Extract skills from a normalized job record using structured LLM output.

    Parameters
    ----------
    job_record : JobRecord
        A normalized job posting from the normalization pipeline.
    pass1_tools : list[ToolRecord] | None
        Already-extracted tools so the LLM does not re-extract them as skills.

    Returns
    -------
    tuple[list[SkillRecord], dict]
        (skills, metadata). metadata includes tokens_used, cost_usd, latency_ms,
        success, extraction_failed, error_reason, provider, model,
        and optionally alert_skills_extraction (True when 429 threshold exceeded).
    """
    prompt = _build_skills_prompt_for_job(job_record, pass1_tools)
    metadata = _base_skills_metadata()

    def _do_invoke() -> tuple[_SkillsLLMRoot | None, dict[str, Any]]:
        return invoke_structured_extraction_llm(
            prompt,
            _SkillsLLMRoot,
            agent_name=AGENT_SKILLS,
            deployment_env_keys=_SKILLS_DEPLOYMENT_KEYS,
            model_tier_for_cost="sonnet",
        )

    # Timeout: retry once
    parsed: _SkillsLLMRoot | None = None
    meta: dict[str, Any] = {}
    for timeout_attempt in range(2):
        try:
            parsed, meta = _do_invoke()
            metadata.update(meta)
            break
        except Exception as e:
            err_str = str(e).lower()
            if ("timeout" in err_str or isinstance(e, TimeoutError)) and timeout_attempt == 0:
                time.sleep(0.5)
                continue
            metadata["error_reason"] = str(e)
            return [], metadata

    # 429: back-off with jitter, always respecting server Retry-After header
    is_rate_limited = _is_rate_limited(meta)
    if is_rate_limited:
        for cycle, fallback_delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_skills_extraction"] = True
                return [], metadata
            server_delay = meta.get("retry_after_seconds")
            base_delay = server_delay if server_delay else fallback_delay
            jitter = random.uniform(0.5, min(base_delay * 0.3, 5.0))
            actual_delay = base_delay + jitter
            log.info(
                "skills_extraction_429_backoff",
                cycle=cycle,
                delay_seconds=round(actual_delay, 1),
                server_retry_after=server_delay,
            )
            time.sleep(actual_delay)
            try:
                parsed, meta = _do_invoke()
                _merge_retry_metadata(metadata, meta)
                if meta.get("success") and parsed is not None:
                    metadata.update(meta)
                    break
            except Exception as e2:
                metadata["error_reason"] = str(e2)
        else:
            metadata["alert_skills_extraction"] = True
            return [], metadata

    if not meta.get("success") or parsed is None:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        return [], metadata

    skills = _post_process_llm_skills(parsed, metadata)
    if not skills:
        return [], metadata

    labels = [s.skill_name for s in skills]
    taxonomy_results = resolve_taxonomy_batch(labels)
    for i, res in enumerate(taxonomy_results):
        if i < len(skills):
            skills[i] = SkillRecord(
                skill_id=skills[i].skill_id,
                skill_name=skills[i].skill_name,
                type=skills[i].type,
                confidence=skills[i].confidence,
                required_flag=skills[i].required_flag,
                esco_uri=res.esco_uri,
                is_genai_extension=res.is_genai_extension,
                source_span=skills[i].source_span,
                span_auto_corrected=skills[i].span_auto_corrected,
                original_end_char=skills[i].original_end_char,
            )

    metadata["success"] = True
    metadata["extraction_failed"] = False
    metadata["error_reason"] = None
    return skills, metadata


def extract_skills_no_taxonomy(
    job_record: JobRecord,
    pass1_tools: list[ToolRecord] | None = None,
) -> tuple[list[SkillRecord], dict[str, Any]]:
    """Extract skills via LLM but defer taxonomy resolution.

    Identical to extract_skills() except it skips the resolve_taxonomy_batch()
    call. Returns SkillRecords with esco_uri=None and is_genai_extension=False.

    The caller is responsible for collecting all labels across jobs, calling
    resolve_taxonomy_batch() once, and applying results via
    apply_taxonomy_to_skills().
    """
    prompt = _build_skills_prompt_for_job(job_record, pass1_tools)
    metadata = _base_skills_metadata()

    def _do_invoke() -> tuple[_SkillsLLMRoot | None, dict[str, Any]]:
        return invoke_structured_extraction_llm(
            prompt,
            _SkillsLLMRoot,
            agent_name=AGENT_SKILLS,
            deployment_env_keys=_SKILLS_DEPLOYMENT_KEYS,
            model_tier_for_cost="sonnet",
        )

    parsed: _SkillsLLMRoot | None = None
    meta: dict[str, Any] = {}

    for timeout_attempt in range(2):
        try:
            parsed, meta = _do_invoke()
            metadata.update(meta)
            break
        except Exception as e:
            err_str = str(e).lower()
            if ("timeout" in err_str or isinstance(e, TimeoutError)) and timeout_attempt == 0:
                time.sleep(0.5)
                continue
            metadata["error_reason"] = str(e)
            return [], metadata

    is_rate_limited = _is_rate_limited(meta)
    if is_rate_limited:
        for cycle, fallback_delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_skills_extraction"] = True
                return [], metadata
            server_delay = meta.get("retry_after_seconds")
            base_delay = server_delay if server_delay else fallback_delay
            jitter = random.uniform(0.5, min(base_delay * 0.3, 5.0))
            actual_delay = base_delay + jitter
            time.sleep(actual_delay)
            try:
                parsed, meta = _do_invoke()
                _merge_retry_metadata(metadata, meta)
                if meta.get("success") and parsed is not None:
                    metadata.update(meta)
                    break
            except Exception as e2:
                metadata["error_reason"] = str(e2)
        else:
            metadata["alert_skills_extraction"] = True
            return [], metadata

    if not meta.get("success") or parsed is None:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        return [], metadata

    skills = _post_process_llm_skills(parsed, metadata)
    if not skills:
        return [], metadata

    # NOTE: No taxonomy resolution here — caller handles it in batch.
    metadata["success"] = True
    metadata["extraction_failed"] = False
    metadata["error_reason"] = None
    return skills, metadata


async def extract_skills_no_taxonomy_async(
    job_record: JobRecord,
    pass1_tools: list[ToolRecord] | None = None,
) -> tuple[list[SkillRecord], dict[str, Any]]:
    """Async counterpart to ``extract_skills_no_taxonomy`` with async retry/backoff."""
    prompt = _build_skills_prompt_for_job(job_record, pass1_tools)
    metadata = _base_skills_metadata()

    async def _do_invoke() -> tuple[_SkillsLLMRoot | None, dict[str, Any]]:
        return await ainvoke_structured_extraction_llm(
            prompt,
            _SkillsLLMRoot,
            agent_name=AGENT_SKILLS,
            deployment_env_keys=_SKILLS_DEPLOYMENT_KEYS,
            model_tier_for_cost="sonnet",
        )

    parsed: _SkillsLLMRoot | None = None
    meta: dict[str, Any] = {}

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
            return [], metadata

    if _is_rate_limited(meta):
        for cycle, fallback_delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_skills_extraction"] = True
                return [], metadata
            server_delay = meta.get("retry_after_seconds")
            base_delay = server_delay if server_delay else fallback_delay
            jitter = random.uniform(0.5, min(base_delay * 0.3, 5.0))
            actual_delay = base_delay + jitter
            log.info(
                "skills_extraction_429_backoff",
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
            except Exception as e2:
                metadata["error_reason"] = str(e2)
        else:
            metadata["alert_skills_extraction"] = True
            return [], metadata

    if not meta.get("success") or parsed is None:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        return [], metadata

    skills = _post_process_llm_skills(parsed, metadata)
    if not skills:
        return [], metadata

    metadata["success"] = True
    metadata["extraction_failed"] = False
    metadata["error_reason"] = None
    return skills, metadata


def apply_taxonomy_to_skills(
    skills: list[SkillRecord],
    taxonomy_map: dict[str, TaxonomyResult],
) -> list[SkillRecord]:
    """Apply pre-resolved taxonomy results to SkillRecords.

    Used after extract_skills_no_taxonomy() when taxonomy resolution was
    deferred to a single batch call across all jobs.
    """
    result = []
    for skill in skills:
        res = taxonomy_map.get(skill.skill_name)
        if res:
            skill = SkillRecord(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                type=skill.type,
                confidence=skill.confidence,
                required_flag=skill.required_flag,
                esco_uri=res.esco_uri,
                is_genai_extension=res.is_genai_extension,
                source_span=skill.source_span,
                span_auto_corrected=skill.span_auto_corrected,
                original_end_char=skill.original_end_char,
            )
        result.append(skill)
    return result
