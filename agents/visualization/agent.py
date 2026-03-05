"""Visualization agent — dashboard renderers, PDF/CSV/JSON exporters."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class VisualizationAgent(BaseAgent):
    """
    Consumes AnalyticsRefreshed; serves Streamlit dashboard (Ingestion Overview, Normalization Quality,
    Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts) and exports (PDF, CSV, JSON).
    Read-only DB; TTL cache with staleness banner. On failure emits RenderFailed/VisualizationDegraded.
    Emits RenderComplete.
    """

    def __init__(self, agent_id: str = "visualization") -> None:
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
        Build RenderComplete payload: pages_rendered, exports_generated, summary.
        Walking skeleton: no actual render; healthy payload only.
        """
        p = event.payload
        out_payload = {
            "pages_rendered": [],
            "exports_generated": [],
            "record_count": p.get("record_count", 1),
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = VisualizationAgent(agent_id="visualization")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
