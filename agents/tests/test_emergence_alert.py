"""Tests for EmergenceAlert payload builder."""

from __future__ import annotations

import pytest

from agents.analytics.clustering.types import EmergenceCandidate, RankedSkill, RankedTool
from agents.common.events.emergence_alert import (
    build_emergence_alert_envelope,
    build_emergence_alert_payload,
)
from agents.common.events.typed_events import EmergenceAlertEvent


def test_build_emergence_alert_maps_nearest_cluster_to_role_id() -> None:
    cand = EmergenceCandidate(
        candidate_id="ec-1",
        posting_ids=["p1", "p2"],
        posting_count=2,
        candidate_role_label="Emerging title",
        top_skills=[RankedSkill(skill_name="Python", count=2)],
        top_tools=[RankedTool(tool_name="Docker", count=1)],
        nearest_cluster_id="cluster-0001",
        filter_reason="quality_and_novelty",
    )
    payload = build_emergence_alert_payload(
        cand,
        correlation_id="corr-1",
        cluster_id_to_role_id={"cluster-0001": "550e8400-e29b-41d4-a716-446655440000"},
    )
    assert payload["event_type"] == "EmergenceAlert"
    assert payload["correlation_id"] == "corr-1"
    assert payload["posting_count"] == 2
    assert payload["nearest_canonical_role"] == "550e8400-e29b-41d4-a716-446655440000"
    assert payload["top_skills"] == [{"skill_name": "Python", "count": 2}]
    assert payload["top_tools"] == [{"tool_name": "Docker", "count": 1}]


def test_emergence_alert_event_wrapper() -> None:
    cand = EmergenceCandidate(
        candidate_id="ec-2",
        posting_ids=["p1"],
        posting_count=1,
        candidate_role_label=None,
        top_skills=[],
        top_tools=[],
        nearest_cluster_id=None,
        filter_reason=None,
    )
    env = build_emergence_alert_envelope(
        cand,
        correlation_id="corr-2",
        cluster_id_to_role_id={},
    )
    wrapped = EmergenceAlertEvent(envelope=env)
    assert wrapped.correlation_id == "corr-2"
    assert wrapped.envelope.payload["candidate_role_label"] == "emergence_candidate"


def test_emergence_alert_event_rejects_wrong_type() -> None:
    from agents.common.event_envelope import EventEnvelope

    bad = EventEnvelope(
        correlation_id="x",
        agent_id="analytics-agent",
        payload={"event_type": "AnalyticsRefreshed"},
    )
    with pytest.raises(ValueError, match="EmergenceAlert"):
        EmergenceAlertEvent(envelope=bad)
