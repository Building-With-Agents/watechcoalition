"""
Visualization Agent stub — Week 2 Walking Skeleton.

Real implementation: Week 5.

In the walking skeleton this agent receives an AnalyticsRefreshed event
and emits a RenderComplete event confirming the dashboard would be updated.
No actual rendering happens in the agent itself; the Streamlit dashboard
reads pipeline_run.json directly for the demo.

Agent ID (canonical): visualization-agent
Emits:    RenderComplete
Consumes: AnalyticsRefreshed

Week 5 replaces this stub with:
- Six Streamlit dashboard pages:
    Ingestion Overview | Normalization Quality | Skill Taxonomy Coverage |
    Weekly Insights | Ask the Data | Operations & Alerts
- PDF, CSV, and JSON exports (standard Phase 1 deliverables)
- TTL cache with staleness banner — never a blank page
- Read-only SQLAlchemy DB connection
"""

from __future__ import annotations

from agents.common.base_agent import BaseAgent
from agents.common.event_envelope import EventEnvelope


class VisualizationAgent(BaseAgent):
    """
    Stub for the Visualization Agent.

    Week 2: emits a RenderComplete acknowledgment.
    Week 5: replaces this with real Streamlit rendering and exports.
    """

    def __init__(self) -> None:
        super().__init__(agent_id="visualization-agent")

    def health_check(self) -> dict:
        """Always ready — no external dependencies in stub mode."""
        return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}

    def process(self, event: EventEnvelope) -> EventEnvelope:
        """
        Accept an AnalyticsRefreshed event and emit a RenderComplete event.

        Stub confirms that, in a real implementation, the Streamlit dashboard
        would now be updated with the latest analytics data.  The actual
        Week 2 dashboard reads pipeline_run.json directly rather than being
        triggered by this event.
        """
        return EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id=self.agent_id,
            payload={
                "event_type": "RenderComplete",
                "triggered_by_posting_id": event.payload.get("triggered_by_posting_id"),
                "pages_rendered": [
                    "Pipeline Run Summary",
                    "Record Journey",
                    "Batch Insights",
                ],
                "render_status": "success",
                "export_formats_available": ["pdf", "csv", "json"],
                # Week 5 adds: actual render time, cache TTL, export file paths
                "stub": True,
            },
        )
