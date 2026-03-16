"""Tests for VisualizationAgent — Week 2 stub."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.visualization.agent import VisualizationAgent


class TestVisualizationAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = VisualizationAgent()
        assert agent.agent_id == "visualization-agent"

    def test_health_check_always_ok(self) -> None:
        """Stateless stub — always returns 'ok'."""
        agent = VisualizationAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "visualization-agent"

    def test_process_emits_render_complete(
        self, analytics_event: EventEnvelope
    ) -> None:
        """Output event_type is RenderComplete."""
        agent = VisualizationAgent()
        out = agent.process(analytics_event)
        assert out.payload["event_type"] == "RenderComplete"
        assert out.agent_id == "visualization-agent"

    def test_process_payload_shape(
        self, analytics_event: EventEnvelope
    ) -> None:
        """Output has expected stub fields: pages, render_status, export_formats."""
        agent = VisualizationAgent()
        out = agent.process(analytics_event)
        p = out.payload
        assert len(p["pages_rendered"]) == 3
        assert p["render_status"] == "success"
        assert "pdf" in p["export_formats_available"]
        assert "csv" in p["export_formats_available"]
        assert "json" in p["export_formats_available"]
