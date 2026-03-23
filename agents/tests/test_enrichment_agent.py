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
        with patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}):
            with patch("agents.enrichment.agent.resolve_sector", return_value=None):
                out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"

    def test_process_passes_skills_into_enrich_record(
        self, skills_event: EventEnvelope
    ) -> None:
        """Skills from the upstream event are passed on the posting dict to enrich_record."""
        captured: dict = {}

        def capture_enrich(posting: dict, session: object) -> dict:
            captured["skills"] = posting.get("skills")
            return {"enriched": True}

        agent = EnrichmentAgent()
        with patch.object(EnrichmentAgent, "enrich_record", side_effect=capture_enrich):
            with patch("agents.enrichment.agent.resolve_sector", return_value=None):
                agent.process(skills_event)
        assert captured.get("skills") == skills_event.payload["skills"]
