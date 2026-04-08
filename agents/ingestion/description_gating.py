"""Description text quality gate for JSearch detail backfill (Phase 1a).

Initial ingestion staging uses whitespace-only checks in
``raw_processing_status_for_record``; this module defines **substantive**
text for promoting ``awaiting_description`` → ``pending`` after a detail fetch.
"""

from __future__ import annotations

import os


def description_min_chars_from_env() -> int:
    """Minimum trimmed length to count as substantive (default 200)."""
    raw = os.getenv("DESCRIPTION_MIN_CHARS", "200")
    try:
        n = int(raw)
    except (TypeError, ValueError):
        return 200
    return max(1, min(n, 500_000))


def is_substantive_description(text: str | None) -> bool:
    """Return True if ``text`` is long enough to treat as a real job body."""
    if text is None:
        return False
    stripped = text.strip()
    if not stripped:
        return False
    return len(stripped) >= description_min_chars_from_env()


def description_gate_reason(text: str | None) -> str:
    """Short machine reason for logging (no PII)."""
    if text is None:
        return "null"
    stripped = text.strip()
    if not stripped:
        return "empty"
    if len(stripped) < description_min_chars_from_env():
        return "below_min_length"
    return "ok"
