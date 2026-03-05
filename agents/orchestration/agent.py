"""Orchestration agent — scheduler, retries, sole consumer of *Failed/*Alert events."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class OrchestrationAgent(BaseAgent):
    """
    Consumes all events (IngestBatch, NormalizationComplete, SkillsExtracted, RecordEnriched,
    AnalyticsRefreshed, RenderComplete, and all *Failed/*Alert/SourceFailure). Runs pipeline on
    schedule (APScheduler); LangGraph StateGraph for routing; retry policies (exponential back-off + jitter);
    maintains audit log with 100% completeness; monitors system health. Emits triggers and retry signals
    only (no domain payload events).
    """

    def __init__(self, agent_id: str = "orchestration") -> None:
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
        Consume any event; emit ack only (no domain payload).
        """
        out_payload = {
            "received": True,
            "correlation_id": event.correlation_id,
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = OrchestrationAgent(agent_id="orchestration")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
