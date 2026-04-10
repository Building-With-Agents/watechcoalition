"""Tests for analytics posting freshness / staleness detection."""

from __future__ import annotations

from agents.analytics.insights.freshness import detect_staleness
from agents.common.data_store.models import (
    FRESH_THRESHOLD_DAYS,
    STALE_THRESHOLD_DAYS,
)


def test_fresh_record_below_fresh_threshold() -> None:
    days = max(0, FRESH_THRESHOLD_DAYS - 5)
    rows = [{"posting_id": "p-fresh", "days_since_posted": days}]
    out = detect_staleness(rows)
    assert len(out) == 1
    assert out[0].posting_id == "p-fresh"
    assert out[0].days_since_posted == days
    assert out[0].freshness_status == "fresh"


def test_stale_record_between_thresholds() -> None:
    assert FRESH_THRESHOLD_DAYS < STALE_THRESHOLD_DAYS
    days = (FRESH_THRESHOLD_DAYS + STALE_THRESHOLD_DAYS) // 2
    assert FRESH_THRESHOLD_DAYS < days < STALE_THRESHOLD_DAYS
    rows = [{"posting_id": "p-stale", "days_since_posted": days}]
    out = detect_staleness(rows)
    assert len(out) == 1
    assert out[0].freshness_status == "stale"


def test_expired_record_above_stale_threshold() -> None:
    days = STALE_THRESHOLD_DAYS + 10
    rows = [{"posting_id": "p-expired", "days_since_posted": days}]
    out = detect_staleness(rows)
    assert len(out) == 1
    assert out[0].freshness_status == "expired"


def test_boundary_days_equals_fresh_threshold_is_fresh() -> None:
    rows = [{"posting_id": "p-b1", "days_since_posted": FRESH_THRESHOLD_DAYS}]
    out = detect_staleness(rows)
    assert out[0].freshness_status == "fresh"


def test_boundary_days_equals_stale_threshold_is_stale() -> None:
    rows = [{"posting_id": "p-b2", "days_since_posted": STALE_THRESHOLD_DAYS}]
    out = detect_staleness(rows)
    assert out[0].freshness_status == "stale"


def test_empty_input_returns_empty() -> None:
    assert detect_staleness([]) == []

