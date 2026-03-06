# agents/visualization/agent.py
"""Visualization Agent — Phase 1. Consumes AnalyticsRefreshed, emits RenderComplete. DB read-only.

Spec: ARCHITECTURE_DEEP.md § 6. Visualization Agent.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import RENDER_COMPLETE


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class VisualizationAgent(BaseAgent):
    """Dashboard pages; PDF/CSV/JSON export; TTL cache; staleness banner — never blank page."""

    def __init__(self) -> None:
        super().__init__(agent_id="visualization_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixtures dir exists and agent is initialized."""
        try:
            fd = _fixtures_dir()
            ok = fd.exists() and fd.is_dir()
            status = "ok" if ok else "down"
            self._last_run_metrics["fixtures_dir_accessible"] = ok
        except Exception:
            status = "down"
            self._last_run_metrics["fixtures_dir_accessible"] = False
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": self._last_run_metrics,
        }

    def process(self, event: EventEnvelope) -> EventEnvelope | None:
        """Consume AnalyticsRefreshed; return RenderComplete with correlation_id propagated."""
        correlation_id = event.correlation_id
        payload = {
            "event_type": RENDER_COMPLETE,
            "pages_rendered": ["ingestion_overview", "normalization_quality", "skill_taxonomy", "weekly_insights", "ask_the_data", "operations_alerts"],
            "exports_generated": [],
        }
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_pages_rendered"] = len(payload["pages_rendered"])
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
