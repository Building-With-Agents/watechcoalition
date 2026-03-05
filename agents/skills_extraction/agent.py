"""Skills extraction agent — taxonomy linking, LLM extraction, raw_skill fallback."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope

# Default skills when fixture has no match (walking skeleton resilience).
_DEFAULT_SKILLS = [
    {"name": "Python", "type": "Technical", "confidence": 0.85},
    {"name": "SQL", "type": "Technical", "confidence": 0.80},
]


def _load_skills_fixture() -> dict[int, dict[str, Any]]:
    """Load fixture_skills_extracted.json once; return dict keyed by posting_id."""
    agents_dir = Path(__file__).resolve().parent.parent
    path = agents_dir / "data" / "fixtures" / "fixture_skills_extracted.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {item["posting_id"]: item for item in data if "posting_id" in item}


_FIXTURE_SKILLS: dict[int, dict[str, Any]] = _load_skills_fixture()


class SkillsExtractionAgent(BaseAgent):
    """
    Consumes NormalizationComplete; adds skills and extraction_status; emits SkillsExtracted.
    Phase 1: LLM extraction, taxonomy linking. Walking skeleton: fixture-backed payload.
    """

    def __init__(self, agent_id: str = "skills_extraction") -> None:
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
        Build SkillsExtracted payload: normalized record + skills + extraction_status.
        Walking skeleton: use fixture_skills_extracted.json by posting_id; else defaults.
        """
        p = event.payload
        posting_id = p.get("posting_id")
        if posting_id is not None and isinstance(posting_id, str):
            try:
                posting_id = int(posting_id)
            except (ValueError, TypeError):
                posting_id = None

        fixture = _FIXTURE_SKILLS.get(posting_id) if posting_id is not None else None
        if fixture:
            skills = list(fixture.get("skills", []))
            extraction_status = fixture.get("extraction_status", "success")
            seniority = fixture.get("seniority")
        else:
            skills = list(_DEFAULT_SKILLS)
            extraction_status = "success"
            seniority = None

        out_payload = dict(p)
        out_payload["skills"] = skills
        out_payload["extraction_status"] = extraction_status
        if seniority is not None:
            out_payload["seniority"] = seniority

        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload=out_payload,
        )


default_agent = SkillsExtractionAgent(agent_id="skills_extraction")


def health_check() -> dict:
    """Return agent health status. Required on every agent. Backward-compatible module-level API."""
    return default_agent.health_check()
