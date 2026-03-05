"""
Analytics Agent — stub: returns fixture payload, no aggregates/LLM.

Production: aggregates, salary distributions, weekly insights, analytics_aggregates. See PIPELINE_DESIGN.md.
"""

import json
from datetime import UTC, datetime

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.config import FIXTURE_ANALYTICS_REFRESHED, get_fixture_path
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class AnalyticsAgent(BaseAgent):
    AGENT_ID = "analytics"
    """Stub: reads fixture_analytics_refreshed.json as payload."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        if event is None:
            log.warning("analytics_received_none")
            return None
        self._last_run = datetime.now(UTC)
        path = get_fixture_path("ANALYTICS_FIXTURE_PATH", FIXTURE_ANALYTICS_REFRESHED)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            log.warning("analytics_fixture_read_failed", path=str(path), error_type=type(e).__name__)
            return None
        payload = data if isinstance(data, dict) else {"summary": data}
        ev = create_event(event.correlation_id, self.agent_id, SCHEMA_VERSION, payload)
        log.debug("analytics_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id)
        return ev

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {},
        }
