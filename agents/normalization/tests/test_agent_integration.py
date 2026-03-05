"""Integration tests for the Normalization Agent (require PostgreSQL with tables)."""

from __future__ import annotations

import pytest

from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.event_envelope import EventEnvelope
from agents.normalization.agent import NormalizationAgent

pytestmark = pytest.mark.integration


def _tables_exist() -> bool:
    """Check if required DB tables exist."""
    try:
        with session_scope() as session:
            session.execute(
                __import__("sqlalchemy").text(
                    "SELECT 1 FROM dbo.raw_ingested_jobs LIMIT 1"
                )
            )
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _skip_if_no_db():
    if not check_db_connection():
        pytest.skip("PostgreSQL not available")
    if not _tables_exist():
        pytest.skip("Required tables not created — run migrations first")


class TestNormalizationAgentIntegration:

    def test_health_check_with_db(self) -> None:
        agent = NormalizationAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["db_reachable"] is True

    def test_empty_batch(self) -> None:
        """Empty batch produces NormalizationComplete with 0 counts."""
        agent = NormalizationAgent()
        event = EventEnvelope(
            correlation_id="norm-test-1",
            agent_id="test",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "test-batch",
                "staged_record_ids": [],
            },
        )
        result = agent.process(event)
        assert result.payload["event_type"] == "NormalizationComplete"
        assert result.payload["normalized_count"] == 0

    def test_normalization_complete_event_shape(self) -> None:
        """NormalizationComplete has required fields."""
        agent = NormalizationAgent()
        event = EventEnvelope(
            correlation_id="shape-test",
            agent_id="test",
            payload={
                "event_type": "IngestBatch",
                "batch_id": "test-batch",
                "staged_record_ids": [],
            },
        )
        result = agent.process(event)
        p = result.payload
        assert "batch_id" in p
        assert "normalized_count" in p
        assert "quarantined_count" in p
        assert "normalization_status" in p
