"""
Demand Analysis Agent — Phase 2 only. Consumes RecordEnriched, would emit DemandSignalsUpdated.
Walking skeleton: process() returns None.
"""
from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

# Phase 2: no fixture; health can check for scaffold
AGENT_ID = "demand_analysis"


class DemandAnalysisAgent(BaseAgent):
    """Phase 2 agent: time series and forecasting; stub returns None from process()."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Return healthy so pipeline does not abort (Phase 2)."""
        return {"status": "healthy", "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> None:
        """Phase 2: not implemented; MUST return None."""
        return None
