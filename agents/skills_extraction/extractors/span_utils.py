"""Shared source_span auto-correction for all extraction dimensions.

LLMs frequently return ``end_char`` values that don't match
``start_char + len(text)``.  Rather than dropping the entire record,
we auto-correct ``end_char`` and flag the correction for audit.

Used by skills, tasks, and responsibilities extractors.
"""

from __future__ import annotations

from typing import Any

import structlog

from agents.common.types.extraction_types import SpanRecord

log = structlog.get_logger()


def auto_correct_span(
    raw_span: dict[str, Any],
    *,
    dimension: str = "unknown",
    label: str = "",
) -> tuple[SpanRecord, bool, int | None]:
    """Build a ``SpanRecord`` from a raw dict, auto-correcting ``end_char``.

    Parameters
    ----------
    raw_span
        Raw dict with ``text``, ``field_source``, ``start_char``, ``end_char``.
    dimension
        Extraction dimension name for structured logging (e.g. "tasks").
    label
        Human-readable label for the record being corrected.

    Returns
    -------
    tuple[SpanRecord, bool, int | None]
        (corrected SpanRecord, was_corrected, original_end_char or None)
    """
    text = str(raw_span.get("text", ""))
    field_source = raw_span.get("field_source", "description")
    start_char = int(raw_span.get("start_char", 0))
    end_char = int(raw_span.get("end_char", 0))
    expected_end = start_char + len(text)

    span_auto_corrected = False
    original_end_char: int | None = None

    if end_char != expected_end:
        log.debug(
            f"{dimension}_extraction_span_auto_correct",
            label=label,
            original_end_char=end_char,
            corrected_end_char=expected_end,
        )
        span_auto_corrected = True
        original_end_char = end_char
        end_char = expected_end

    span = SpanRecord(
        text=text,
        field_source=field_source,
        start_char=start_char,
        end_char=end_char,
    )
    return span, span_auto_corrected, original_end_char
