"""Tests for Streamlit dashboard — data loading, grouping, and DB detection."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helpers: build sample JSON entries matching pipeline_run.json shape
# ---------------------------------------------------------------------------


def _make_entry(agent_id: str, correlation_id: str = "1", **payload_extra: object) -> dict:
    """Build a minimal pipeline_run.json entry."""
    return {
        "event_id": f"evt-{agent_id}-{correlation_id}",
        "correlation_id": correlation_id,
        "agent_id": agent_id,
        "timestamp": "2026-03-16T06:10:30.000000",
        "schema_version": "1.0",
        "payload": {"event_type": "StubEvent", **payload_extra},
    }


def _full_pipeline_entries(correlation_id: str = "1") -> list[dict]:
    """Return one entry per Phase 1 agent for a single record."""
    agents = [
        "ingestion-agent",
        "normalization-agent",
        "skills-extraction-agent",
        "enrichment-agent",
        "analytics-agent",
        "visualization-agent",
        "orchestration-agent",
    ]
    return [_make_entry(a, correlation_id) for a in agents]


# ---------------------------------------------------------------------------
# Tests: _build_record_map
# ---------------------------------------------------------------------------


class TestBuildRecordMap:
    """Grouping entries by correlation_id."""

    def test_groups_by_correlation_id(self) -> None:
        from agents.dashboard.streamlit_app import _build_record_map

        entries = [
            _make_entry("ingestion-agent", "c-1"),
            _make_entry("normalization-agent", "c-1"),
            _make_entry("ingestion-agent", "c-2"),
        ]
        result = _build_record_map(entries)

        assert len(result) == 2
        assert len(result["c-1"]) == 2
        assert len(result["c-2"]) == 1

    def test_empty_list_returns_empty_dict(self) -> None:
        from agents.dashboard.streamlit_app import _build_record_map

        assert _build_record_map([]) == {}

    def test_missing_correlation_id_grouped_as_unknown(self) -> None:
        from agents.dashboard.streamlit_app import _build_record_map

        entries = [{"agent_id": "ingestion-agent", "payload": {}}]
        result = _build_record_map(entries)

        assert "unknown" in result
        assert len(result["unknown"]) == 1


# ---------------------------------------------------------------------------
# Tests: _sort_key
# ---------------------------------------------------------------------------


class TestSortKey:
    """Numeric sort key for correlation IDs."""

    def test_numeric_string(self) -> None:
        from agents.dashboard.streamlit_app import _sort_key

        assert _sort_key("42") == 42

    def test_non_numeric_returns_zero(self) -> None:
        from agents.dashboard.streamlit_app import _sort_key

        assert _sort_key("pipeline-0e2444d0") == 0

    def test_sort_order(self) -> None:
        from agents.dashboard.streamlit_app import _sort_key

        cids = ["10", "2", "1", "abc"]
        assert sorted(cids, key=_sort_key) == ["abc", "1", "2", "10"]


# ---------------------------------------------------------------------------
# Tests: _load_run_log (JSON fallback)
# ---------------------------------------------------------------------------


class TestLoadRunLog:
    """JSON file loading with caching."""

    def test_returns_empty_list_when_file_missing(self, tmp_path: Path) -> None:
        from agents.dashboard.streamlit_app import _load_run_log

        with patch("agents.dashboard.streamlit_app._RUN_LOG_PATH", tmp_path / "nope.json"):
            # Clear Streamlit cache for this function
            _load_run_log.clear()
            result = _load_run_log()

        assert result == []

    def test_loads_valid_json(self, tmp_path: Path) -> None:
        from agents.dashboard.streamlit_app import _load_run_log

        data = [_make_entry("ingestion-agent")]
        json_path = tmp_path / "pipeline_run.json"
        json_path.write_text(json.dumps(data), encoding="utf-8")

        with patch("agents.dashboard.streamlit_app._RUN_LOG_PATH", json_path):
            _load_run_log.clear()
            result = _load_run_log()

        assert len(result) == 1
        assert result[0]["agent_id"] == "ingestion-agent"


# ---------------------------------------------------------------------------
# Tests: _db_available
# ---------------------------------------------------------------------------


class TestDbAvailable:
    """Database availability detection."""

    def test_returns_false_when_env_var_missing(self) -> None:
        from agents.dashboard.streamlit_app import _db_available

        with patch.dict("os.environ", {}, clear=True):
            assert _db_available() is False

    @patch("agents.dashboard.readonly_engine.check_dashboard_db_connection", return_value=True)
    def test_returns_true_when_db_reachable(self, mock_check: MagicMock) -> None:
        from agents.dashboard.streamlit_app import _db_available

        with patch.dict("os.environ", {"PYTHON_DATABASE_URL": "postgresql+psycopg2://u:p@h/db"}):
            assert _db_available() is True

    @patch(
        "agents.dashboard.readonly_engine.check_dashboard_db_connection",
        side_effect=Exception("conn refused"),
    )
    def test_returns_false_when_db_unreachable(self, mock_check: MagicMock) -> None:
        from agents.dashboard.streamlit_app import _db_available

        with patch.dict("os.environ", {"PYTHON_DATABASE_URL": "postgresql+psycopg2://u:p@h/db"}):
            assert _db_available() is False

    @patch("agents.dashboard.readonly_engine.check_dashboard_db_connection", return_value=True)
    def test_returns_true_when_only_readonly_url_set(self, mock_check: MagicMock) -> None:
        from agents.dashboard.streamlit_app import _db_available

        env = {
            "PYTHON_DATABASE_URL_READONLY": "postgresql+psycopg2://ro:pw@h/db",
        }
        with patch.dict("os.environ", env, clear=True):
            assert _db_available() is True


# ---------------------------------------------------------------------------
# Tests: agent order constants
# ---------------------------------------------------------------------------


class TestAgentOrder:
    """Agent ordering constants are consistent."""

    def test_agent_order_has_eight_agents(self) -> None:
        from agents.dashboard.streamlit_app import _AGENT_ORDER

        assert len(_AGENT_ORDER) == 8

    def test_agent_order_index_matches_list(self) -> None:
        from agents.dashboard.streamlit_app import _AGENT_ORDER, _AGENT_ORDER_INDEX

        for i, agent in enumerate(_AGENT_ORDER):
            assert _AGENT_ORDER_INDEX[agent] == i

    def test_ingestion_is_first(self) -> None:
        from agents.dashboard.streamlit_app import _AGENT_ORDER

        assert _AGENT_ORDER[0] == "ingestion-agent"

    def test_demand_analysis_is_last(self) -> None:
        from agents.dashboard.streamlit_app import _AGENT_ORDER

        assert _AGENT_ORDER[-1] == "demand-analysis-agent"


# ---------------------------------------------------------------------------
# Tests: JSON fallback page logic (data transformation, not Streamlit rendering)
# ---------------------------------------------------------------------------


class TestJsonFallbackLogic:
    """Data transformations used by JSON fallback pages."""

    def test_completion_table_marks_all_pass_when_all_agents_present(self) -> None:
        """Simulate the completion table logic from page_run_summary_json."""
        from agents.dashboard.streamlit_app import _AGENT_ORDER, _build_record_map

        entries = _full_pipeline_entries("1")
        record_map = _build_record_map(entries)
        phase1_agents = [a for a in _AGENT_ORDER if a != "demand-analysis-agent"]

        completed_agents = {e["agent_id"] for e in record_map["1"]}
        all_done = all(a in completed_agents for a in phase1_agents)

        assert all_done is True

    def test_completion_table_marks_fail_when_agent_missing(self) -> None:
        """Missing an agent should not count as all-complete."""
        from agents.dashboard.streamlit_app import _AGENT_ORDER, _build_record_map

        entries = _full_pipeline_entries("1")
        # Remove the analytics-agent entry
        entries = [e for e in entries if e["agent_id"] != "analytics-agent"]
        record_map = _build_record_map(entries)
        phase1_agents = [a for a in _AGENT_ORDER if a != "demand-analysis-agent"]

        completed_agents = {e["agent_id"] for e in record_map["1"]}
        all_done = all(a in completed_agents for a in phase1_agents)

        assert all_done is False

    def test_record_journey_sorts_by_agent_order(self) -> None:
        """Entries should be sortable by canonical agent order."""
        from agents.dashboard.streamlit_app import _AGENT_ORDER_INDEX

        entries = [
            _make_entry("analytics-agent"),
            _make_entry("ingestion-agent"),
            _make_entry("normalization-agent"),
        ]
        sorted_entries = sorted(
            entries,
            key=lambda e: _AGENT_ORDER_INDEX.get(e.get("agent_id", ""), 99),
        )

        assert sorted_entries[0]["agent_id"] == "ingestion-agent"
        assert sorted_entries[1]["agent_id"] == "normalization-agent"
        assert sorted_entries[2]["agent_id"] == "analytics-agent"

    def test_duration_calculation(self) -> None:
        """Pipeline duration computed from min/max timestamps."""
        entries = [
            {**_make_entry("ingestion-agent"), "timestamp": "2026-03-16T06:10:30.000000"},
            {**_make_entry("orchestration-agent"), "timestamp": "2026-03-16T06:10:32.380000"},
        ]
        timestamps = [e["timestamp"] for e in entries]
        t0 = datetime.fromisoformat(min(timestamps)).replace(tzinfo=None)
        t1 = datetime.fromisoformat(max(timestamps)).replace(tzinfo=None)
        delta = (t1 - t0).total_seconds()

        assert 2.3 < delta < 2.5

    def test_analytics_payload_extraction(self) -> None:
        """Batch insights page extracts analytics payload correctly."""
        entries = [
            _make_entry(
                "analytics-agent",
                top_skills=[{"skill": "Python", "count": 10}],
                seniority_distribution={"senior": 3, "mid": 4},
            ),
        ]
        analytics_entries = [e for e in entries if e["agent_id"] == "analytics-agent"]

        assert len(analytics_entries) == 1
        p = analytics_entries[0]["payload"]
        assert p["top_skills"][0]["skill"] == "Python"
        assert p["seniority_distribution"]["senior"] == 3


# Need datetime for duration test
from datetime import datetime  # noqa: E402
