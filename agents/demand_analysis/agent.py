"""Demand analysis agent — Phase 2 scaffold only. Not implemented."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class DemandAnalysisAgent(BaseAgent):
    """
    Phase 2 only — scaffold. Consumes RecordEnriched; would do time-series indexing by skill, role,
    industry, region; velocity windows (7d, 30d, 90d); emerging/declining skills; supply/demand gap;
    30-day demand forecasts; emit DemandSignalsUpdated and DemandAnomaly on spikes/cliffs. Not implemented.
    """

    def __init__(self, agent_id: str = "demand_analysis") -> None:
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
        Intended logic (text only — Phase 2, not implemented):
        1. Would consume RecordEnriched.
        2. Time-series indexing by skill, role, industry, region.
        3. Velocity windows: 7d, 30d, 90d.
        4. Emerging/declining skills; supply/demand gap estimates; 30-day demand forecasts.
        5. Emit DemandSignalsUpdated; on spikes or cliffs emit DemandAnomaly to Orchestrator.
        Phase 1: return None; pipeline runner handles None gracefully.
        """
        return None


default_agent = DemandAnalysisAgent(agent_id="demand_analysis")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
