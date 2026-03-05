"""
Orchestration Agent — schedules pipeline, consumes *Failed/*Alert; emits triggers.
Walking skeleton: pass-through; returns EventEnvelope with same correlation_id.
"""
from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

AGENT_ID = "orchestration"


class OrchestrationAgent(BaseAgent):
    """Schedules and monitors pipeline; stub passes through with same correlation_id."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Always healthy for stub."""
        return {"status": "healthy", "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Pass through: same correlation_id and payload."""
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=event.payload,
        )
