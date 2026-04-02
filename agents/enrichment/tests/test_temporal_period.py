"""Unit tests for deterministic temporal period classification (UTC calendar date)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from agents.enrichment.classifiers.temporal_period import classify_temporal_period


@pytest.mark.parametrize(
    ("posted_at", "expected"),
    [
        (datetime(2022, 11, 30, tzinfo=timezone.utc), "pre_chatgpt"),
        (datetime(2022, 12, 1, tzinfo=timezone.utc), "early_genai"),
        (datetime(2023, 3, 31, tzinfo=timezone.utc), "early_genai"),
        (datetime(2023, 4, 1, tzinfo=timezone.utc), "post_gpt4"),
        (datetime(2024, 5, 31, tzinfo=timezone.utc), "post_gpt4"),
        (datetime(2024, 6, 1, tzinfo=timezone.utc), "agentic_era"),
    ],
)
def test_classify_temporal_period_boundaries(posted_at: datetime, expected: str) -> None:
    assert classify_temporal_period(posted_at) == expected


def test_classify_temporal_period_non_boundary_mid_bucket() -> None:
    assert classify_temporal_period(datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc)) == "post_gpt4"
    assert classify_temporal_period(datetime(2025, 1, 1, 0, 0, tzinfo=timezone.utc)) == "agentic_era"


def test_classify_temporal_period_none_returns_none() -> None:
    assert classify_temporal_period(None) is None


def test_classify_temporal_period_uses_utc_calendar_date_not_local_wall_clock() -> None:
    """Same local calendar evening can be next UTC day (crosses pre vs early_genai)."""
    la = ZoneInfo("America/Los_Angeles")
    # 2022-11-30 20:00 PST = 2022-12-01 04:00 UTC → early_genai
    assert classify_temporal_period(datetime(2022, 11, 30, 20, 0, tzinfo=la)) == "early_genai"
    # 2022-11-30 12:00 PST = 2022-11-30 20:00 UTC → pre_chatgpt
    assert classify_temporal_period(datetime(2022, 11, 30, 12, 0, tzinfo=la)) == "pre_chatgpt"
