# agents/analytics/agent.py
"""Analytics Agent — Phase 1. Consumes RecordEnriched, emits AnalyticsRefreshed. Exposes POST /analytics/query."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class AnalyticsAgent:
    """Aggregates (skill, role, industry, region, experience, company size); salary distributions; text-to-SQL with guardrails."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "analytics",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, event_payload: dict) -> None:
        """Process RecordEnriched; refresh aggregates; emit AnalyticsRefreshed. TODO: implement."""
        raise NotImplementedError("AnalyticsAgent.run — Phase 1 implementation")
