# agents/ingestion/agent.py
"""Ingestion Agent — Phase 1. Emits IngestBatch. Writes to raw_ingested_jobs.

Spec: ARCHITECTURE_DEEP.md § 1. Ingestion Agent.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import INGEST_BATCH


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class IngestionAgent(BaseAgent):
    """Poll JSearch (httpx) and Crawl4AI; dedup; stage to raw_ingested_jobs; emit IngestBatch."""

    def __init__(self) -> None:
        super().__init__(agent_id="ingestion_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixture (fallback_scrape_sample) is accessible."""
        fixture = _fixtures_dir() / "fallback_scrape_sample.json"
        try:
            if fixture.exists() and fixture.is_file():
                status = "ok"
                self._last_run_metrics["fixture_accessible"] = True
            else:
                status = "down"
                self._last_run_metrics["fixture_accessible"] = False
        except Exception:
            status = "down"
            self._last_run_metrics["fixture_accessible"] = False
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a raw posting payload and emit an IngestBatch event.

        The raw payload is passed through unchanged.  In Week 3 this is
        where source-field normalisation, dedup fingerprinting, and
        provenance tagging happen.
        """
        raw = event.payload

        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_posting_id"] = raw.get("posting_id")

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": INGEST_BATCH,
                "posting_id": raw.get("posting_id"),
                "source": raw.get("source", "web_scrape"),
                "url": raw.get("url"),
                "title": raw.get("title"),
                "company": raw.get("company"),
                "location": raw.get("location"),
                "timestamp": raw.get("timestamp"),
                "raw_text": raw.get("raw_text"),
                "ingestion_run_id": event.correlation_id,
                "ingestion_timestamp": event.timestamp.isoformat(),
                "raw_payload_hash": "stub-hash",  
                "external_id": str(raw.get("posting_id")),
            },
        )
