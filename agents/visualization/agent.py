"""
Visualization Agent — consumes AnalyticsRefreshed, emits RenderComplete.
Walking skeleton: no fixture file; extracts posting_id/run_id from inbound, returns single dict as payload (simulated render result).
"""
from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

AGENT_ID = "visualization"


def _get_posting_id(payload: dict) -> int | None:
    """Extract posting_id (integer 1, 2, 3, ...) from inbound envelope; match by id only, not URL."""
    pid = payload.get("posting_id")
    if pid is not None:
        return int(pid)
    record = payload.get("record")
    if isinstance(record, dict):
        pid = record.get("posting_id")
        return int(pid) if pid is not None else None
    records = payload.get("records")
    if isinstance(records, list) and records and isinstance(records[0], dict):
        pid = records[0].get("posting_id")
        return int(pid) if pid is not None else None
    return None


class VisualizationAgent(BaseAgent):
    """Renders dashboards and exports; stub returns single dict built from inbound (no fixture)."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Always healthy for stub (no fixture to check)."""
        return {"status": "healthy", "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Extract posting_id and run_id from inbound; return ONLY a single dict as payload (simulated render result)."""
        posting_id = _get_posting_id(event.payload)
        run_id = event.payload.get("run_id", "")
        payload = {
            "rendered": True,
            "run_id": run_id,
            "posting_id": posting_id,
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
