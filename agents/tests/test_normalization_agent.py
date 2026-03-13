"""Tests for NormalizationAgent — agent_id, health_check, mapper integration, NormalizationComplete emission."""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.types.raw_job_record import RawJobRecord
from agents.normalization.agent import NormalizationAgent


@pytest.fixture
def ingest_batch_with_records() -> EventEnvelope:
    """IngestBatch event with records array (JSearch-style)."""
    records = [
        RawJobRecord(
            external_id="j1",
            source="jsearch",
            region_id="el-paso",
            raw_payload_hash="h1",
            title="Software Engineer",
            company="Acme Inc",
            description="Build things.",
        ).model_dump(mode="json"),
        RawJobRecord(
            external_id="j2",
            source="jsearch",
            region_id="el-paso",
            raw_payload_hash="h2",
            title="Data Analyst",
            company="Beta Corp",
            description="Analyze data.",
        ).model_dump(mode="json"),
    ]
    return EventEnvelope(
        correlation_id="corr-123",
        agent_id="ingestion-agent",
        payload={
            "event_type": "IngestBatch",
            "batch_id": "batch-abc",
            "source": "jsearch",
            "region_id": "el-paso",
            "total_fetched": 2,
            "staged_count": 2,
            "dedup_count": 0,
            "error_count": 0,
            "records": records,
        },
    )


class TestNormalizationAgentAgentId:
    """Property-based agent_id."""

    def test_agent_id_is_normalization_agent(self) -> None:
        agent = NormalizationAgent()
        assert agent.agent_id == "normalization-agent"


class TestNormalizationAgentHealthCheck:
    """Health check shape and status."""

    def test_health_check_returns_expected_shape(self) -> None:
        agent = NormalizationAgent()
        result = agent.health_check()
        assert "status" in result
        assert "agent" in result
        assert "last_run" in result
        assert "metrics" in result
        assert result["status"] in ("ok", "degraded", "down")
        assert result["agent"] == "normalization-agent"


class TestNormalizationAgentMapperIntegration:
    """Mapper integration and NormalizationComplete emission."""

    def test_process_ingest_batch_with_records_emits_normalization_complete(
        self,
        ingest_batch_with_records: EventEnvelope,
    ) -> None:
        agent = NormalizationAgent()
        out = agent.process(ingest_batch_with_records)
        assert out is not None
        assert out.agent_id == "normalization-agent"
        assert out.payload.get("event_type") == "NormalizationComplete"
        assert out.payload.get("batch_id") == "batch-abc"
        assert out.payload.get("record_count") == 2
        assert out.payload.get("quarantine_count") == 0
        assert "normalized_records" in out.payload
        assert len(out.payload["normalized_records"]) == 2
        assert out.correlation_id == ingest_batch_with_records.correlation_id

    def test_normalization_complete_payload_conforms_to_catalog(
        self,
        ingest_batch_with_records: EventEnvelope,
    ) -> None:
        agent = NormalizationAgent()
        out = agent.process(ingest_batch_with_records)
        assert out is not None
        p = out.payload
        assert "event_type" in p
        assert "batch_id" in p
        assert "record_count" in p
        assert "quarantine_count" in p

    def test_legacy_ingest_event_emits_normalization_complete(self, ingest_event: EventEnvelope) -> None:
        """Legacy IngestBatch without records array (single-posting shape)."""
        agent = NormalizationAgent()
        out = agent.process(ingest_event)
        assert out is not None
        assert out.payload.get("event_type") == "NormalizationComplete"
        assert out.payload.get("record_count") == 1
        assert out.payload.get("quarantine_count") == 0
        assert out.correlation_id == ingest_event.correlation_id
