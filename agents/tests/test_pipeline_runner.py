"""Tests for pipeline_runner — health checks and batch pipeline execution."""

from __future__ import annotations

from agents.pipeline_runner import PIPELINE, run_health_checks, run_pipeline


class TestRunHealthChecks:
    """Verify health check gating logic."""

    def test_all_pass(self) -> None:
        """Returns True when all Phase 1 agents are healthy (real pipeline).

        DB-dependent agents (ingestion, normalization) report "degraded"
        without a database, which is accepted by the pipeline runner.
        """
        assert run_health_checks(PIPELINE) is True

    def test_phase1_failure_aborts(self) -> None:
        """Returns False when a Phase 1 agent reports 'down'."""

        class _UnhealthyAgent:
            agent_id = "broken-agent"

            def health_check(self) -> dict:
                return {"status": "down", "agent": self.agent_id, "last_run": None, "metrics": {}}

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
            (_HealthyAgent(), False),
            (_DownPhase2Agent(), True),
        ]
        assert run_health_checks(pipeline) is True

    def test_degraded_is_acceptable(self) -> None:
        """Degraded status does not abort the pipeline."""

        class _DegradedAgent:
            agent_id = "degraded-agent"

            def health_check(self) -> dict:
                return {"status": "degraded", "agent": self.agent_id, "last_run": None, "metrics": {}}

        pipeline = [(_DegradedAgent(), False)]
        assert run_health_checks(pipeline) is True


class TestRunPipelineStubs:
    """Test pipeline execution with stub agents (no DB required)."""

    def test_stub_pipeline_produces_entries(self) -> None:
        """A pipeline of stub agents that don't need DB still produces entries."""
        from agents.analytics.agent import AnalyticsAgent
        from agents.enrichment.agent import EnrichmentAgent
        from agents.orchestration.agent import OrchestrationAgent
        from agents.skills_extraction.agent import SkillsExtractionAgent
        from agents.visualization.agent import VisualizationAgent

        stub_pipeline = [
            (SkillsExtractionAgent(), False),
            (EnrichmentAgent(), False),
            (AnalyticsAgent(), False),
            (VisualizationAgent(), False),
            (OrchestrationAgent(), False),
        ]
        trigger = {"event_type": "NormalizationComplete", "posting_id": 1}
        entries = run_pipeline(stub_pipeline, "test-stubs", trigger)
        assert len(entries) == 5

    def test_correlation_id_consistency(self) -> None:
        """All entries share the same correlation_id."""
        from agents.analytics.agent import AnalyticsAgent
        from agents.enrichment.agent import EnrichmentAgent
        from agents.orchestration.agent import OrchestrationAgent
        from agents.skills_extraction.agent import SkillsExtractionAgent
        from agents.visualization.agent import VisualizationAgent

        stub_pipeline = [
            (SkillsExtractionAgent(), False),
            (EnrichmentAgent(), False),
            (AnalyticsAgent(), False),
            (VisualizationAgent(), False),
            (OrchestrationAgent(), False),
        ]
        trigger = {"event_type": "NormalizationComplete", "posting_id": 1}
        entries = run_pipeline(stub_pipeline, "test-cid", trigger)
        for entry in entries:
            assert entry["correlation_id"] == "test-cid"

    def test_all_envelope_fields_present(self) -> None:
        """Every entry has all 6 required envelope fields."""
        from agents.skills_extraction.agent import SkillsExtractionAgent

        stub_pipeline = [(SkillsExtractionAgent(), False)]
        trigger = {"event_type": "NormalizationComplete", "posting_id": 1}
        entries = run_pipeline(stub_pipeline, "test-fields", trigger)
        required = {"agent_id", "event_id", "correlation_id", "timestamp", "schema_version", "payload"}
        for entry in entries:
            missing = required - set(entry.keys())
            assert not missing, f"Entry from {entry.get('agent_id')} missing: {missing}"
