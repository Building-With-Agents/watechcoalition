"""Tests for analytics staleness guardrails."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

import agents.analytics.insights.guardrails as guardrails
from agents.analytics.insights.guardrails import build_stale_alert_payload, check_staleness


def test_check_staleness_fresh_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    computed = fixed_now - timedelta(minutes=10)
    monkeypatch.setattr(guardrails, "STALENESS_THRESHOLD_MINUTES", 15)
    with patch.object(guardrails, "_utc_now", return_value=fixed_now):
        assert check_staleness("analytics_aggregates", computed) is False


def test_check_staleness_stale_returns_true(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    computed = fixed_now - timedelta(minutes=20)
    monkeypatch.setattr(guardrails, "STALENESS_THRESHOLD_MINUTES", 15)
    with patch.object(guardrails, "_utc_now", return_value=fixed_now):
        assert check_staleness("skill_demand_weekly", computed) is True


def test_check_staleness_exactly_at_threshold_returns_false(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    computed = fixed_now - timedelta(minutes=15)
    monkeypatch.setattr(guardrails, "STALENESS_THRESHOLD_MINUTES", 15)
    with patch.object(guardrails, "_utc_now", return_value=fixed_now):
        assert check_staleness("geo_demand_weekly", computed) is False


def test_build_stale_alert_payload_shape_and_age_minutes() -> None:
    computed = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    queried = datetime(2026, 1, 15, 10, 23, 0, tzinfo=timezone.utc)
    payload = build_stale_alert_payload("sector_summary_weekly", computed, queried)
    assert payload["event_type"] == "AnalyticsStaleAlert"
    assert payload["table_name"] == "sector_summary_weekly"
    assert payload["computed_at"] == computed.isoformat()
    assert payload["queried_at"] == queried.isoformat()
    assert payload["age_minutes"] == 23


def test_staleness_threshold_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    fixed_now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    computed = fixed_now - timedelta(minutes=2)
    monkeypatch.setattr(guardrails, "STALENESS_THRESHOLD_MINUTES", 1)
    with patch.object(guardrails, "_utc_now", return_value=fixed_now):
        assert check_staleness("t", computed) is True
