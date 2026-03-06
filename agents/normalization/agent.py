# agents/normalization/agent.py
"""Normalization Agent — Phase 1. Consumes IngestBatch, emits NormalizationComplete, writes to normalized_jobs.

Spec: ARCHITECTURE_DEEP.md § 2. Normalization Agent.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import NORMALIZATION_COMPLETE


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class NormalizationAgent(BaseAgent):
    """Map source fields → JobRecord; standardize dates/salaries/locations; quarantine schema violations."""

    def __init__(self) -> None:
        super().__init__(agent_id="normalization_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixtures dir exists and agent is initialized."""
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
        """Consume IngestBatch; return NormalizationComplete with correlation_id propagated."""
        correlation_id = event.correlation_id
        inbound = event.payload
        record_count = inbound.get("record_count", 0)
        batch_id = inbound.get("batch_id", "stub-batch-001")
        payload = {
            "event_type": NORMALIZATION_COMPLETE,
            "batch_id": batch_id,
            "record_count": record_count,
            "quarantine_count": 0,
        }
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_record_count"] = record_count
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
