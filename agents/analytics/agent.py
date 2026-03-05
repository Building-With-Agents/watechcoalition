"""
Analytics Agent — consumes RecordEnriched, emits AnalyticsRefreshed.
Walking skeleton: loads fixture; if array, returns ONLY the single record matching posting_id; else returns fixture object as payload.
"""
from __future__ import annotations

import json
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "fixture_analytics_refreshed.json"
AGENT_ID = "analytics"


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


class AnalyticsAgent(BaseAgent):
    """Aggregates and weekly insights; stub loads fixture and returns single matched dict or full object as payload."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Return healthy if fixture file exists."""
        status = "healthy" if FIXTURE_PATH.exists() else "unhealthy"
        return {"status": status, "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture; if array, find dict where posting_id == inbound posting_id; return ONLY that dict. Else return whole fixture as payload."""
        posting_id = _get_posting_id(event.payload)
        payload: dict = {}
        if FIXTURE_PATH.exists():
            with open(FIXTURE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if item.get("posting_id") == posting_id:
                        payload = dict(item)
                        break
            elif isinstance(data, dict):
                payload = dict(data)
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
