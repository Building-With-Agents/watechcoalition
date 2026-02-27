# agents/enrichment/agent.py
"""Enrichment Agent — Phase 1 lite. Consumes SkillsExtracted, emits RecordEnriched, writes to job_postings."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class EnrichmentAgent:
    """Classify role/seniority; quality score; spam detection; company_id resolution; sector_id; write only when company_id resolved."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "enrichment",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, event_payload: dict) -> None:
        """Process SkillsExtracted; emit RecordEnriched; write to job_postings. TODO: implement."""
        raise NotImplementedError("EnrichmentAgent.run — Phase 1 implementation")
