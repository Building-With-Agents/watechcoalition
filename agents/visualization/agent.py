"""
Visualization Agent — stub: emits RenderComplete.

Production: Streamlit dashboards, PDF/CSV/JSON export, read-only DB. See PIPELINE_DESIGN.md.
"""

from datetime import UTC, datetime

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class VisualizationAgent(BaseAgent):
    AGENT_ID = "visualization"
    """Stub: emits RenderComplete with run metadata."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        if event is None:
            log.warning("visualization_received_none")
            return None
        self._last_run = datetime.now(UTC)
        payload = {
            "correlation_id": event.correlation_id,
            "event_count": 1,
            "status": "complete",
        }
        ev = create_event(event.correlation_id, self.agent_id, SCHEMA_VERSION, payload)
        log.debug("visualization_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id)
        return ev

    def health_check(self) -> dict:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {},
        }
