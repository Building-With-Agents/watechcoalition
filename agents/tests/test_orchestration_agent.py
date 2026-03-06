"""Tests for OrchestrationAgent — Week 2 stub."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.orchestration.agent import OrchestrationAgent


class TestOrchestrationAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = OrchestrationAgent()
        assert agent.agent_id == "orchestration-agent"

    def test_health_check_always_ok(self) -> None:
        """Stateless stub — always returns 'ok'."""
        agent = OrchestrationAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "orchestration-agent"

    def test_process_emits_orchestration_ack(
        self, render_event: EventEnvelope
    ) -> None:
        """Output event_type is OrchestrationAck."""
        agent = OrchestrationAgent()
        out = agent.process(render_event)
        assert out.payload["event_type"] == "OrchestrationAck"
        assert out.agent_id == "orchestration-agent"

    def test_process_acknowledges_upstream_event(
        self, render_event: EventEnvelope
    ) -> None:
        """Output records the upstream event_type it acknowledged."""
        agent = OrchestrationAgent()
        out = agent.process(render_event)
        assert out.payload["acknowledged_event_type"] == "RenderComplete"

    def test_process_preserves_correlation_id(
        self, render_event: EventEnvelope
    ) -> None:
        """Correlation ID passes through unchanged."""
        agent = OrchestrationAgent()
        out = agent.process(render_event)
        assert out.correlation_id == render_event.correlation_id
