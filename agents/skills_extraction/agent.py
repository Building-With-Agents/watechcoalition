# agents/skills_extraction/agent.py
"""Skills Extraction Agent — Phase 1. Consumes NormalizationComplete, emits SkillsExtracted.

Spec: ARCHITECTURE_DEEP.md § 3. Skills Extraction Agent.
LLM-dependent stub: returns fixture_skills_extracted.json payload.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import SKILLS_EXTRACTED


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class SkillsExtractionAgent(BaseAgent):
    """LLM inference for skills; taxonomy linking; log all LLM calls to llm_audit_log."""

    def __init__(self) -> None:
        super().__init__(agent_id="skills_extraction_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixture_skills_extracted.json is accessible."""
        fixture = _fixtures_dir() / "fixture_skills_extracted.json"
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
        """Consume NormalizationComplete; return SkillsExtracted with fixture payload; correlation_id propagated."""
        correlation_id = event.correlation_id
        payload: dict = {"event_type": SKILLS_EXTRACTED, "batch_id": event.payload.get("batch_id", "stub-batch-001")}
        try:
            fixture = _fixtures_dir() / "fixture_skills_extracted.json"
            if fixture.exists():
                with open(fixture, encoding="utf-8") as f:
                    data = json.load(f)
                payload["records"] = data
                payload["record_count"] = len(data) if isinstance(data, list) else 1
                payload["skills_count"] = sum(
                    len(r.get("skills", [])) for r in (data if isinstance(data, list) else [data])
                )
                payload["avg_confidence"] = 0.85
            else:
                payload["record_count"] = 0
                payload["skills_count"] = 0
                payload["avg_confidence"] = 0.0
        except Exception:
            payload["record_count"] = 0
            payload["skills_count"] = 0
            payload["avg_confidence"] = 0.0
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_skills_count"] = payload.get("skills_count", 0)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
