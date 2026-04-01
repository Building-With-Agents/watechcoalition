"""Deterministic job-posting temporal buckets from a single posted timestamp.

Classification uses the **UTC calendar date** of ``posted_at``: timezone-aware
values are converted with ``astimezone(timezone.utc)`` before taking ``.date()``;
naive datetimes are treated as UTC wall time (``replace(tzinfo=UTC)``) so the
result does not depend on the host local timezone.

Maps to string labels aligned with ``dbo.job_postings.temporal_period`` (TEXT).
No LLM; boundaries are fixed module-level dates.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

# Inclusive-range boundaries on the UTC calendar.
DATE_EARLY_GENAI_START = date(2022, 12, 1)
DATE_EARLY_GENAI_END = date(2023, 3, 31)
DATE_POST_GPT4_START = date(2023, 4, 1)
DATE_POST_GPT4_END = date(2024, 5, 31)
DATE_AGENTIC_ERA_START = date(2024, 6, 1)


def _utc_calendar_date(posted_at: datetime) -> date:
    if posted_at.tzinfo is None:
        return posted_at.replace(tzinfo=timezone.utc).date()
    return posted_at.astimezone(timezone.utc).date()


def classify_temporal_period(posted_at: datetime | None) -> str | None:
    """Return temporal bucket for ``posted_at``, or ``None`` if input is ``None``.

    Buckets (UTC date ``d``):
    - ``pre_chatgpt``: d < 2022-12-01
    - ``early_genai``: 2022-12-01 <= d <= 2023-03-31
    - ``post_gpt4``: 2023-04-01 <= d <= 2024-05-31
    - ``agentic_era``: d >= 2024-06-01
    """
    if posted_at is None:
        return None

    d = _utc_calendar_date(posted_at)

    if d < DATE_EARLY_GENAI_START:
        return "pre_chatgpt"
    if d <= DATE_EARLY_GENAI_END:
        return "early_genai"
    if DATE_POST_GPT4_START <= d <= DATE_POST_GPT4_END:
        return "post_gpt4"
    # Remaining UTC dates: ``d`` > DATE_POST_GPT4_END ⇒ ``d`` >= DATE_AGENTIC_ERA_START.
    return "agentic_era"
