"""
Skills Extraction Agent — stub (LLM-dependent). Consumes NormalizationComplete, emits SkillsExtracted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _agents_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _fixture_path() -> Path:
    return _agents_root() / "data" / "fixtures" / "fixture_skills_extracted.json"


class SkillsExtractionAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("skills_extraction_agent")
        self._last_run: datetime | None = None

    def health_check(self) -> dict:
        path = _fixture_path()
        status = "down"
        try:
            if path.exists() and path.is_file():
                json.loads(path.read_text(encoding="utf-8"))
                status = "ok"
            else:
                status = "degraded"
        except (OSError, json.JSONDecodeError):
            pass
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"fixture_path": str(path), "fixture_loadable": status == "ok"},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id
        payload_list: list = []
        path = _fixture_path()
        if path.exists():
            try:
                payload_list = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload_list, list):
                    payload_list = [payload_list] if isinstance(payload_list, dict) else []
            except (OSError, json.JSONDecodeError):
                pass
        self._last_run = datetime.now(timezone.utc)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload={"records": payload_list, "batch_id": correlation_id},
        )
