# agents/normalization/agent.py
"""Normalization Agent — Phase 1. Consumes IngestBatch, emits NormalizationComplete, writes to normalized_jobs."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class NormalizationAgent:
    """Map source fields → JobRecord; standardize dates/salaries/locations; quarantine schema violations."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "normalization",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, event_payload: dict) -> None:
        """Process IngestBatch payload; emit NormalizationComplete. TODO: implement."""
        raise NotImplementedError("NormalizationAgent.run — Phase 1 implementation")
