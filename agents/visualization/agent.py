"""
Visualization Agent — stub. Consumes AnalyticsRefreshed, emits RenderComplete. Read-only DB.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


def _agents_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _rendered_dir() -> Path:
    return _agents_root() / "data" / "rendered"


class VisualizationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("visualization_agent")
        self._last_run: datetime | None = None

    def health_check(self) -> dict:
        rendered = _rendered_dir()
        if not rendered.exists():
            rendered.mkdir(parents=True, exist_ok=True)
        ok = rendered.exists() and rendered.is_dir()
        status = "ok" if ok else "degraded"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "metrics": {"rendered_dir_exists": ok},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        correlation_id = event.correlation_id
        self._last_run = datetime.now(timezone.utc)
        return EventEnvelope(
            correlation_id=correlation_id,
            agent_id=self.agent_id,
            payload={
                "render_status": "complete",
                "batch_id": correlation_id,
                "artifacts": [],
                "stale": False,
            },
        )
