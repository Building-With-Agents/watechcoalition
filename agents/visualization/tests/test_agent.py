# agents/visualization/tests/test_agent.py

import pytest

from agents.visualization.agent import VisualizationAgent


def test_visualization_agent_health_check() -> None:
    agent = VisualizationAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "visualization"
    assert "last_run" in out
    assert "metrics" in out
