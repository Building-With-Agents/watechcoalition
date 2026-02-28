"""Tests for SkillsExtractionAgent — Week 2 stub."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agents.common.event_envelope import EventEnvelope
from agents.skills_extraction.agent import SkillsExtractionAgent


class TestSkillsExtractionAgent:
    """Verify agent_id, health_check (incl. failure modes), and process behaviour."""

    def test_agent_id(self) -> None:
        agent = SkillsExtractionAgent()
        assert agent.agent_id == "skills-extraction-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fixture file exists and is valid JSON."""
        agent = SkillsExtractionAgent()
        result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = SkillsExtractionAgent()
        fake_path = Path("/nonexistent/fixture_skills_extracted.json")
        with patch("agents.skills_extraction.agent._FIXTURE_PATH", fake_path):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_health_check_down_bad_json(self, tmp_path: Path) -> None:
        """Returns 'down' when the fixture file contains invalid JSON."""
        bad_file = tmp_path / "fixture_skills_extracted.json"
        bad_file.write_text("NOT VALID JSON {{{", encoding="utf-8")
        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent._FIXTURE_PATH", bad_file):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_skills_extracted(
        self, normalization_event: EventEnvelope
    ) -> None:
        """Output event_type is SkillsExtracted."""
        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(normalization_event)
        assert out.payload["event_type"] == "SkillsExtracted"
        assert out.agent_id == "skills-extraction-agent"

    def test_process_returns_fixture_skills(
        self, normalization_event: EventEnvelope
    ) -> None:
        """Output contains a non-empty skills list with expected keys."""
        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(normalization_event)
        skills = out.payload["skills"]
        assert isinstance(skills, list)
        assert len(skills) > 0
        for skill in skills:
            assert "name" in skill
            assert "type" in skill
            assert "confidence" in skill
