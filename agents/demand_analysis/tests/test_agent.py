# agents/demand_analysis/tests/test_agent.py — Phase 2 scaffold: health_check only; process() returns None

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.demand_analysis.agent import DemandAnalysisAgent


def test_demand_analysis_agent_health_check() -> None:
    agent = DemandAnalysisAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "demand_analysis_agent"
    assert "last_run" in out
    assert "metrics" in out


def test_demand_analysis_process_returns_none_phase2_stub() -> None:
    """Phase 2 stub: process() returns None."""
    agent = DemandAnalysisAgent()
    event = EventEnvelope(correlation_id="c1", agent_id="enrichment_agent", payload={})
    out = agent.process(event)
    assert out is None
