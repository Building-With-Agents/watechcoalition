"""
Visualization Agent — consumes AnalyticsRefreshed, emits RenderComplete.

Walking skeleton: stub returns fixed pages_rendered and exports_generated (no render).
"""

from __future__ import annotations

from datetime import datetime, timezone

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope
from agents.common.paths import FIXTURES_DIR


class VisualizationAgent(BaseAgent):
    """Stub: emits RenderComplete with fixed payload. No Streamlit render in stub."""

    def __init__(self) -> None:
        super().__init__(agent_id="visualization_agent")
        self._last_run_at: datetime | None = None

    def health_check(self) -> dict:
        """Ok only if dashboard app path exists (streamlit_app.py)."""
        agents_root = FIXTURES_DIR.parent.parent
        dashboard_app = agents_root / "dashboard" / "streamlit_app.py"
        status = "ok" if dashboard_app.exists() and dashboard_app.is_file() else "down"
        return {
            "status": status,
            "agent": self.agent_id,
            "last_run": self._last_run_at.isoformat() if self._last_run_at else None,
            "metrics": {"dashboard_path": str(dashboard_app)},
        }

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """Emit RenderComplete. correlation_id from inbound."""
        self._last_run_at = datetime.now(timezone.utc)
        payload = {
            "pages_rendered": 6,
            "exports_generated": ["pdf", "csv", "json"],
        }
        return self.create_outbound_event(event, payload)
