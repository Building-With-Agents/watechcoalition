# agents/ingestion/tests/test_agent.py

import pytest

from agents.ingestion.agent import IngestionAgent


def test_ingestion_agent_health_check() -> None:
    agent = IngestionAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "ingestion"
    assert "last_run" in out
    assert "metrics" in out
