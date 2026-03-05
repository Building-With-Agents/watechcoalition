"""
Demand Analysis Agent stub for Week 2 walking skeleton.

Phase boundary:
- Week 2 / Phase 1: stub only (no forecasting model, no DB writes)
- Future phase: time-series + forecasting + anomaly detection
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import structlog

from agents.common.base_agent import BaseAgent
from agents.common.events.base import SCHEMA_VERSION, AgentEvent, create_event

log = structlog.get_logger()


class DemandAnalysisAgent(BaseAgent):
    AGENT_ID = "demand_analysis"
    """Stub: consumes an upstream event and emits a demand-signals placeholder event."""

    def __init__(self) -> None:
        super().__init__(self.AGENT_ID)
        self._last_run: datetime | None = None

    @staticmethod
    def _estimate_record_count(payload: dict[str, Any]) -> int:
        jobs = payload.get("jobs")
        if isinstance(jobs, list):
            return len(jobs)
        total_postings = payload.get("total_postings")
        if isinstance(total_postings, int) and total_postings >= 0:
            return total_postings
        return 0

    def process(
        self,
        event: AgentEvent | None,
        correlation_id: str | None = None,
    ) -> AgentEvent | None:
        self._last_run = datetime.now(UTC)
        cid = correlation_id or (event.correlation_id if event else None)
        if not cid:
            log.warning("demand_analysis_missing_correlation_id")
            return None

        upstream_payload = event.payload if event else {}
        payload = {
            "status": "stub_only",
            "phase": "phase_1",
            "record_count": self._estimate_record_count(upstream_payload),
            "upstream_agent_id": event.agent_id if event else None,
        }
        ev = create_event(cid, self.agent_id, SCHEMA_VERSION, payload)
        log.debug("demand_analysis_emitted", event_id=ev.event_id, correlation_id=ev.correlation_id)
        return ev

    def health_check(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"mode": "stub_only"},
        }
