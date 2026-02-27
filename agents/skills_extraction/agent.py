# agents/skills_extraction/agent.py
"""Skills Extraction Agent — Phase 1. Consumes NormalizationComplete, emits SkillsExtracted."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class SkillsExtractionAgent:
    """LLM inference for skills; taxonomy linking; log all LLM calls to llm_audit_log."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "skills_extraction",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, event_payload: dict) -> None:
        """Process NormalizationComplete; emit SkillsExtracted. TODO: implement."""
        raise NotImplementedError("SkillsExtractionAgent.run — Phase 1 implementation")
