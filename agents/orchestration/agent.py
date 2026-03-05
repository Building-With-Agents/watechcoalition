"""
Orchestration Agent — stub. Sole consumer of *Failed/*Alert. LangGraph StateGraph + APScheduler (Phase 1).
"""

from __future__ import annotations

from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class OrchestrationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("orchestration_agent")
        self._last_run: datetime | None = None
        self._initialized = True

    def health_check(self) -> dict:
        ok = self._initialized and self.agent_id == "orchestration_agent"
        status = "ok" if ok else "down"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"initialized": self._initialized},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id
        self._last_run = datetime.now(timezone.utc)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload={
                "ack": True,
                "inbound_agent_id": event.agent_id,
                "batch_id": correlation_id,
            },
        )
