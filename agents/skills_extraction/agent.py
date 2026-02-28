"""
Skills Extraction Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 4.

In the walking skeleton this agent returns a pre-computed fixture payload
instead of making an LLM call.  The fixture (fixture_skills_extracted.json)
contains realistic skill extractions for all 10 demo postings, matched to
the actual job descriptions in fallback_scrape_sample.json.

Agent ID (canonical): skills-extraction-agent
Emits:    SkillsExtracted
Consumes: NormalizationComplete

Fixture: agents/data/fixtures/fixture_skills_extracted.json

Week 4 replaces this stub with:
- LLM-based skill extraction via LangChain + Azure OpenAI
- Taxonomy linking against the watechcoalition skills table
- Embedding cosine similarity fallback (>= 0.92 threshold)
- O*NET occupation code fallback
- LLM call logging to llm_audit_log
"""

from __future__ import annotations

import json
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

_FIXTURE_PATH = (
    Path(__file__).parent.parent / "data" / "fixtures" / "fixture_skills_extracted.json"
)


class SkillsExtractionAgent(BaseAgent):
    """
    Stub for the Skills Extraction Agent.

    Week 2: returns fixture data indexed by posting_id instead of calling an LLM.
    Week 4: replaces this with real LLM extraction + taxonomy linking.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="skills-extraction-agent")
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
        Accept a NormalizationComplete event and emit a SkillsExtracted event
        using the pre-loaded fixture payload for this posting_id.
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
                "event_type": "SkillsExtracted",
                "posting_id": posting_id,
                "title": fx.get("title"),
                "company": fx.get("company"),
                "skills": fx.get("skills", []),
                "seniority": fx.get("seniority"),
                "extraction_status": fx.get("extraction_status", "success"),
                # LLM call metadata — stub values; real data logged in Week 4
                "llm_provider": "stub",
                "llm_model": "stub",
                "llm_call_logged": False,
            },
        )
