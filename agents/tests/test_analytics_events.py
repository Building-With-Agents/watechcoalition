"""Tests for ``build_analytics_refreshed_event``."""

from __future__ import annotations

from datetime import datetime

from agents.analytics.insights.events import build_analytics_refreshed_event
from agents.analytics.insights.freshness import PostingFreshnessResult
from agents.analytics.insights.llm_summary import SummaryResult
from agents.analytics.insights.trajectory import TrajectoryEntry, build_trajectory_map


def _summary(llm: bool) -> SummaryResult:
    return {
        "skill_label": None,
        "sector_label": None,
        "summary_text": "x",
        "is_llm_generated": llm,
        "model_used": "m" if llm else None,
        "generated_at": "2026-01-01T00:00:00Z",
    }


def test_event_type():
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=[],
        trajectory_map={},
        summaries=[],
    )
    assert env.payload["event_type"] == "AnalyticsRefreshed"


def test_freshness_record_count_matches_input():
    fr = [
        PostingFreshnessResult("p1", 1, "fresh", "r"),
        PostingFreshnessResult("p2", 40, "stale", "r"),
    ]
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=fr,
        trajectory_map={},
        summaries=[],
    )
    assert env.payload["freshness_record_count"] == 2


def test_trajectory_map_count_matches_input():
    tm: dict[str, TrajectoryEntry] = build_trajectory_map(
        [
            {
                "label": "Python",
                "current_count": 10,
                "prior_count": 8,
                "confidence": 0.9,
            }
        ]
    )
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=[],
        trajectory_map=tm,
        summaries=[],
    )
    assert env.payload["trajectory_map_count"] == 1


def test_llm_plus_fallback_equals_summaries_generated():
    summaries = [_summary(True), _summary(False), _summary(True)]
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=[],
        trajectory_map={},
        summaries=summaries,
    )
    p = env.payload
    assert p["llm_generated_count"] + p["fallback_count"] == p["summaries_generated_count"]
    assert p["summaries_generated_count"] == 3


def test_refreshed_at_valid_iso8601():
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=[],
        trajectory_map={},
        summaries=[],
    )
    raw = env.payload["refreshed_at"]
    datetime.fromisoformat(raw.replace("Z", "+00:00"))


def test_envelope_correlation_and_agent():
    env = build_analytics_refreshed_event(
        correlation_id="corr-xyz",
        batch_id="b1",
        freshness_results=[],
        trajectory_map={},
        summaries=[],
    )
    assert env.correlation_id == "corr-xyz"
    assert env.agent_id == "analytics-agent"


def test_empty_inputs_all_counts_zero():
    env = build_analytics_refreshed_event(
        correlation_id="c1",
        batch_id="b1",
        freshness_results=[],
        trajectory_map={},
        summaries=[],
    )
    p = env.payload
    assert p["freshness_record_count"] == 0
    assert p["trajectory_map_count"] == 0
    assert p["summaries_generated_count"] == 0
    assert p["llm_generated_count"] == 0
    assert p["fallback_count"] == 0
    assert p["event_type"] == "AnalyticsRefreshed"
