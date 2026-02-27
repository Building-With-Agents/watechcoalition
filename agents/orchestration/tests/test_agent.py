# agents/orchestration/tests/test_agent.py

import pytest

from agents.orchestration.agent import OrchestrationAgent


def test_orchestration_agent_health_check() -> None:
    agent = OrchestrationAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "orchestration"
    assert "last_run" in out
    assert "metrics" in out
