"""
Orchestration Agent stub for the walking skeleton.

This stub provides an explicit orchestration module while keeping Week 2
execution simple and sequential via `run_pipeline()`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class OrchestrationAgent(BaseAgent):
    AGENT_ID = "orchestration"
    """Stub control-plane agent for launching and observing pipeline runs."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        """
        Accept any upstream event and emit a lightweight orchestration audit event.

        In Week 2, this is a stub and not part of the sequential stage chain.
        """
        self._last_run = datetime.now(UTC)
        cid = correlation_id or (event.correlation_id if event else None)
        if not cid:
            log.warning("orchestration_missing_correlation_id")
            return None

        payload = {
            "status": "observed",
            "mode": "sequential_stub",
            "observed_agent_id": event.agent_id if event else None,
            "observed_event_id": event.event_id if event else None,
        }
        ev = create_event(cid, self.agent_id, SCHEMA_VERSION, payload)
        log.debug("orchestration_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id)
        return ev

    def run_once(self, skip_health_check: bool = False) -> list[dict[str, Any]]:
        """Launch one in-process pipeline run and return emitted event dicts."""
        from agents.common.pipeline.runner import run_pipeline

        return run_pipeline(skip_health_check=skip_health_check)

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"mode": "sequential_stub"},
        }
