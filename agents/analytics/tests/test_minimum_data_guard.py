"""Tests for analytics minimum-data guard (pipeline Step 1 / issue #179)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table

from agents.analytics.agent import MINIMUM_NEW_RECORDS, AnalyticsAgent, check_minimum_data
from agents.common.event_envelope import EventEnvelope


def _minimal_job_postings_table() -> Table:
    md = MetaData(schema="dbo")
    return Table(
        "job_postings",
        md,
        Column("job_posting_id", Integer, primary_key=True),
        Column("created_at", DateTime(timezone=True)),
        Column("spam_tier", String),
        schema="dbo",
    )


def test_check_minimum_data_false_and_exact_log_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANALYTICS_DISABLE_MINIMUM_DATA_GUARD", raising=False)
    jp = _minimal_job_postings_table()
    session = MagicMock()
    session.get_bind.return_value = object()
    result = MagicMock()
    result.scalar_one.return_value = 12
    session.execute.return_value = result

    with patch("agents.analytics.agent._job_postings_table_for_guard", return_value=jp), patch(
        "agents.analytics.agent.log"
    ) as log_mock:
        ok = check_minimum_data(session, datetime(2025, 1, 1, tzinfo=timezone.utc))

    assert ok is False
    log_mock.info.assert_called_once()
    assert log_mock.info.call_args[0][0] == "analytics_minimum_data_guard_skip"
    expected = (
        f"Minimum data guard: 12 new records (threshold: {MINIMUM_NEW_RECORDS}). "
        "Skipping pipeline run — deliberate, not an error."
    )
    assert log_mock.info.call_args[1]["message"] == expected


def test_check_minimum_data_true_when_count_met() -> None:
    jp = _minimal_job_postings_table()
    session = MagicMock()
    session.get_bind.return_value = object()
    result = MagicMock()
    result.scalar_one.return_value = 50
    session.execute.return_value = result

    with patch("agents.analytics.agent._job_postings_table_for_guard", return_value=jp):
        assert check_minimum_data(session, datetime(2025, 1, 1, tzinfo=timezone.utc)) is True


def test_run_pipeline_returns_none_without_emit_when_guard_fails() -> None:
    event = EventEnvelope(correlation_id="c1", agent_id="upstream", payload={})
    agent = AnalyticsAgent()
    agent.health_check()
    session = MagicMock()
    with patch("agents.analytics.agent.check_minimum_data", return_value=False):
        out = agent.run_pipeline(session, None, event)
    assert out is None
