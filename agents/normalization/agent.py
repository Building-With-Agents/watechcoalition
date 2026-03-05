"""
Normalization Agent — consumes IngestBatch, emits NormalizationComplete.
Walking skeleton: loads fixture, returns ONLY the single record matching posting_id in payload.
"""
from __future__ import annotations

import json
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "fallback_scrape_sample.json"
AGENT_ID = "normalization"


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


class NormalizationAgent(BaseAgent):
    """Maps raw records to canonical shape; stub returns single fixture record by posting_id."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Return healthy if fixture file exists."""
        status = "healthy" if FIXTURE_PATH.exists() else "unhealthy"
        return {"status": status, "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture, find dict where posting_id == inbound posting_id; return ONLY that dict as payload."""
        posting_id = _get_posting_id(event.payload)
        payload: dict = {}
        if FIXTURE_PATH.exists() and posting_id is not None:
            with open(FIXTURE_PATH, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if item.get("posting_id") == posting_id:
                        payload = dict(item)
                        break
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
