"""
Demand Analysis Agent — Phase 2 stub only.
Phase 2 — not implemented; process() returns None.
Consumes RecordEnriched; would emit DemandSignalsUpdated. Do not implement in Phase 1.
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class DemandAnalysisAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("demand_analysis_agent")

    def health_check(self) -> dict:
        return {
            "status": "degraded",
            "agent": self.agent_id,
            "last_run": None,
            "metrics": {"phase": "2", "note": "Phase 2 stub — not implemented"},
        }

    def process(self, event: EventEnvelope) -> None:
        # Phase 2 — not implemented; process() returns None.
        return None
