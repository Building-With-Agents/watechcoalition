# agents/analytics/agent.py
"""Analytics Agent — Phase 1. Consumes RecordEnriched, emits AnalyticsRefreshed. Exposes POST /analytics/query.

Spec: ARCHITECTURE_DEEP.md § 5. Analytics Agent.
LLM-dependent stub: returns fixture_analytics_refreshed.json payload.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.events.catalog import ANALYTICS_REFRESHED


def _fixtures_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "fixtures"


class AnalyticsAgent(BaseAgent):
    """Aggregates (skill, role, industry, region, experience, company size); salary distributions; text-to-SQL with guardrails."""

    def __init__(self) -> None:
        super().__init__(agent_id="analytics_agent")
        self._last_run_at: datetime | None = None
        self._last_run_metrics: dict = {}

    def health_check(self) -> dict:
        """Return status dict. ok if fixture_analytics_refreshed.json is accessible."""
        fixture = _fixtures_dir() / "fixture_analytics_refreshed.json"
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
        """Consume RecordEnriched; return AnalyticsRefreshed with fixture payload; correlation_id propagated."""
        correlation_id = event.correlation_id
        payload: dict = {
            "event_type": ANALYTICS_REFRESHED,
            "batch_id": event.payload.get("batch_id", "stub-batch-001"),
        }
        try:
            fixture = _fixtures_dir() / "fixture_analytics_refreshed.json"
            if fixture.exists():
                with open(fixture, encoding="utf-8") as f:
                    data = json.load(f)
                payload.update(data)
                payload["aggregate_types"] = list(data.keys()) if isinstance(data, dict) else []
                payload["record_count"] = data.get("total_postings", 0)
                payload["refresh_duration_ms"] = 0
            else:
                payload["aggregate_types"] = []
                payload["record_count"] = 0
                payload["refresh_duration_ms"] = 0
        except Exception:
            payload["aggregate_types"] = []
            payload["record_count"] = 0
            payload["refresh_duration_ms"] = 0
        self._last_run_at = datetime.utcnow()
        self._last_run_metrics["last_record_count"] = payload.get("record_count", 0)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload=payload,
        )
