"""Tests for NormalizationAgent — updated for Week 3 implementation."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.normalization.agent import NormalizationAgent


class TestNormalizationAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = NormalizationAgent()
        assert agent.agent_id == "normalization-agent"

    def test_health_check_shape(self) -> None:
        """Health check returns dict with required keys."""
        agent = NormalizationAgent()
        result = agent.health_check()
        assert "status" in result
        assert result["status"] in ("ok", "degraded", "down")
        assert result["agent"] == "normalization-agent"
        assert "metrics" in result

    def test_process_empty_batch(self) -> None:
        """Empty staged_record_ids returns NormalizationComplete with 0 counts."""
        agent = NormalizationAgent()
        event = EventEnvelope(
            correlation_id="test-1",
            agent_id="ingestion-agent",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "test-batch",
                "staged_record_ids": [],
            },
        )
        out = agent.process(event)
        assert out.payload["event_type"] == "NormalizationComplete"
        assert out.agent_id == "normalization-agent"
        assert out.payload["normalized_count"] == 0

    def test_process_preserves_correlation_id(self) -> None:
        """Correlation ID passes through unchanged."""
        agent = NormalizationAgent()
        event = EventEnvelope(
            correlation_id="test-1",
            agent_id="ingestion-agent",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "test-batch",
                "staged_record_ids": [],
            },
        )
        out = agent.process(event)
        assert out.correlation_id == "test-1"
