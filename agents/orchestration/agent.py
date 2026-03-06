"""
Orchestration Agent — consumes all pipeline events; sole consumer of *Failed/*Alert.

Walking skeleton: stub accepts inbound event and returns ack (run_complete) so the
runner has a consistent 8-step chain. No LangGraph, no scheduler in stub.
"""

from __future__ import annotations

from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.datetime_utils import datetime_to_iso_utc
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURES_DIR


class OrchestrationAgent(BaseAgent):
    """Stub: acknowledges completion. Full orchestration (LangGraph, APScheduler) later."""

    def __init__(self) -> None:
        super().__init__(agent_id="orchestration_agent")
        self._last_run_at: datetime | None = None
        self._initialized = True

    def health_check(self) -> dict:
        """Ok only if initialized and agents root (fixtures parent) exists."""
        agents_root = FIXTURES_DIR.parent.parent
        status = "ok" if self._initialized and agents_root.exists() else "down"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": datetime_to_iso_utc(self._last_run_at) if self._last_run_at else None,
            "metrics": {"initialized": self._initialized},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Ack completion. correlation_id from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        payload = {
            "run_complete": True,
            "correlation_id": event.correlation_id,
        }
        return self.create_outbound_event(event, payload)
