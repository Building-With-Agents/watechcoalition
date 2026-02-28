"""Tests for DemandAnalysisAgent — Phase 2 stub."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.demand_analysis.agent import DemandAnalysisAgent


class TestDemandAnalysisAgent:
    """Verify Phase 2 stub behaviour: always down, always returns None."""

    def test_agent_id(self) -> None:
        agent = DemandAnalysisAgent()
        assert agent.agent_id == "demand-analysis-agent"

    def test_health_check_always_down(self) -> None:
        """Phase 2 agent — health check always reports 'down'."""
        agent = DemandAnalysisAgent()
        result = agent.health_check()
        assert result["status"] == "down"
        assert result["agent"] == "demand-analysis-agent"

    def test_process_returns_none(self, enriched_event: EventEnvelope) -> None:
        """Phase 2 stub — process() returns None (no event emitted)."""
        agent = DemandAnalysisAgent()
        result = agent.process(enriched_event)
        assert result is None

    def test_process_does_not_raise(self, enriched_event: EventEnvelope) -> None:
        """process() completes without raising any exception."""
        agent = DemandAnalysisAgent()
        # Should not raise — if it does, the test fails automatically.
        agent.process(enriched_event)
