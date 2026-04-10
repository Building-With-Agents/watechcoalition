"""Context extraction — dimension 5 of 6 (Pass 1, pattern matching only).

Zero LLM tokens. Regex/keyword patterns for remote policy, team size,
reporting structure, work methodology, and AI adoption signals.

Reference: ARCHITECTURE_DEEP.md § Work Intelligence Agent — hybrid extraction.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any, cast

import structlog

from agents.common.types import ContextSignal, JobRecord, SpanRecord
from agents.common.types.extraction_schemas import ContextSignalType

log = structlog.get_logger()

# (signal_type, compiled regex, confidence when matched)
_CONTEXT_PATTERNS: tuple[tuple[str, re.Pattern[str], float], ...] = (
    (
        "remote_policy",
        re.compile(
            r"\b(fully\s+remote|full-?time\s+remote|100%\s+remote|remote-?first|"
            r"hybrid|hybrid\s+work|2\s+days?\s+onsite|two\s+days?\s+(?:a\s+week\s+)?onsite|"
            r"on-?site\s+(?:required|only)|work\s+from\s+home|wfh)\b",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "team_size",
        re.compile(
            r"\b(?:team\s+of\s+(\d+)|(\d+)\s*[-–]\s*(\d+)\s*person\s+team|"
            r"(\d+)\s*[-–]\s*(\d+)\s*member\s+team|(\d+)\s*person\s+team)\b",
            re.IGNORECASE,
        ),
        0.88,
    ),
    (
        "reporting_structure",
        re.compile(
            r"\b(reports?\s+to|direct\s+reports?|dotted-?line|matrix\s+reporting|"
            r"reporting\s+line|manager\s+of)\b",
            re.IGNORECASE,
        ),
        0.85,
    ),
    (
        "work_methodology",
        re.compile(
            r"\b(Agile|Scrum|Kanban|SAFe|Lean|sprint\s+planning|daily\s+stand-?up)\b",
            re.IGNORECASE,
        ),
        0.9,
    ),
    (
        "ai_adoption_signal",
        re.compile(
            r"\b(LLMs?|large\s+language\s+models?|generative\s+AI|gen-?ai|"
            r"AI-?first|machine\s+learning|ML\s+models?|deep\s+learning)\b",
            re.IGNORECASE,
        ),
        0.87,
    ),
)


def _iter_job_fields(job_record: JobRecord) -> Iterable[tuple[str, str]]:
    """Yield non-empty text fields in priority order (same as tools extractor)."""
    for field_source in ("title", "requirements", "responsibilities", "description"):
        value = getattr(job_record, field_source, None)
        if isinstance(value, str) and value.strip():
            yield field_source, value


def extract_context(
    job_record: JobRecord,
) -> tuple[list[ContextSignal], dict[str, Any]]:
    """Extract context signals using Pass 1 regex patterns only (no LLM).

    Parameters
    ----------
    job_record
        Normalized job posting.

    Returns
    -------
    tuple[list[ContextSignal], dict]
        Signals and metadata. ``tokens_used`` is always 0. On catastrophic
        regex failure, returns ``[]`` and logs a warning (never raises).
    """
    metadata: dict[str, Any] = {
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 0,
        "success": True,
        "extraction_failed": False,
        "error_reason": None,
        "provider": "pattern-matching",
        "model": "none",
        "extraction_metadata": {
            "extraction_version": "week5-context-pass1",
            "model_used": "none",
            "model_tier": "none",
            "tokens_used": 0,
            "cost_usd": 0.0,
            "extraction_duration_ms": 0,
            "pass1_tool_count": 0,
            "pass2_llm_dimensions": [],
            "pass2_llm_calls": 0,
            "extraction_warnings": [],
        },
    }

    signals: list[ContextSignal] = []

    try:
        fields = list(_iter_job_fields(job_record))
        for field_source, text in fields:
            for signal_type, pattern, confidence in _CONTEXT_PATTERNS:
                for match in pattern.finditer(text):
                    matched = match.group(0).strip()
                    if not matched:
                        continue
                    start, end = match.start(), match.end()
                    try:
                        span = SpanRecord(
                            text=matched,
                            field_source=field_source,  # type: ignore[arg-type]
                            start_char=start,
                            end_char=end,
                        )
                        signals.append(
                            ContextSignal(
                                signal_type=cast(ContextSignalType, signal_type),
                                value=matched,
                                confidence=confidence,
                                source_span=span,
                            )
                        )
                    except ValueError:
                        log.warning(
                            "context_extraction_invalid_span",
                            signal_type=signal_type,
                            field_source=field_source,
                        )
                        metadata["extraction_metadata"]["extraction_warnings"].append(f"invalid_span:{signal_type}")

        log.info(
            "context_extraction_complete",
            context_signal_count=len(signals),
            field_count=len(fields),
        )
        return signals, metadata
    except Exception as e:
        log.warning("context_extraction_pattern_failure", error_type=type(e).__name__)
        metadata["success"] = False
        metadata["extraction_failed"] = True
        metadata["error_reason"] = type(e).__name__
        metadata["extraction_metadata"]["extraction_warnings"].append("pattern_failure")
        return [], metadata


def _format_pass1_context_for_prompt(pass1_context: list[ContextSignal] | None) -> str:
    """Serialize Pass 1 context for injection into Pass 2 prompts (no raw job PII beyond signals)."""
    if not pass1_context:
        return "(none)"
    lines: list[str] = []
    for s in pass1_context:
        lines.append(f"- {s.signal_type}: {s.value} (confidence={s.confidence:.2f})")
    return "\n".join(lines)
