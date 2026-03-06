"""Tests for NormalizationAgent — Week 2 stub."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.normalization.agent import NormalizationAgent


class TestNormalizationAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = NormalizationAgent()
        assert agent.agent_id == "normalization-agent"

    def test_health_check_always_ok(self) -> None:
        """Stateless stub — always returns 'ok'."""
        agent = NormalizationAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "normalization-agent"

    def test_process_emits_normalization_complete(
        self, ingest_event: EventEnvelope
    ) -> None:
        """Output event_type is NormalizationComplete."""
        agent = NormalizationAgent()
        out = agent.process(ingest_event)
        assert out.payload["event_type"] == "NormalizationComplete"
        assert out.agent_id == "normalization-agent"

    def test_process_preserves_correlation_id(
        self, ingest_event: EventEnvelope
    ) -> None:
        """Correlation ID passes through unchanged."""
        agent = NormalizationAgent()
        out = agent.process(ingest_event)
        assert out.correlation_id == ingest_event.correlation_id

    def test_process_adds_stub_fields(
        self, ingest_event: EventEnvelope
    ) -> None:
        """Stub adds normalized_location, employment_type, and normalization_status."""
        agent = NormalizationAgent()
        out = agent.process(ingest_event)
        p = out.payload
        assert p["normalized_location"] == ingest_event.payload["location"]
        assert p["employment_type"] == "full_time"
        assert p["normalization_status"] == "success"
