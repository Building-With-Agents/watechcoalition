# agents/demand_analysis/agent.py
"""Demand Analysis Agent — Phase 2 only. Scaffold: no pipeline logic, no DemandSignalsUpdated/DemandAnomaly."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class DemandAnalysisAgent:
    """Phase 2: time-series, forecasting, demand signals. Not implemented in Phase 1."""

    def __init__(self) -> None:
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict[str, Any] = {}

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": "demand_analysis",
            "last_run": self._last_run_at.isoformat() if self._last_run_at else "",
            "metrics": self._last_run_metrics,
        }

    def run(self, event_payload: dict) -> None:
        raise NotImplementedError("Demand Analysis is Phase 2 — scaffold only")
