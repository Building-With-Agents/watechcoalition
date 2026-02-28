"""
Enrichment Agent stub — Week 2 Walking Skeleton.

Real implementation: Phase 1 lite (refined in Week 5+).

In the walking skeleton this agent returns a pre-computed fixture payload
instead of classifying role/seniority and scoring quality via LLM.

Agent ID (canonical): enrichment-agent
Emits:    RecordEnriched
Consumes: SkillsExtracted

Fixture: agents/data/fixtures/fixture_enriched.json

Phase 1 lite replaces this stub with:
- Role classification (Software Engineering, Data Science, ML, etc.)
- Seniority classification (junior / mid / senior / lead)
- Quality score [0-1]: completeness + clarity + AI keyword density + structural coherence
- Spam detection: score < 0.7 -> proceed | 0.7-0.9 -> flag (is_spam=null) | > 0.9 -> reject
- Company resolution: match companies table by name, create placeholder if missing
- Sector mapping: map to industry_sectors table
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_enriched.json"
)


class EnrichmentAgent(BaseAgent):
    """
    Stub for the Enrichment Agent (Phase 1 lite).

    Week 2: returns fixture data indexed by posting_id.
    Week 5+: replaces this with real role/seniority classification,
             quality scoring, spam detection, and company resolution.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="enrichment-agent")
        self._fixture: dict[int, dict] = {}

    def health_check(self) -> dict:
        """Return ok status if the fixture file is present and loadable."""
        if not _FIXTURE_PATH.exists():
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}
        try:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            self._fixture = {r["posting_id"]: r for r in records}
            return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}
        except Exception:
            return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept a SkillsExtracted event and emit a RecordEnriched event
        using the pre-loaded fixture payload for this posting_id.

        Skills from the upstream event are carried forward in the payload.
        """
        if not self._fixture:
            records = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
            self._fixture = {r["posting_id"]: r for r in records}

        posting_id = event.payload.get("posting_id")
        fx = self._fixture.get(posting_id, {})

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "RecordEnriched",
                "posting_id": posting_id,
                "title": fx.get("title"),
                "company": fx.get("company"),
                "company_id": fx.get("company_id"),
                "sector_id": fx.get("sector_id"),
                "role_classification": fx.get("role_classification"),
                "seniority": fx.get("seniority"),
                "quality_score": fx.get("quality_score"),
                "spam_score": fx.get("spam_score"),
                "is_spam": fx.get("is_spam"),
                "enrichment_status": fx.get("enrichment_status", "success"),
                # Carry skills forward from the SkillsExtracted event
                "skills": event.payload.get("skills", []),
            },
        )
