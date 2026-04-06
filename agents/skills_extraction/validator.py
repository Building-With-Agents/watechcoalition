"""Extraction result validation — guardrails for SkillRecord/ToolRecord output.

validate_extraction_result() is called after every extraction (real or stub)
to flag data quality issues before writing to extracted_intelligence.

Warning categories (per Week 4 spec):
- missing_name: record has no name field
- low_confidence: confidence below threshold (default 0.5)
- empty_source_span: source_span is absent or empty string
- missing_esco_uri: esco_uri is null on a non-raw (linked/genai_extension) skill
"""

from __future__ import annotations

import structlog

from agents.common.types.skill_record import SkillRecord, ToolRecord

log = structlog.get_logger()

_DEFAULT_CONFIDENCE_THRESHOLD = 0.5


def validate_extraction_result(
    skills: list[dict],
    tools: list[dict],
    confidence_threshold: float = _DEFAULT_CONFIDENCE_THRESHOLD,
) -> list[str]:
    """Validate extraction output against SkillRecord/ToolRecord schemas.

    Accepts raw dicts (as stored in the DB / returned by LLM) and coerces
    them through the Pydantic models for field presence checks.

    Returns a list of human-readable warning strings. An empty list means
    the extraction passed all checks. Never raises — validation must not
    break the pipeline.
    """
    warnings: list[str] = []

    for i, raw in enumerate(skills):
        try:
            record = SkillRecord.model_validate(raw)
        except Exception as exc:
            warnings.append(f"skill[{i}] failed schema validation: {exc}")
            continue
        _check_skill(record, index=i, warnings=warnings, threshold=confidence_threshold)

    for i, raw in enumerate(tools):
        try:
            record = ToolRecord.model_validate(raw)
        except Exception as exc:
            warnings.append(f"tool[{i}] failed schema validation: {exc}")
            continue
        _check_tool(record, index=i, warnings=warnings, threshold=confidence_threshold)

    if warnings:
        log.warning(
            "extraction_validation_warnings",
            skill_count=len(skills),
            tool_count=len(tools),
            warning_count=len(warnings),
        )

    return warnings


def _check_skill(
    record: SkillRecord,
    index: int,
    warnings: list[str],
    threshold: float,
) -> None:
    if not record.name or not record.name.strip():
        warnings.append(f"skill[{index}] missing required field: name")

    if record.confidence < threshold:
        warnings.append(f"skill[{index}] '{record.name}' low confidence: {record.confidence:.2f} < {threshold}")

    if not record.source_span:
        warnings.append(f"skill[{index}] '{record.name}' empty source_span")

    if record.skill_type != "raw" and record.esco_uri is None:
        warnings.append(f"skill[{index}] '{record.name}' non-raw skill (type='{record.skill_type}') has null esco_uri")


def _check_tool(
    record: ToolRecord,
    index: int,
    warnings: list[str],
    threshold: float,
) -> None:
    if not record.name or not record.name.strip():
        warnings.append(f"tool[{index}] missing required field: name")

    if record.confidence < threshold:
        warnings.append(f"tool[{index}] '{record.name}' low confidence: {record.confidence:.2f} < {threshold}")

    if not record.source_span:
        warnings.append(f"tool[{index}] '{record.name}' empty source_span")
