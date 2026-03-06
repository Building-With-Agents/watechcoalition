"""
Ingestion Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 3.

In the walking skeleton this agent receives the raw job posting payload
(loaded from the fallback scrape file by the pipeline runner) and wraps it
in an IngestBatch event, adding stub provenance metadata.

Agent ID (canonical): ingestion-agent
Emits:    IngestBatch
Consumes: (initial pipeline input — raw posting dict as payload)

Week 3 replaces this stub with:
- Real JSearch API ingestion via httpx
- Web scraping via Crawl4AI
- SHA-256 deduplication fingerprint
- Full provenance tagging
"""

from __future__ import annotations

from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

# The fallback scrape file lives alongside the other fixtures.
# health_check() verifies it exists before the pipeline runs.
_FIXTURES_DIR = Path(__file__).parent.parent / "data" / "fixtures"
_FALLBACK_SCRAPE = _FIXTURES_DIR / "fallback_scrape_sample.json"


class IngestionAgent(BaseAgent):
    """
    Stub for the Ingestion Agent.

    Week 2: wraps raw posting data in a typed IngestBatch event envelope.
    Week 3: replaces this with real API + scraping, dedup, and provenance tags.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="ingestion-agent")

    def health_check(self) -> dict:
        """Return ok status if the fallback scrape file is present and readable."""
        if _FALLBACK_SCRAPE.exists():
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a raw posting payload and emit an IngestBatch event.

        The raw payload is passed through unchanged.  In Week 3 this is
        where source-field normalisation, dedup fingerprinting, and
        provenance tagging happen.
        """
        raw = event.payload

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "IngestBatch",
                "posting_id": raw.get("posting_id"),
                "source": raw.get("source", "web_scrape"),
                "url": raw.get("url"),
                "title": raw.get("title"),
                "company": raw.get("company"),
                "location": raw.get("location"),
                "timestamp": raw.get("timestamp"),
                "raw_text": raw.get("raw_text"),
                # Provenance tags — stubs for Week 2; real values set in Week 3
                "ingestion_run_id": event.correlation_id,
                "ingestion_timestamp": event.timestamp.isoformat(),
                "raw_payload_hash": "stub-hash",   # Week 3: sha256(source+id+title+company+date)
                "external_id": str(raw.get("posting_id")),
            },
        )
