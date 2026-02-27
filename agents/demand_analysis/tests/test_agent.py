# agents/demand_analysis/tests/test_agent.py — Phase 2 scaffold: health_check only

import pytest

from agents.demand_analysis.agent import DemandAnalysisAgent


def test_demand_analysis_agent_health_check() -> None:
    agent = DemandAnalysisAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "demand_analysis"


def test_demand_analysis_run_raises() -> None:
    agent = DemandAnalysisAgent()
    with pytest.raises(NotImplementedError, match="Phase 2"):
        agent.run({})
