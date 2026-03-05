"""
Demand Analysis Agent — Phase 2 only. Consumes RecordEnriched, would emit DemandSignalsUpdated.

Walking skeleton: stub only. process() returns None so the pipeline runner logs
Phase2Skipped and continues. Do not implement in Phase 1.
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class DemandAnalysisAgent(BaseAgent):
    """Phase 2 stub. process() returns None; pipeline runner handles gracefully."""

    def __init__(self) -> None:
        super().__init__(agent_id="demand_analysis_agent")

    def health_check(self) -> dict:
        """Degraded: Phase 2 not implemented. Runner does not abort on non-ok for Phase 2."""
        return {
            "status": "degraded",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {"phase": "2", "message": "Phase 2 not implemented"},
        }

    def process(self, event: EventEnvelope) -> None:
        """Phase 2: not implemented. Return None so runner logs Phase2Skipped."""
        return None
