"""
Normalization Agent — consumes IngestBatch, emits NormalizationComplete.

Walking skeleton: stub passes through inbound records as normalized (no real mapping).
Payload: batch_id, record_count, quarantine_count, records.
"""

from __future__ import annotations

from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.datetime_utils import datetime_to_iso_utc
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURES_DIR


class NormalizationAgent(BaseAgent):
    """Stub: consumes IngestBatch, returns NormalizationComplete with same records."""

    def __init__(self) -> None:
        super().__init__(agent_id="normalization_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if fixtures dir exists (can read upstream fixture output)."""
        status = "ok" if FIXTURES_DIR.exists() and FIXTURES_DIR.is_dir() else "down"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": datetime_to_iso_utc(self._last_run_at) if self._last_run_at else None,
            "metrics": {"fixtures_dir": str(FIXTURES_DIR)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Pass through payload as normalized. correlation_id propagated from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        payload_in = event.payload
        records = payload_in.get("records", [])
        if not isinstance(records, list):
            records = []
        payload = {
            "batch_id": payload_in.get("batch_id", ""),
            "record_count": len(records),
            "quarantine_count": 0,
            "records": records,
        }
        return self.create_outbound_event(event, payload)
