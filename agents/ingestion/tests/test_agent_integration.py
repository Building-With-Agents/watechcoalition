"""Integration tests for the Ingestion Agent (require PostgreSQL)."""

from __future__ import annotations

import pytest

from agents.common.data_store.database import check_db_connection
from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _skip_if_no_db():
    """Skip integration tests if database is not available."""
    if not check_db_connection():
        pytest.skip("PostgreSQL not available")


class TestIngestionAgentIntegration:
    """Integration tests requiring a live database."""

    def test_health_check_with_db(self) -> None:
        agent = IngestionAgent()
        result = agent.health_check()
        assert result["status"] in ("ok", "degraded")
        assert result["metrics"]["db_connected"] is True

    def test_full_cycle_fixture_fallback(self) -> None:
        """Full ingestion cycle using fixture data."""
        agent = IngestionAgent()
        trigger = EventEnvelope(
            correlation_id="integration-test-1",
            agent_id="test",
            payload={"source": "crawl4ai", "limit": 3},
        )
        result = agent.process(trigger)
        assert result.payload["event_type"] == "IngestBatch"
        assert result.payload["records_staged"] >= 0
        assert result.correlation_id == "integration-test-1"

    def test_ingest_batch_event_shape(self) -> None:
        """IngestBatch event contains all required fields."""
        agent = IngestionAgent()
        trigger = EventEnvelope(
            correlation_id="shape-test",
            agent_id="test",
            payload={"source": "crawl4ai", "limit": 2},
        )
        result = agent.process(trigger)
        p = result.payload
        assert "batch_id" in p
        assert "source" in p
        assert "total_fetched" in p
        assert "duplicates_skipped" in p
        assert "records_staged" in p
        assert "dead_letter_count" in p
        assert "staged_record_ids" in p
