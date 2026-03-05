"""Analytics agent — aggregates, text-to-SQL guardrails, weekly insights."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class AnalyticsAgent(BaseAgent):
    """
    Consumes RecordEnriched; builds aggregates by skill, role, industry, region, experience level,
    company size; salary distributions (median, p25/p75/p95); co-occurrence matrices; posting
    lifecycle metrics; weekly LLM summaries with template fallback; text-to-SQL with guardrails.
    Exposes POST /analytics/query. Emits AnalyticsRefreshed.
    """

    def __init__(self, agent_id: str = "analytics") -> None:
        super().__init__(agent_id=agent_id)
        self.last_run_at: Optional[datetime] = None
        self.last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return agent readiness: status, agent, last_run, metrics (architecture contract)."""
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self.last_run_at.isoformat() if self.last_run_at else None,
            "metrics": self.last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        Build AnalyticsRefreshed payload: minimal summary for single-record flow.
        Walking skeleton: record_count, aggregate_types, optional enriched_record.
        """
        p = event.payload
        out_payload = {
            "record_count": 1,
            "aggregate_types": [],
            "enriched_record": dict(p),
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = AnalyticsAgent(agent_id="analytics")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
