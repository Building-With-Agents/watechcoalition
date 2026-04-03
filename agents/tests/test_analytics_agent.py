"""Tests for AnalyticsAgent — Week 2 stub."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agents.analytics.agent import AnalyticsAgent
from agents.common.event_envelope import EventEnvelope


class TestAnalyticsAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = AnalyticsAgent()
        assert agent.agent_id == "analytics-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fixture file exists and is valid JSON."""
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = AnalyticsAgent()
        fake_path = Path("/nonexistent/fixture_analytics_refreshed.json")
        with patch("agents.analytics.agent._FIXTURE_PATH", fake_path):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_analytics_refreshed(self, enriched_event: EventEnvelope) -> None:
        """Output event_type is AnalyticsRefreshed."""
        agent = AnalyticsAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(enriched_event)
        assert out.payload["event_type"] == "AnalyticsRefreshed"
        assert out.agent_id == "analytics-agent"

    def test_process_includes_batch_data(self, enriched_event: EventEnvelope) -> None:
        """Output payload contains AnalyticsRefreshed Week 7 count fields."""
        agent = AnalyticsAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(enriched_event)
        p = out.payload
        assert p["event_type"] == "AnalyticsRefreshed"
        assert p["batch_id"] == enriched_event.payload["batch_id"]
        assert "refreshed_at" in p
        assert "freshness_record_count" in p
        assert "trajectory_map_count" in p
        assert "summaries_generated_count" in p
        assert p["triggered_by_batch_id"] == enriched_event.payload["batch_id"]
