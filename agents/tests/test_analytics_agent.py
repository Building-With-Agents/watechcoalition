"""Tests for AnalyticsAgent — Week 7 clustering + Week 2 fixture fallback."""

from __future__ import annotations

import os
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
        """ok when DB reachable; degraded when only fixture (no DB)."""
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["agent"] == "analytics-agent"
        assert result["status"] in ("ok", "degraded")
        if result["status"] == "degraded":
            assert result["metrics"].get("fixture_available") is True
        else:
            assert result["metrics"].get("db_connected") is True

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist and DB is unavailable."""
        agent = AnalyticsAgent()
        fake_path = Path("/nonexistent/fixture_analytics_refreshed.json")
        with (
            patch("agents.analytics.agent._FIXTURE_PATH", fake_path),
            patch("agents.analytics.agent.check_db_connection", return_value=False),
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": ""}),
        ):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_analytics_refreshed(self, enriched_event: EventEnvelope) -> None:
        """Output event_type is AnalyticsRefreshed."""
        agent = AnalyticsAgent()
        agent.health_check()
        with (
            patch("agents.analytics.agent.check_db_connection", return_value=False),
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": ""}),
        ):
            out = agent.process(enriched_event)
        assert out.payload["event_type"] == "AnalyticsRefreshed"
        assert out.agent_id == "analytics-agent"

    def test_process_includes_batch_data(self, enriched_event: EventEnvelope) -> None:
        """Output payload merges fixture keys with clustering placeholders."""
        agent = AnalyticsAgent()
        agent.health_check()
        with (
            patch("agents.analytics.agent.check_db_connection", return_value=False),
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": ""}),
        ):
            out = agent.process(enriched_event)
        p = out.payload
        assert "top_skills" in p
        assert "seniority_distribution" in p
        assert "run_id" in p
        assert p["triggered_by_batch_id"] == enriched_event.payload["batch_id"]
        assert "canonical_clustering_ran" in p
        assert "clustering_skipped" in p
