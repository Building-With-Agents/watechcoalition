"""Tests for agent BaseAgent contract: health_check shape and process() correlation_id propagation."""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.analytics.agent import AnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.orchestration.agent import OrchestrationAgent
from agents.demand_analysis.agent import DemandAnalysisAgent


def _envelope(correlation_id: str = "test-correlation-123") -> EventEnvelope:
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="upstream",
        payload={"key": "value"},
    )


@pytest.mark.parametrize(
    "agent_class,agent_id",
    [
        (EnrichmentAgent, "enrichment"),
        (AnalyticsAgent, "analytics"),
        (VisualizationAgent, "visualization"),
        (OrchestrationAgent, "orchestration"),
        (DemandAnalysisAgent, "demand_analysis"),
    ],
)
def test_agent_health_check_shape(agent_class: type, agent_id: str) -> None:
    """health_check() returns dict with status, agent, last_run, metrics."""
    agent = agent_class(agent_id=agent_id)
    result = agent.health_check()
    assert result["status"] == "ok"
    assert result["agent"] == agent_id
    assert "last_run" in result
    assert "metrics" in result
    assert isinstance(result["metrics"], dict)


@pytest.mark.parametrize(
    "agent_class,agent_id",
    [
        (EnrichmentAgent, "enrichment"),
        (AnalyticsAgent, "analytics"),
        (VisualizationAgent, "visualization"),
        (OrchestrationAgent, "orchestration"),
    ],
)
def test_agent_process_returns_envelope_and_propagates_correlation_id(
    agent_class: type, agent_id: str
) -> None:
    """Phase 1 agents return EventEnvelope with same correlation_id and correct agent_id."""
    agent = agent_class(agent_id=agent_id)
    event = _envelope(correlation_id="my-correlation-456")
    out = agent.process(event)
    assert out is not None
    assert out.correlation_id == "my-correlation-456"
    assert out.agent_id == agent_id
    assert isinstance(out.payload, dict)


def test_demand_analysis_process_returns_none() -> None:
    """Demand Analysis (Phase 2 scaffold) process() returns None."""
    agent = DemandAnalysisAgent(agent_id="demand_analysis")
    event = _envelope()
    out = agent.process(event)
    assert out is None


@pytest.mark.parametrize(
    "module_health_check,expected_agent",
    [
        ("enrichment", "enrichment"),
        ("analytics", "analytics"),
        ("visualization", "visualization"),
        ("orchestration", "orchestration"),
        ("demand_analysis", "demand_analysis"),
    ],
)
def test_module_level_health_check(module_health_check: str, expected_agent: str) -> None:
    """Module-level health_check() is backward-compatible and returns expected shape."""
    import importlib
    mod = importlib.import_module(f"agents.{module_health_check}.agent")
    health_check = getattr(mod, "health_check")
    result = health_check()
    assert result["status"] == "ok"
    assert result["agent"] == expected_agent
    assert "last_run" in result
    assert "metrics" in result
