"""
Tests for the exercise 2.2 walking-skeleton pipeline runner.

Verifies that all eight agent stubs run in sequence, correlation_id is preserved,
and Demand Analysis returns None (Phase2Skipped).
"""

from __future__ import annotations

import uuid

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.demand_analysis.agent import DemandAnalysisAgent
from agents.analytics.agent import AnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.orchestration.agent import OrchestrationAgent


@pytest.fixture
def correlation_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def trigger_event(correlation_id: str) -> EventEnvelope:
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="runner",
        payload={"trigger": "test"},
    )


def test_ingestion_preserves_correlation_id(trigger_event: EventEnvelope, correlation_id: str) -> None:
    agent = IngestionAgent()
    out = agent.process(trigger_event)
    assert out is not None
    assert out.correlation_id == correlation_id
    assert "batch_id" in out.payload and "record_count" in out.payload


def test_normalization_preserves_correlation_id(trigger_event: EventEnvelope, correlation_id: str) -> None:
    ingestion = IngestionAgent()
    norm = NormalizationAgent()
    ingest_out = ingestion.process(trigger_event)
    assert ingest_out is not None
    out = norm.process(ingest_out)
    assert out is not None
    assert out.correlation_id == correlation_id
    assert "records" in out.payload


def test_demand_analysis_returns_none(trigger_event: EventEnvelope) -> None:
    ingestion = IngestionAgent()
    norm = NormalizationAgent()
    skills = SkillsExtractionAgent()
    enrichment = EnrichmentAgent()
    demand = DemandAnalysisAgent()
    ingest_out = ingestion.process(trigger_event)
    norm_out = norm.process(ingest_out)
    skills_out = skills.process(norm_out)
    enrich_out = enrichment.process(skills_out)
    out = demand.process(enrich_out)
    assert out is None


def test_full_stub_chain_preserves_correlation_id(trigger_event: EventEnvelope, correlation_id: str) -> None:
    """Run Ingestion → … → Orchestration; Demand Analysis returns None, rest propagate event."""
    event = trigger_event
    agents = [
        IngestionAgent(),
        NormalizationAgent(),
        SkillsExtractionAgent(),
        EnrichmentAgent(),
        DemandAnalysisAgent(),
        AnalyticsAgent(),
        VisualizationAgent(),
        OrchestrationAgent(),
    ]
    for agent in agents:
        if isinstance(agent, DemandAnalysisAgent):
            out = agent.process(event)
            assert out is None
            continue
        out = agent.process(event)
        assert out is not None, f"{agent.agent_id} returned None"
        assert out.correlation_id == correlation_id, f"{agent.agent_id} changed correlation_id"
        event = out
    assert event.payload.get("run_complete") is True


def test_all_agents_health_check_return_dict() -> None:
    agents = [
        IngestionAgent(),
        NormalizationAgent(),
        SkillsExtractionAgent(),
        EnrichmentAgent(),
        DemandAnalysisAgent(),
        AnalyticsAgent(),
        VisualizationAgent(),
        OrchestrationAgent(),
    ]
    for agent in agents:
        h = agent.health_check()
        assert isinstance(h, dict)
        assert "status" in h and "agent" in h
        assert h["agent"] == agent.agent_id
