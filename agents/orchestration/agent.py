# agents/orchestration/agent.py
"""Orchestration Agent — Phase 1. LangGraph StateGraph + APScheduler; sole consumer of *Failed/*Alert.

Spec: ARCHITECTURE_DEEP.md § 7. Orchestration Agent.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class OrchestrationAgent(BaseAgent):
    """Master schedule; trigger pipeline in sequence; retry policies; audit log 100% completeness."""

    def __init__(self) -> None:
        super().__init__(agent_id="orchestration_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if agent is initialized and fixtures dir accessible."""
        try:
            fd = _fixtures_dir()
            ok = fd.exists() and fd.is_dir()
            status = "ok" if ok else "down"
            self._last_run_metrics["fixtures_dir_accessible"] = ok
        except Exception:
            status = "down"
            self._last_run_metrics["fixtures_dir_accessible"] = False
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """Consume inbound (trigger or *Failed/*Alert). Stub: propagate correlation_id and return same event for audit."""
        correlation_id = event.correlation_id
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_event_agent"] = event.agent_id
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "OrchestrationAck",
                "received_from": event.agent_id,
                "original_payload_keys": list(event.payload.keys()) if event.payload else [],
            },
        )
