"""Skills extraction — Pass 2 (LLM-based).

Extracts nuanced skills from normalized job postings using a Sonnet-class LLM.
Each skill is linked to the ESCO digital skills taxonomy via the 6-step
resolution order, with GenAI Extension Layer checked first.

Week 4 implementation (Bryan + Emilio):
- Consume normalized JobRecord documents
- Extract skills from title, description, requirements, responsibilities
- Produce SkillRecord per skill with esco_uri and source_span
- Use Sonnet-class model (configured via EXTRACTION_MODEL_SKILLS env var)
- Track tokens_used per extraction call
- Handle LLM timeout: retry once, then emit with skills=[] and extraction_failed=true
- Handle rate limit (429): exponential back-off with SkillsExtractionAlert

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — Hybrid Extraction.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

import structlog

from agents.common.types import JobRecord, SkillRecord, SpanRecord, TaxonomyResult, ToolRecord
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy_batch
from agents.skills_extraction.prompts import build_skills_prompt

log = structlog.get_logger()

# Back-off delays for 429 in seconds
RATE_LIMIT_BACKOFF_SECS = (1, 2, 4)
RATE_LIMIT_MAX_CYCLES = 3

DEFAULT_SKILL_CONFIDENCE_THRESHOLD = 0.75


def _skill_confidence_threshold() -> float:
    """Minimum confidence for a skill to be kept; skills below this are discarded."""
    try:
        return float(os.getenv("SKILL_CONFIDENCE_THRESHOLD", str(DEFAULT_SKILL_CONFIDENCE_THRESHOLD)))
    except (TypeError, ValueError):
        return DEFAULT_SKILL_CONFIDENCE_THRESHOLD


def _invoke_client(prompt: str) -> tuple[str, dict[str, Any]]:
    """Call the LLM client. Isolated for testing."""
    from agents.common.llm_client import invoke_skills_llm
    return invoke_skills_llm(prompt)


def _parse_skills_response(response_text: str) -> list[dict[str, Any]]:
    """Extract skills array from LLM JSON response. Strips markdown code blocks if present."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    try:
        data = json.loads(text)
        raw = data.get("skills")
        return list(raw) if isinstance(raw, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def _skill_dict_to_record(raw: dict[str, Any]) -> SkillRecord | None:
    """Build SkillRecord from parsed dict. Returns None if validation fails.

    Auto-corrects source_span when the LLM returns end_char such that
    end_char - start_char != len(text): sets end_char = start_char + len(text)
    so the skill is kept instead of dropped (avoids skills_extraction_skip_invalid_skill).
    """
    from pydantic import ValidationError
    try:
        span = raw.get("source_span")
        if not isinstance(span, dict):
            return None
        text = str(span.get("text", ""))
        field_source = span.get("field_source", "description")
        start_char = int(span.get("start_char", 0))
        end_char = int(span.get("end_char", 0))
        expected_end = start_char + len(text)
        span_auto_corrected = False
        original_end_char = None
        if end_char != expected_end:
            log.debug(
                "skills_extraction_span_auto_correct",
                label=raw.get("label"),
                original_end_char=end_char,
                corrected_end_char=expected_end,
            )
            span_auto_corrected = True
            original_end_char = end_char
            end_char = expected_end
        source_span = SpanRecord(
            text=text,
            field_source=field_source,
            start_char=start_char,
            end_char=end_char,
        )
        return SkillRecord(
            skill_name=str(raw.get("skill_name") or raw.get("label", "")).strip() or "unknown",
            type=raw.get("type", "Technical"),
            confidence=float(raw.get("confidence", 0.0)),
            required_flag=raw.get("required_flag"),
            source_span=source_span,
            span_auto_corrected=span_auto_corrected,
            original_end_char=original_end_char,
        )
    except (ValidationError, TypeError, ValueError, KeyError):
        return None


def extract_skills(
    job_record: JobRecord,
    pass1_tools: list[ToolRecord] | None = None,
) -> tuple[list[SkillRecord], dict[str, Any]]:
    """Extract skills from a normalized job record using LLM inference.

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
    already_tools = [t.tool_name for t in (pass1_tools or [])]
    prompt = build_skills_prompt(
        title=job_record.title or "",
        description=job_record.description or "",
        requirements=job_record.requirements or "",
        responsibilities=job_record.responsibilities or "",
        already_extracted_tool_names=already_tools,
    )

    metadata: dict[str, Any] = {
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

    text = ""
    meta: dict[str, Any] = {}

    def _do_invoke() -> tuple[str, dict[str, Any]]:
        return _invoke_client(prompt)

    # Timeout: retry once
    for timeout_attempt in range(2):
        try:
            text, meta = _do_invoke()
            metadata.update(meta)
            break
        except Exception as e:
            err_str = str(e).lower()
            if ("timeout" in err_str or isinstance(e, TimeoutError)) and timeout_attempt == 0:
                time.sleep(0.5)
                continue
            metadata["error_reason"] = str(e)
            return [], metadata

    # 429: exponential back-off up to RATE_LIMIT_MAX_CYCLES
    is_rate_limited = not meta.get("success") and (
        meta.get("is_rate_limit")
        or meta.get("retry_after_seconds") is not None
        or "429" in str(meta.get("error_reason", ""))
    )
    if is_rate_limited:
        for cycle, delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_skills_extraction"] = True
                return [], metadata
            # Honor server Retry-After if provided, otherwise use backoff sequence
            server_delay = meta.get("retry_after_seconds")
            actual_delay = server_delay if server_delay and cycle == 0 else delay
            time.sleep(actual_delay)
            try:
                text, meta = _do_invoke()
                metadata["tokens_used"] = metadata.get("tokens_used", 0) + meta.get("tokens_used", 0)
                metadata["cost_usd"] = metadata.get("cost_usd", 0.0) + meta.get("cost_usd", 0.0)
                metadata["latency_ms"] = metadata.get("latency_ms", 0) + meta.get("latency_ms", 0)
                metadata["provider"] = meta.get("provider", metadata["provider"])
                metadata["model"] = meta.get("model", metadata["model"])
                if meta.get("success") and text:
                    metadata.update(meta)
                    break
            except Exception as e2:
                metadata["error_reason"] = str(e2)
        else:
            metadata["alert_skills_extraction"] = True
            return [], metadata

    if not meta.get("success") or not text:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        return [], metadata

    raw_skills = _parse_skills_response(text)
    if not raw_skills:
        log.warning("skills_extraction_empty_or_invalid_json", raw_preview=text[:500])
        metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
            "LLM response had no valid skills array"
        ]
        metadata["extraction_failed"] = True
        return [], metadata

    skills: list[SkillRecord] = []
    for raw in raw_skills:
        rec = _skill_dict_to_record(raw)
        if rec is None:
            log.warning("skills_extraction_skip_invalid_skill", raw=raw)
            metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
                f"Invalid skill skipped: {raw.get('label', raw)}"
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
    already_tools = [t.tool_name for t in (pass1_tools or [])]
    prompt = build_skills_prompt(
        title=job_record.title or "",
        description=job_record.description or "",
        requirements=job_record.requirements or "",
        responsibilities=job_record.responsibilities or "",
        already_extracted_tool_names=already_tools,
    )

    metadata: dict[str, Any] = {
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

    text = ""
    meta: dict[str, Any] = {}

    def _do_invoke() -> tuple[str, dict[str, Any]]:
        return _invoke_client(prompt)

    for timeout_attempt in range(2):
        try:
            text, meta = _do_invoke()
            metadata.update(meta)
            break
        except Exception as e:
            err_str = str(e).lower()
            if ("timeout" in err_str or isinstance(e, TimeoutError)) and timeout_attempt == 0:
                time.sleep(0.5)
                continue
            metadata["error_reason"] = str(e)
            return [], metadata

    is_rate_limited = not meta.get("success") and (
        meta.get("is_rate_limit")
        or meta.get("retry_after_seconds") is not None
        or "429" in str(meta.get("error_reason", ""))
    )
    if is_rate_limited:
        for cycle, delay in enumerate(RATE_LIMIT_BACKOFF_SECS):
            if cycle >= RATE_LIMIT_MAX_CYCLES:
                metadata["alert_skills_extraction"] = True
                return [], metadata
            server_delay = meta.get("retry_after_seconds")
            actual_delay = server_delay if server_delay and cycle == 0 else delay
            time.sleep(actual_delay)
            try:
                text, meta = _do_invoke()
                metadata["tokens_used"] = metadata.get("tokens_used", 0) + meta.get("tokens_used", 0)
                metadata["cost_usd"] = metadata.get("cost_usd", 0.0) + meta.get("cost_usd", 0.0)
                metadata["latency_ms"] = metadata.get("latency_ms", 0) + meta.get("latency_ms", 0)
                metadata["provider"] = meta.get("provider", metadata["provider"])
                metadata["model"] = meta.get("model", metadata["model"])
                if meta.get("success") and text:
                    metadata.update(meta)
                    break
            except Exception as e2:
                metadata["error_reason"] = str(e2)
        else:
            metadata["alert_skills_extraction"] = True
            return [], metadata

    if not meta.get("success") or not text:
        metadata["error_reason"] = meta.get("error_reason") or "empty response"
        return [], metadata

    raw_skills = _parse_skills_response(text)
    if not raw_skills:
        log.warning("skills_extraction_empty_or_invalid_json", raw_preview=text[:500])
        metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
            "LLM response had no valid skills array"
        ]
        metadata["extraction_failed"] = True
        return [], metadata

    skills: list[SkillRecord] = []
    for raw in raw_skills:
        rec = _skill_dict_to_record(raw)
        if rec is None:
            log.warning("skills_extraction_skip_invalid_skill", raw=raw)
            metadata["extraction_warnings"] = metadata.get("extraction_warnings", []) + [
                f"Invalid skill skipped: {raw.get('label', raw)}"
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
        return [], metadata

    # NOTE: No taxonomy resolution here — caller handles it in batch.
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
