"""
Analytics Agent — consumes RecordEnriched, emits AnalyticsRefreshed.

Walking skeleton: stub loads fixture_analytics_refreshed.json (no DB, no LLM).
Payload: run_id, total_postings, top_skills, distributions, aggregate_types, refresh_duration_ms.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURE_ANALYTICS_REFRESHED_PATH


class AnalyticsAgent(BaseAgent):
    """Stub: returns pre-computed aggregates from fixture. No LLM, no DB."""

    def __init__(self) -> None:
        super().__init__(agent_id="analytics_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if analytics fixture exists and is valid JSON."""
        status = "down"
        if FIXTURE_ANALYTICS_REFRESHED_PATH.exists():
            try:
                raw = FIXTURE_ANALYTICS_REFRESHED_PATH.read_text(encoding="utf-8")
                json.loads(raw)
                status = "ok"
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": {"fixture_path": str(FIXTURE_ANALYTICS_REFRESHED_PATH)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Load fixture and emit AnalyticsRefreshed. correlation_id from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        raw = FIXTURE_ANALYTICS_REFRESHED_PATH.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            data = {}
        payload = {
            **data,
            "aggregate_types": ["skills", "seniority", "role", "locations", "sectors", "skill_type"],
            "record_count": data.get("total_postings", 0),
            "refresh_duration_ms": 0,
        }
        return self.create_outbound_event(event, payload)
