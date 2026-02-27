# agents/enrichment/tests/test_agent.py

import pytest

from agents.enrichment.agent import EnrichmentAgent


def test_enrichment_agent_health_check() -> None:
    agent = EnrichmentAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "enrichment"
    assert "last_run" in out
    assert "metrics" in out
