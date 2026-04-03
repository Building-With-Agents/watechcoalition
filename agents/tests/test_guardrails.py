"""Tests for analytics staleness guardrails."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

import agents.analytics.insights.guardrails as guardrails
from agents.analytics.insights.guardrails import (
    build_cardinality_warning_payload,
    build_stale_alert_payload,
    cap_cardinality,
    check_staleness,
)


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


def test_cap_cardinality_under_limit_unchanged() -> None:
    values = [f"v{i}" for i in range(10)]
    out, warn = cap_cardinality(values, limit=50)
    assert out == values
    assert warn is False


def test_cap_cardinality_over_limit_appends_other() -> None:
    values = [f"v{i}" for i in range(12)]
    out, warn = cap_cardinality(values, limit=10)
    assert warn is True
    assert out == values[:10] + ["Other"]
    assert out[-1] == "Other"


def test_cap_cardinality_exactly_at_limit_no_warning() -> None:
    values = [f"v{i}" for i in range(10)]
    out, warn = cap_cardinality(values, limit=10)
    assert warn is False
    assert out == values


def test_cap_cardinality_other_appears_once_when_many_coalesced() -> None:
    values = [f"v{i}" for i in range(1000)]
    out, warn = cap_cardinality(values, limit=500)
    assert warn is True
    assert out.count("Other") == 1
    assert out[-1] == "Other"
    assert len(out) == 501


def test_build_cardinality_warning_payload_shape() -> None:
    fixed = datetime(2026, 3, 1, 9, 0, 0, tzinfo=timezone.utc)
    with patch.object(guardrails, "_utc_now", return_value=fixed):
        payload = build_cardinality_warning_payload(
            "skill_demand_weekly",
            "skill_label",
            1200,
            500,
        )
    assert payload["event_type"] == "CardinalityWarning"
    assert payload["table"] == "skill_demand_weekly"
    assert payload["column"] == "skill_label"
    assert payload["cardinality_count"] == 1200
    assert payload["threshold"] == 500
    assert payload["triggered_at"] == fixed.isoformat()


def test_cardinality_cap_configurable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(guardrails, "CARDINALITY_CAP", 3)
    values = ["a", "b", "c", "d", "e"]
    out, warn = cap_cardinality(values)
    assert warn is True
    assert out == ["a", "b", "c", "Other"]
