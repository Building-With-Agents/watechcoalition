"""
Normalization Agent — stub: pass-through and validate envelope.

Production: field mapping, schema validation, quarantine, normalized_jobs. See PIPELINE_DESIGN.md.
"""

from datetime import UTC, datetime

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class NormalizationAgent(BaseAgent):
    AGENT_ID = "normalization"
    """Stub: minimal field pass-through; validates event envelope."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        if event is None:
            log.warning("normalization_received_none")
            return None
        self._last_run = datetime.now(UTC)
        # Pass through payload as "normalized" (stub)
        payload = {"jobs": event.payload.get("jobs", [])}
        ev = create_event(event.correlation_id, self.agent_id, SCHEMA_VERSION, payload)
        log.debug("normalization_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id)
        return ev

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {},
        }
