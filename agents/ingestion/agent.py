"""
Ingestion Agent — entry point for the pipeline.
Emits IngestBatch. Adds mandatory provenance tags to each raw record.
process() uses only the inbound event payload; it does not read from any file.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

# Used only for health_check(); process() never reads from disk.
FIXTURE_PATH = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "fallback_scrape_sample.json"
AGENT_ID = "ingestion"


def _extract_raw_record(payload: dict) -> dict | None:
    """Get single raw record from inbound payload (record, records[0], or payload itself)."""
    if "record" in payload and isinstance(payload["record"], dict):
        return payload["record"]
    records = payload.get("records")
    if isinstance(records, list) and records:
        return records[0] if isinstance(records[0], dict) else None
    if isinstance(payload, dict) and payload.get("posting_id") is not None:
        return payload
    if isinstance(payload, dict) and (payload.get("source") or payload.get("scraped_url") or payload.get("raw_text")):
        return payload
    return None


class IngestionAgent(BaseAgent):
    """Entry point: accepts raw record, adds provenance tags, emits IngestBatch."""

    def __init__(self) -> None:
        super().__init__(AGENT_ID)

    def health_check(self) -> dict:
        """Return healthy if fixture file exists."""
        status = "healthy" if FIXTURE_PATH.exists() else "unhealthy"
        return {"status": status, "agent": self.agent_id}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Extract raw record, add provenance tags, return EventEnvelope with single record as payload."""
        raw = _extract_raw_record(event.payload)
        if raw is None:
            return EventEnvelope(
                correlation_id=event.correlation_id,
                agent_id=self.agent_id,
                payload=event.payload,
            )
        ingestion_run_id = str(uuid.uuid4())
        ingestion_timestamp = datetime.now(timezone.utc).isoformat()
        source = raw.get("source") or "web_scrape"
        external_id = raw.get("url") or raw.get("scraped_url") or ""
        record_with_provenance = {
            **raw,
            "source": source,
            "external_id": external_id,
            "ingestion_run_id": ingestion_run_id,
            "ingestion_timestamp": ingestion_timestamp,
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=record_with_provenance,
        )
