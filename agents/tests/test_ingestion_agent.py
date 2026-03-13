"""Tests for IngestionAgent — agent_id, health_check, JSearch adapter integration, IngestBatch emission."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.types.raw_job_record import RawJobRecord
from agents.ingestion.agent import IngestionAgent
from agents.ingestion.events import ingest_batch_payload


@pytest.fixture
def minimal_region_config() -> dict:
    """Minimal RegionConfig-compatible dict for tests."""
    return {
        "region_id": "el-paso",
        "display_name": "El Paso",
        "query_location": "El Paso, TX",
        "radius_miles": 50,
        "states": ["TX"],
        "countries": ["US"],
        "sources": ["jsearch"],
        "role_categories": ["Technology"],
        "keywords": ["software"],
    }


@pytest.fixture
def sample_raw_job_records() -> list[RawJobRecord]:
    """Two RawJobRecords as if returned by JSearch adapter."""
    return [
        RawJobRecord(
            external_id="j1",
            source="jsearch",
            region_id="el-paso",
            raw_payload_hash="hash1",
            title="Software Engineer",
            company="Acme Inc",
            description="Build things.",
        ),
        RawJobRecord(
            external_id="j2",
            source="jsearch",
            region_id="el-paso",
            raw_payload_hash="hash2",
            title="Data Analyst",
            company="Beta Corp",
            description="Analyze data.",
        ),
    ]


class TestIngestionAgentAgentId:
    """Property-based agent_id."""

    def test_agent_id_is_ingestion_agent(self) -> None:
        agent = IngestionAgent()
        assert agent.agent_id == "ingestion-agent"


class TestIngestionAgentHealthCheck:
    """Health check shape and status."""

    def test_health_check_returns_expected_shape(self) -> None:
        agent = IngestionAgent()
        result = agent.health_check()
        assert "status" in result
        assert "agent" in result
        assert "last_run" in result
        assert "metrics" in result
        assert result["status"] in ("ok", "degraded", "down")
        assert result["agent"] == "ingestion-agent"


class TestIngestionAgentSourceAdapterIntegration:
    """JSearch adapter integration with mocked fetch."""

    def test_process_with_region_config_emits_ingest_batch(
        self,
        minimal_region_config: dict,
        sample_raw_job_records: list[RawJobRecord],
    ) -> None:
        agent = IngestionAgent()
        event = EventEnvelope(
            correlation_id="corr-123",
            agent_id="trigger",
            payload={"region_config": minimal_region_config, "source": "jsearch"},
        )
        with patch.object(
            agent._jsearch,
            "fetch",
            new_callable=AsyncMock,
            return_value=sample_raw_job_records,
        ):
            out = agent.process(event)
        assert out is not None
        assert isinstance(out, EventEnvelope)
        assert out.agent_id == "ingestion-agent"
        assert out.payload.get("event_type") == "IngestBatch"
        assert out.payload.get("batch_id")
        assert out.payload.get("source") == "jsearch"
        assert out.payload.get("region_id") == "el-paso"
        assert out.payload.get("total_fetched") == 2
        assert out.payload.get("staged_count") == 2
        assert out.payload.get("dedup_count") == 0
        assert out.payload.get("error_count") == 0
        assert "records" in out.payload
        assert len(out.payload["records"]) == 2

    def test_ingest_batch_payload_keys_match_contract(
        self,
        minimal_region_config: dict,
        sample_raw_job_records: list[RawJobRecord],
    ) -> None:
        agent = IngestionAgent()
        event = EventEnvelope(
            correlation_id="corr-456",
            agent_id="trigger",
            payload={"region_config": minimal_region_config},
        )
        with patch.object(
            agent._jsearch,
            "fetch",
            new_callable=AsyncMock,
            return_value=sample_raw_job_records,
        ):
            out = agent.process(event)
        assert out is not None
        expected_keys = set(ingest_batch_payload(
            batch_id="x", source="jsearch", region_id="r",
            total_fetched=0, staged_count=0, dedup_count=0, error_count=0,
        ).keys())
        assert expected_keys <= set(out.payload.keys())
        assert out.correlation_id == "corr-456"

    def test_source_failure_emits_failure_event(self, minimal_region_config: dict) -> None:
        agent = IngestionAgent()
        event = EventEnvelope(
            correlation_id="corr-789",
            agent_id="trigger",
            payload={"region_config": minimal_region_config, "source": "jsearch"},
        )
        with patch.object(
            agent._jsearch,
            "fetch",
            new_callable=AsyncMock,
            side_effect=Exception("Connection refused"),
        ):
            out = agent.process(event)
        assert out is not None
        assert out.payload.get("event_type") == "SourceFailure"
        assert out.payload.get("source") == "jsearch"
        assert "error" in out.payload


class TestIngestionAgentLegacySinglePosting:
    """Legacy path: single raw posting without region_config."""

    def test_legacy_single_posting_emits_ingest_batch_with_one_record(self, sample_event: EventEnvelope) -> None:
        agent = IngestionAgent()
        out = agent.process(sample_event)
        assert out is not None
        assert out.payload.get("event_type") == "IngestBatch"
        assert out.payload.get("total_fetched") == 1
        assert out.payload.get("staged_count") == 1
        assert "records" in out.payload
        assert len(out.payload["records"]) == 1
        assert out.correlation_id == sample_event.correlation_id
