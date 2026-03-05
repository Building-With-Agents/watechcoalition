"""Enrichment agent — role/seniority/quality/spam classifiers, company_id resolution (Phase 1 lite)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _load_enriched_fixture() -> dict[int, dict[str, Any]]:
    """Load fixture_enriched.json once; return dict keyed by posting_id."""
    agents_dir = Path(__file__).resolve().parent.parent
    path = agents_dir / "data" / "fixtures" / "fixture_enriched.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["posting_id"]: item for item in data if "posting_id" in item}


_FIXTURE_ENRICHED: dict[int, dict[str, Any]] = _load_enriched_fixture()


class EnrichmentAgent(BaseAgent):
    """
    Consumes SkillsExtracted; classifies role and seniority; computes quality score and spam score;
    resolves company_id (match or placeholder) and sector_id; writes to job_postings only when
    company_id is set. Spam: <0.7 proceed, 0.7–0.9 flag for review, >0.9 auto-reject. Emits RecordEnriched.
    """

    def __init__(self, agent_id: str = "enrichment") -> None:
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

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """
        Build RecordEnriched payload: merge inbound SkillsExtracted with enrichment fields.
        Walking skeleton: use fixture_enriched.json by posting_id; else sensible defaults.
        """
        p = event.payload
        posting_id = p.get("posting_id")
        if posting_id is not None and isinstance(posting_id, str):
            try:
                posting_id = int(posting_id)
            except (ValueError, TypeError):
                posting_id = None

        fixture = _FIXTURE_ENRICHED.get(posting_id) if posting_id is not None else None
        if fixture:
            out_payload = dict(p)
            out_payload["company_id"] = fixture.get("company_id")
            out_payload["sector_id"] = fixture.get("sector_id")
            out_payload["role_classification"] = fixture.get("role_classification")
            out_payload["seniority"] = fixture.get("seniority", p.get("seniority"))
            out_payload["quality_score"] = fixture.get("quality_score", 0.8)
            out_payload["spam_score"] = fixture.get("spam_score", 0.05)
            out_payload["is_spam"] = fixture.get("is_spam", False)
            out_payload["enrichment_status"] = fixture.get("enrichment_status", "success")
        else:
            out_payload = dict(p)
            out_payload["company_id"] = None
            out_payload["sector_id"] = None
            out_payload["role_classification"] = None
            out_payload["seniority"] = p.get("seniority")
            out_payload["quality_score"] = 0.8
            out_payload["spam_score"] = 0.05
            out_payload["is_spam"] = False
            out_payload["enrichment_status"] = "success"

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = EnrichmentAgent(agent_id="enrichment")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
