"""
Ingestion Agent — pipeline entry point. Emits IngestBatch.

Walking skeleton: stub loads fallback_scrape_sample.json and returns
payload with batch_id, record_count, source, dedup_count, run_id, records.
Correlation_id is taken from the inbound event (runner trigger); never generated here.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FALLBACK_SCRAPE_PATH


class IngestionAgent(BaseAgent):
    """Stub: loads fixture and emits IngestBatch. No LLM, no DB writes."""

    def __init__(self) -> None:
        super().__init__(agent_id="ingestion_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if fallback scrape fixture exists and is readable."""
        status = "ok" if FALLBACK_SCRAPE_PATH.exists() and FALLBACK_SCRAPE_PATH.is_file() else "down"
        try:
            if status == "ok":
                FALLBACK_SCRAPE_PATH.read_text(encoding="utf-8")
        except OSError:
            status = "down"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": {"fixture_path": str(FALLBACK_SCRAPE_PATH)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture and emit IngestBatch. correlation_id from inbound only."""
        self._last_run_at = datetime.now(timezone.utc)
        raw = FALLBACK_SCRAPE_PATH.read_text(encoding="utf-8")
        records = json.loads(raw)
        if not isinstance(records, list):
            records = []
        run_id = str(uuid.uuid4())
        payload = {
            "batch_id": run_id,
            "record_count": len(records),
            "source": "web_scrape",
            "dedup_count": 0,
            "run_id": run_id,
            "records": records,
        }
        return self.create_outbound_event(event, payload)
