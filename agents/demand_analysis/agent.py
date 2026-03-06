# agents/demand_analysis/agent.py
"""Demand Analysis Agent — Phase 2 only. Scaffold: no pipeline logic, no DemandSignalsUpdated/DemandAnomaly.

Spec: ARCHITECTURE_DEEP.md § 8. Demand Analysis Agent.
Phase 2: time-series, forecasting, demand signals. Not implemented in Phase 1.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class DemandAnalysisAgent(BaseAgent):
    """Phase 2: time-series, forecasting, demand signals. Stub only — process() returns None."""

    def __init__(self) -> None:
        super().__init__(agent_id="demand_analysis_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if agent is initialized (Phase 2 stub)."""
        try:
            fd = _fixtures_dir()
            ok = fd.exists() and fd.is_dir()
            status = "ok" if ok else "down"
            self._last_run_metrics["phase"] = "Phase 2 stub"
            self._last_run_metrics["fixtures_dir_accessible"] = ok
        except Exception:
            status = "down"
            self._last_run_metrics["phase"] = "Phase 2 stub"
            self._last_run_metrics["fixtures_dir_accessible"] = False
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """Phase 2 stub: not implemented. Returns None."""
        return None
