"""
Enrichment Agent — consumes SkillsExtracted, emits RecordEnriched.

Walking skeleton: stub loads fixture_enriched.json (no classifiers, no DB).
Payload: batch_id, record_count, spam_rejected, flagged_for_review, records.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.datetime_utils import datetime_to_iso_utc
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURE_ENRICHED_PATH


class EnrichmentAgent(BaseAgent):
    """Stub: returns pre-computed enriched records from fixture. No LLM, no DB."""

    def __init__(self) -> None:
        super().__init__(agent_id="enrichment_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if enriched fixture exists and is valid JSON."""
        status = "down"
        if FIXTURE_ENRICHED_PATH.exists():
            try:
                raw = FIXTURE_ENRICHED_PATH.read_text(encoding="utf-8")
                json.loads(raw)
                status = "ok"
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": datetime_to_iso_utc(self._last_run_at) if self._last_run_at else None,
            "metrics": {"fixture_path": str(FIXTURE_ENRICHED_PATH)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture and emit RecordEnriched. correlation_id from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        raw = FIXTURE_ENRICHED_PATH.read_text(encoding="utf-8")
        records = json.loads(raw)
        if not isinstance(records, list):
            records = []
        batch_id = event.payload.get("batch_id", "")
        payload = {
            "batch_id": batch_id,
            "record_count": len(records),
            "spam_rejected": 0,
            "flagged_for_review": 0,
            "records": records,
        }
        return self.create_outbound_event(event, payload)
