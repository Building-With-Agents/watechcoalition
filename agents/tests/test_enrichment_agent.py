"""Tests for EnrichmentAgent — Week 2 stub."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent


class TestEnrichmentAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = EnrichmentAgent()
        assert agent.agent_id == "enrichment-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fixture file exists and is valid JSON."""
        agent = EnrichmentAgent()
        result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = EnrichmentAgent()
        fake_path = Path("/nonexistent/fixture_enriched.json")
        with patch("agents.enrichment.agent._FIXTURE_PATH", fake_path):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_record_enriched(
        self, skills_event: EventEnvelope
    ) -> None:
        """Output event_type is RecordEnriched."""
        agent = EnrichmentAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"

    def test_process_carries_skills_forward(
        self, skills_event: EventEnvelope
    ) -> None:
        """Skills from the upstream SkillsExtracted event are preserved in the output."""
        agent = EnrichmentAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(skills_event)
        assert out.payload["skills"] == skills_event.payload["skills"]
