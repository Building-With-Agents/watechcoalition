"""Tests for IngestionAgent — updated for Week 3 batch-oriented implementation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent


class TestIngestionAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = IngestionAgent()
        assert agent.agent_id == "ingestion-agent"

    def test_health_check_shape(self) -> None:
        """Health check returns dict with required keys."""
        agent = IngestionAgent()
        result = agent.health_check()
        assert "status" in result
        assert result["status"] in ("ok", "degraded", "down")
        assert result["agent"] == "ingestion-agent"
        assert "db_reachable" in result

    @patch("agents.ingestion.agent.session_scope")
    @patch("agents.ingestion.agent.check_db_connection", return_value=True)
    @patch("agents.ingestion.agent.deduplicate_batch")
    def test_process_emits_ingest_batch(
        self, mock_dedup, mock_db, mock_session
    ) -> None:
        """Output event_type is IngestBatch."""
        from agents.ingestion.deduplicator import DedupResult

        # Mock dedup to return empty result (no DB needed)
        mock_dedup.return_value = DedupResult(new_records=[], duplicates_skipped=0)

        # Mock session_scope context manager
        mock_ctx = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        agent = IngestionAgent()
        trigger = EventEnvelope(
            correlation_id="test-1",
            agent_id="test",
            payload={"sources": ["crawl4ai_indeed"]},
        )
        out = agent.process(trigger)
        assert out.payload["event_type"] == "IngestBatch"
        assert out.agent_id == "ingestion-agent"

    @patch("agents.ingestion.agent.session_scope")
    @patch("agents.ingestion.agent.check_db_connection", return_value=True)
    @patch("agents.ingestion.agent.deduplicate_batch")
    def test_process_preserves_correlation_id(
        self, mock_dedup, mock_db, mock_session
    ) -> None:
        """Correlation ID passes through unchanged."""
        from agents.ingestion.deduplicator import DedupResult

        mock_dedup.return_value = DedupResult(new_records=[], duplicates_skipped=0)

        mock_ctx = MagicMock()
        mock_session.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        agent = IngestionAgent()
        trigger = EventEnvelope(
            correlation_id="test-1",
            agent_id="test",
            payload={"sources": ["crawl4ai_indeed"]},
        )
        out = agent.process(trigger)
        assert out.correlation_id == "test-1"
