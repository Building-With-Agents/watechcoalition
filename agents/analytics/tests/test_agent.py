# agents/analytics/tests/test_agent.py

import pytest

from agents.analytics.agent import AnalyticsAgent


def test_analytics_agent_health_check() -> None:
    agent = AnalyticsAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "analytics"
    assert "last_run" in out
    assert "metrics" in out
