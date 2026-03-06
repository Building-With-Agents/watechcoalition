"""Tests for IngestionAgent — Week 2 stub."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent


class TestIngestionAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = IngestionAgent()
        assert agent.agent_id == "ingestion-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fallback scrape fixture file exists."""
        agent = IngestionAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "ingestion-agent"

    def test_health_check_down_when_fixture_missing(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = IngestionAgent()
        fake_path = Path("/nonexistent/path/fallback_scrape_sample.json")
        with patch("agents.ingestion.agent._FALLBACK_SCRAPE", fake_path):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_ingest_batch(
        self, sample_event: EventEnvelope
    ) -> None:
        """Output event_type is IngestBatch."""
        agent = IngestionAgent()
        out = agent.process(sample_event)
        assert out.payload["event_type"] == "IngestBatch"
        assert out.agent_id == "ingestion-agent"

    def test_process_preserves_correlation_id(
        self, sample_event: EventEnvelope
    ) -> None:
        """Correlation ID passes through unchanged."""
        agent = IngestionAgent()
        out = agent.process(sample_event)
        assert out.correlation_id == sample_event.correlation_id
