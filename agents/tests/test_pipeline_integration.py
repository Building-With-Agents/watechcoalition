# agents/tests/test_pipeline_integration.py
"""Integration tests: event flow, health checks. Phase 1 scaffold."""

import pytest

from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.skills_extraction.agent import SkillsExtractionAgent
from agents.enrichment.agent import EnrichmentAgent
from agents.analytics.agent import AnalyticsAgent
from agents.visualization.agent import VisualizationAgent
from agents.orchestration.agent import OrchestrationAgent


@pytest.mark.parametrize(
    "agent_factory",
    [
        lambda: IngestionAgent(),
        lambda: NormalizationAgent(),
        lambda: SkillsExtractionAgent(),
        lambda: EnrichmentAgent(),
        lambda: AnalyticsAgent(),
        lambda: VisualizationAgent(),
        lambda: OrchestrationAgent(),
    ],
)
def test_all_phase1_agents_health_check(agent_factory) -> None:
    agent = agent_factory()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert "agent" in out
    assert "last_run" in out
    assert "metrics" in out
