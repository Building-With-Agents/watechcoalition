# agents/skills_extraction/tests/test_agent.py

import pytest

from agents.skills_extraction.agent import SkillsExtractionAgent


def test_skills_extraction_agent_health_check() -> None:
    agent = SkillsExtractionAgent()
    out = agent.health_check()
    assert out["status"] == "ok"
    assert out["agent"] == "skills_extraction"
    assert "last_run" in out
    assert "metrics" in out
