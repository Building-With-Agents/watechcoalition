"""Analytics Agent — ``AnalyticsRefreshed`` :class:`EventEnvelope` builder."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agents.analytics.insights.freshness import PostingFreshnessResult
from agents.analytics.insights.llm_summary import SummaryResult
from agents.analytics.insights.trajectory import TrajectoryEntry
from agents.common.event_envelope import EventEnvelope

_ANALYTICS_AGENT_ID = "analytics-agent"


def _refreshed_at_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_analytics_refreshed_event(
    correlation_id: str,
    batch_id: str,
    freshness_results: list[PostingFreshnessResult],
    trajectory_map: dict[str, TrajectoryEntry],
    summaries: list[SummaryResult],
) -> EventEnvelope:
    """Build the canonical ``AnalyticsRefreshed`` envelope for downstream agents."""
    llm_generated_count = sum(1 for s in summaries if s.get("is_llm_generated"))
    fallback_count = len(summaries) - llm_generated_count
    payload: dict[str, Any] = {
        "event_type": "AnalyticsRefreshed",
        "batch_id": batch_id,
        "triggered_by_batch_id": batch_id,
        "refreshed_at": _refreshed_at_iso(),
        "freshness_record_count": len(freshness_results),
        "trajectory_map_count": len(trajectory_map),
        "summaries_generated_count": len(summaries),
        "llm_generated_count": llm_generated_count,
        "fallback_count": fallback_count,
    }
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id=_ANALYTICS_AGENT_ID,
        payload=payload,
    )
