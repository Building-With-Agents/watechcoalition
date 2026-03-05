"""
Skills Extraction Agent — consumes NormalizationComplete, emits SkillsExtracted.

Walking skeleton: stub loads fixture_skills_extracted.json (no LLM).
Payload: batch_id, record_count, skills_count, avg_confidence, records.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURE_SKILLS_EXTRACTED_PATH


class SkillsExtractionAgent(BaseAgent):
    """Stub: returns pre-computed skills from fixture. No LLM calls."""

    def __init__(self) -> None:
        super().__init__(agent_id="skills_extraction_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if skills fixture exists and is valid JSON."""
        status = "down"
        if FIXTURE_SKILLS_EXTRACTED_PATH.exists():
            try:
                raw = FIXTURE_SKILLS_EXTRACTED_PATH.read_text(encoding="utf-8")
                json.loads(raw)
                status = "ok"
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": {"fixture_path": str(FIXTURE_SKILLS_EXTRACTED_PATH)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture and emit SkillsExtracted. correlation_id from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        raw = FIXTURE_SKILLS_EXTRACTED_PATH.read_text(encoding="utf-8")
        records = json.loads(raw)
        if not isinstance(records, list):
            records = []
        batch_id = event.payload.get("batch_id", "")
        skills_count = 0
        conf_sum = 0.0
        conf_n = 0
        for r in records:
            skills = r.get("skills") or []
            skills_count += len(skills)
            for s in skills:
                c = s.get("confidence")
                if isinstance(c, (int, float)):
                    conf_sum += float(c)
                    conf_n += 1
        avg_confidence = conf_sum / conf_n if conf_n else 0.0
        payload = {
            "batch_id": batch_id,
            "record_count": len(records),
            "skills_count": skills_count,
            "avg_confidence": round(avg_confidence, 4),
            "records": records,
        }
        return self.create_outbound_event(event, payload)
