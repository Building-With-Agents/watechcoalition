"""Tests for pipeline_runner — health checks and per-record processing."""

from __future__ import annotations

from agents.pipeline_runner import PIPELINE, process_record, run_health_checks


class TestRunHealthChecks:
    """Verify health check gating logic."""

    def test_all_pass(self) -> None:
        """Returns True when all Phase 1 agents are healthy (real pipeline)."""
        assert run_health_checks(PIPELINE) is True

    def test_phase1_failure_aborts(self) -> None:
        """Returns False when a Phase 1 agent reports 'down'."""

        class _UnhealthyAgent:
            agent_id = "broken-agent"

            def health_check(self) -> dict:
                return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

        # Pipeline with one unhealthy Phase 1 agent.
        pipeline = [(_UnhealthyAgent(), False)]
        assert run_health_checks(pipeline) is False

    def test_phase2_failure_continues(self) -> None:
        """Returns True even when a Phase 2 agent reports 'down'."""

        class _HealthyAgent:
            agent_id = "ok-agent"

            def health_check(self) -> dict:
                return {"status": "ok", "agent": self.agent_id, "last_run": None, "metrics": {}}

        class _DownPhase2Agent:
            agent_id = "phase2-down"

            def health_check(self) -> dict:
                return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

        pipeline = [
            (_HealthyAgent(), False),   # Phase 1 — healthy
            (_DownPhase2Agent(), True),  # Phase 2 — down but should not abort
        ]
        assert run_health_checks(pipeline) is True


class TestProcessRecord:
    """Verify per-record pipeline execution with real agents and fixtures."""

    _RAW_POSTING = {
        "posting_id": 1,
        "source": "web_scrape",
        "url": "https://careers.microsoft.com/jobs/1234567",
        "timestamp": "2026-02-24T08:15:00Z",
        "title": "Senior Data Engineer",
        "company": "Microsoft",
        "location": "Redmond, WA",
        "raw_text": "Microsoft is hiring a Senior Data Engineer...",
    }

    @classmethod
    def setup_class(cls) -> None:
        """Run health checks once to pre-load fixtures for all agents."""
        run_health_checks(PIPELINE)

    def test_produces_8_entries(self) -> None:
        """Single record through the full pipeline yields 8 log entries."""
        entries = process_record(self._RAW_POSTING, PIPELINE, correlation_id="test-1")
        assert len(entries) == 8

    def test_correlation_id_consistency(self) -> None:
        """All 8 entries share the same correlation_id."""
        entries = process_record(self._RAW_POSTING, PIPELINE, correlation_id="test-cid")
        for entry in entries:
            assert entry["correlation_id"] == "test-cid"

    def test_all_envelope_fields_present(self) -> None:
        """Every entry has all 6 required envelope fields."""
        required = {"agent_id", "event_id", "correlation_id", "timestamp", "schema_version", "payload"}
        entries = process_record(self._RAW_POSTING, PIPELINE, correlation_id="test-fields")
        for entry in entries:
            missing = required - set(entry.keys())
            assert not missing, f"Entry from {entry.get('agent_id')} missing: {missing}"

    def test_unique_event_ids(self) -> None:
        """All 8 event_id values are unique."""
        entries = process_record(self._RAW_POSTING, PIPELINE, correlation_id="test-uids")
        event_ids = [e["event_id"] for e in entries]
        assert len(set(event_ids)) == len(event_ids)
