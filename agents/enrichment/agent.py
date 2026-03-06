# agents/enrichment/agent.py
"""Enrichment Agent — Phase 1 lite. Consumes SkillsExtracted, emits RecordEnriched, writes to job_postings.

Spec: ARCHITECTURE_DEEP.md § 4. Enrichment Agent.
LLM-dependent stub: returns fixture_enriched.json payload.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import RECORD_ENRICHED


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class EnrichmentAgent(BaseAgent):
    """Classify role/seniority; quality score; spam detection; company_id resolution; sector_id; write only when company_id resolved."""

    def __init__(self) -> None:
        super().__init__(agent_id="enrichment_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixture_enriched.json is accessible."""
        fixture = _fixtures_dir() / "fixture_enriched.json"
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

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """Consume SkillsExtracted; return RecordEnriched with fixture payload; correlation_id propagated."""
        correlation_id = event.correlation_id
        payload: dict = {
            "event_type": RECORD_ENRICHED,
            "batch_id": event.payload.get("batch_id", "stub-batch-001"),
        }
        try:
            fixture = _fixtures_dir() / "fixture_enriched.json"
            if fixture.exists():
                with open(fixture, encoding="utf-8") as f:
                    data = json.load(f)
                payload["records"] = data
                payload["record_count"] = len(data) if isinstance(data, list) else 1
                payload["spam_rejected"] = 0
                payload["flagged_for_review"] = 0
            else:
                payload["record_count"] = 0
                payload["spam_rejected"] = 0
                payload["flagged_for_review"] = 0
        except Exception:
            payload["record_count"] = 0
            payload["spam_rejected"] = 0
            payload["flagged_for_review"] = 0
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_record_count"] = payload.get("record_count", 0)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
