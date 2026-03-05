"""Normalization agent — maps source fields to canonical JobRecord, quarantines violations."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class NormalizationAgent(BaseAgent):
    """
    Consumes IngestBatch; maps to canonical JobRecord; emits NormalizationComplete.
    Phase 1: standardize dates, salaries, locations. Walking skeleton: payload shaping only.
    """

    def __init__(self, agent_id: str = "normalization") -> None:
        super().__init__(agent_id=agent_id)
        self.last_run_at: Optional[datetime] = None
        self.last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return agent readiness: status, agent, last_run, metrics (architecture contract)."""
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self.last_run_at.isoformat() if self.last_run_at else None,
            "metrics": self.last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Build NormalizationComplete payload: normalized single JobRecord.
        Walking skeleton: no quarantine; map raw_text -> description, timestamp -> date_posted (ISO).
        """
        p = event.payload
        date_posted = p.get("timestamp") or p.get("date_posted")
        if date_posted and isinstance(date_posted, str) and "T" in date_posted:
            pass
        elif date_posted:
            try:
                dt = datetime.fromisoformat(date_posted.replace("Z", "+00:00"))
                date_posted = dt.isoformat()
            except (ValueError, TypeError):
                date_posted = p.get("timestamp", "")

        out_payload = {
            "external_id": str(p.get("external_id", p.get("posting_id", ""))),
            "source": p.get("source", ""),
            "title": (p.get("title") or "").strip(),
            "company": (p.get("company") or "").strip(),
            "location": (p.get("location") or "").strip() or None,
            "description": (p.get("raw_text") or p.get("description") or "").strip() or None,
            "date_posted": date_posted,
            "ingestion_run_id": p.get("ingestion_run_id", ""),
            "raw_payload_hash": p.get("raw_payload_hash", ""),
            "posting_id": p.get("posting_id"),
        }
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = NormalizationAgent(agent_id="normalization")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
