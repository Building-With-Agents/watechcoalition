"""Tests for AnalyticsAgent — aggregate refresh (Week 7) + clustering + fixture overlay."""

from __future__ import annotations

from unittest.mock import patch

from agents.analytics.agent import AnalyticsAgent, _resolve_target_week, default_analytics_target_week
from agents.common.event_envelope import EventEnvelope


class TestAnalyticsAgent:
    """Verify agent_id, health_check, target week helpers, and process()."""

    def test_agent_id(self) -> None:
        agent = AnalyticsAgent()
        assert agent.agent_id == "analytics-agent"

    @patch("agents.analytics.agent.check_db_connection", return_value=True)
    @patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"})
    def test_health_check_ok_when_db_configured_and_reachable(self, _mock_check: MagicMock) -> None:
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["status"] == "ok"
        assert result["agent"] == "analytics-agent"

    @patch("agents.analytics.agent._db_url_configured", return_value=False)
    def test_health_check_degraded_without_db_url(self, _mock_url: MagicMock) -> None:
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["status"] == "degraded"
        assert "PYTHON_DATABASE_URL" in result["metrics"].get("reason", "")

    @patch("agents.analytics.agent.check_db_connection_detail", return_value=(False, "connection refused"))
    @patch("agents.analytics.agent.check_db_connection", return_value=False)
    @patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"})
    def test_health_check_degraded_when_db_unreachable_but_fixture_exists(
        self, _mock_conn: MagicMock, _mock_detail: MagicMock
    ) -> None:
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["status"] == "degraded"
        assert result["metrics"].get("reason") == "database_unreachable"
        assert result["metrics"].get("fixture_overlay_available") is True

    @patch("agents.analytics.agent._FIXTURE_PATH")
    @patch("agents.analytics.agent.check_db_connection_detail", return_value=(False, "connection refused"))
    @patch("agents.analytics.agent.check_db_connection", return_value=False)
    @patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"})
    def test_health_check_down_when_db_unreachable_and_no_fixture(
        self,
        _mock_conn: MagicMock,
        _mock_detail: MagicMock,
        mock_fixture_path: MagicMock,
    ) -> None:
        mock_fixture_path.exists.return_value = False
        agent = AnalyticsAgent()
        result = agent.health_check()
        assert result["status"] == "down"

    @patch("agents.analytics.agent.refresh_skill_co_occurrence", return_value=9)
    @patch("agents.analytics.agent.refresh_skill_velocity", return_value=8)
    @patch("agents.analytics.agent.refresh_tool_demand_weekly", return_value=3)
    @patch("agents.analytics.agent.refresh_skill_demand_weekly", return_value=2)
    @patch("agents.analytics.agent.session_scope")
    @patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"})
    def test_process_runs_aggregates_in_order_with_row_counts(
        self,
        _mock_scope: MagicMock,
        _mock_r2: MagicMock,
        _mock_r3: MagicMock,
        _mock_r8: MagicMock,
        _mock_r9: MagicMock,
        enriched_event: EventEnvelope,
    ) -> None:
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = MagicMock()
        mock_cm.__exit__.return_value = None
        _mock_scope.return_value = mock_cm

        enriched_event.payload["analytics_target_week"] = "2025-01-06"
        agent = AnalyticsAgent()
        out = agent.process(enriched_event)
        assert out.payload["event_type"] == "AnalyticsRefreshed"
        assert out.agent_id == "analytics-agent"
        ar = out.payload["aggregate_refresh"]
        assert ar["target_week"] == "2025-01-06"
        assert ar["skill_demand_weekly_rows"] == 2
        assert ar["tool_demand_weekly_rows"] == 3
        assert ar["skill_velocity_rows"] == 8
        assert ar["skill_co_occurrence_rows"] == 9
        assert _mock_r2.call_count == 1
        assert _mock_r3.call_count == 1
        assert _mock_r8.call_count == 1
        assert _mock_r9.call_count == 1
        assert _mock_scope.call_count == 4

    @patch("agents.analytics.agent.refresh_skill_co_occurrence")
    @patch("agents.analytics.agent.refresh_skill_velocity")
    @patch("agents.analytics.agent.refresh_tool_demand_weekly", return_value=1)
    @patch("agents.analytics.agent.refresh_skill_demand_weekly", side_effect=RuntimeError("step2 failed"))
    @patch("agents.analytics.agent.session_scope")
    @patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"})
    def test_process_skips_steps_8_and_9_when_step_2_fails(
        self,
        _mock_scope: MagicMock,
        _mock_r2: MagicMock,
        _mock_r3: MagicMock,
        _mock_r8: MagicMock,
        _mock_r9: MagicMock,
        enriched_event: EventEnvelope,
    ) -> None:
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value = MagicMock()
        mock_cm.__exit__.return_value = None
        _mock_scope.return_value = mock_cm

        agent = AnalyticsAgent()
        out = agent.process(enriched_event)
        ar = out.payload["aggregate_refresh"]
        assert ar["skill_velocity_skipped"] is True
        assert ar["skill_co_occurrence_skipped"] is True
        assert "skill_demand_weekly_error" in ar
        _mock_r8.assert_not_called()
        _mock_r9.assert_not_called()

    def test_process_skips_db_refresh_without_url(self, enriched_event: EventEnvelope) -> None:
        with (
            patch("agents.analytics.agent._db_url_configured", return_value=False),
            patch("agents.analytics.agent.refresh_skill_demand_weekly") as mock_r2,
            patch("agents.analytics.agent.session_scope") as mock_scope,
        ):
            agent = AnalyticsAgent()
            out = agent.process(enriched_event)
        assert "aggregate_refresh" in out.payload
        assert "skipped" in out.payload["aggregate_refresh"].get("note", "").lower()
        mock_r2.assert_not_called()
        mock_scope.assert_not_called()

    def test_process_emits_analytics_refreshed(self, enriched_event: EventEnvelope) -> None:
        with (
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": "postgresql+psycopg2://localhost/test"}),
            patch("agents.analytics.agent.session_scope") as mock_scope,
            patch("agents.analytics.agent.refresh_skill_demand_weekly", return_value=0),
            patch("agents.analytics.agent.refresh_tool_demand_weekly", return_value=0),
            patch("agents.analytics.agent.refresh_skill_velocity", return_value=0),
            patch("agents.analytics.agent.refresh_skill_co_occurrence", return_value=0),
        ):
            mock_cm = MagicMock()
            mock_cm.__enter__.return_value = MagicMock()
            mock_cm.__exit__.return_value = None
            mock_scope.return_value = mock_cm
            agent = AnalyticsAgent()
            out = agent.process(enriched_event)
        assert out.payload["event_type"] == "AnalyticsRefreshed"
        assert out.agent_id == "analytics-agent"

    def test_process_includes_batch_data(self, enriched_event: EventEnvelope) -> None:
        """Output payload contains AnalyticsRefreshed Week 7 count fields."""
        agent = AnalyticsAgent()
        agent.health_check()
        with (
            patch("agents.analytics.agent.check_db_connection", return_value=False),
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": ""}),
        ):
            out = agent.process(enriched_event)
        p = out.payload
        assert p["event_type"] == "AnalyticsRefreshed"
        assert p["batch_id"] == enriched_event.payload["batch_id"]
        assert "refreshed_at" in p
        assert "freshness_record_count" in p
        assert "trajectory_map_count" in p
        assert "summaries_generated_count" in p
        assert p["triggered_by_batch_id"] == enriched_event.payload["batch_id"]

    def test_process_clustering_includes_clustering_keys(self, enriched_event: EventEnvelope) -> None:
        """Clustering output payload contains clustering-related keys."""
        agent = AnalyticsAgent()
        with (
            patch("agents.analytics.agent.check_db_connection", return_value=False),
            patch.dict(os.environ, {"PYTHON_DATABASE_URL": ""}),
        ):
            out = agent.process_clustering(enriched_event)
        p = out.payload
        assert p["event_type"] == "AnalyticsRefreshed"
        assert "canonical_clustering_ran" in p
        assert "clustering_skipped" in p

    def test_default_analytics_target_week_is_prior_monday(self) -> None:
        # Wednesday 2025-01-08 -> this_monday 2025-01-06 -> prior Monday 2024-12-30
        ref = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
        assert default_analytics_target_week(ref) == date(2024, 12, 30)

    def test_resolve_target_week_iso_string(self) -> None:
        p = {"analytics_target_week": "2025-01-06"}
        assert _resolve_target_week(p) == date(2025, 1, 6)
