# agents/normalization/tests/test_agent.py

import pytest

from agents.normalization.agent import NormalizationAgent


def test_normalization_agent_health_check() -> None:
    agent = NormalizationAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "normalization"
    assert "last_run" in out
    assert "metrics" in out
