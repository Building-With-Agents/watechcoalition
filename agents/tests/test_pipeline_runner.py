"""
Tests for the pipeline runner: health check gating, correlation_id propagation, 8-stage processing.

Covers agents/pipeline_runner.py (Week 2 walking skeleton). Does not recreate test_base_agent.py.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.common.base_agent import AgentBase
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
from agents.pipeline_runner import PIPELINE, process_record, run_health_checks
from agents.skills_extraction.agent import SkillsExtractionAgent

# Expected agent order for 8-stage pipeline (Phase 1 + Phase 2)
_EXPECTED_AGENT_IDS = [
    "ingestion-agent",
    "normalization-agent",
    "skills-extraction-agent",
    "enrichment-agent",
    "analytics-agent",
    "visualization-agent",
    "orchestration-agent",
    "demand-analysis-agent",
]


# ---------------------------------------------------------------------------
# AgentBase compatibility (runbook: framework must honor existing base class)
# ---------------------------------------------------------------------------


class TestAgentBaseCompatibility:
    """All pipeline agents must be subclasses of AgentBase; no conflicting base class."""

    def test_all_pipeline_agents_extend_agent_base(self) -> None:
        """Every agent in PIPELINE is a subclass of AgentBase (configuration boundary test)."""
        for agent, _ in PIPELINE:
            assert isinstance(agent, AgentBase), (
                f"Agent {agent.agent_id} must be a subclass of AgentBase"
            )

    def test_exp007_runner_agents_extend_agent_base(self) -> None:
        """Agents used by EXP-007 LangGraph and Pure Python runners honor AgentBase (no conflicting base)."""
        for agent_class in (IngestionAgent, NormalizationAgent, SkillsExtractionAgent):
            agent = agent_class()
            assert isinstance(agent, AgentBase), (
                f"{agent_class.__name__} must be a subclass of AgentBase for EXP-007 runners"
            )


# ---------------------------------------------------------------------------
# Health check gating (Phase 1 vs Phase 2)
# ---------------------------------------------------------------------------


class TestHealthCheckGating:
    """Phase 1 agent failure aborts; Phase 2 failure is warning only."""

    def test_run_health_checks_returns_true_when_all_phase1_healthy(self) -> None:
        """With default PIPELINE and fixtures present, all Phase 1 agents pass."""
        result = run_health_checks(PIPELINE)
        assert result is True, (
            "All Phase 1 agents must pass health_check(); "
            "ensure agents/data/fixtures/fallback_scrape_sample.json exists"
        )

    def test_run_health_checks_returns_false_when_phase1_agent_unhealthy(self) -> None:
        """If any Phase 1 agent returns status != 'ok', run_health_checks returns False."""
        unhealthy = MagicMock()
        unhealthy.agent_id = "mock-phase1-agent"
        unhealthy.health_check.return_value = {"status": "down", "agent": unhealthy.agent_id}
        pipeline_with_unhealthy: list[tuple] = [
            (unhealthy, False),  # Phase 1, unhealthy
        ]
        assert run_health_checks(pipeline_with_unhealthy) is False

    def test_run_health_checks_returns_true_when_only_phase2_agent_unhealthy(self) -> None:
        """Phase 2 agent returning non-ok must not cause run_health_checks to return False."""
        healthy = MagicMock()
        healthy.agent_id = "mock-phase1-agent"
        healthy.health_check.return_value = {"status": "ok", "agent": healthy.agent_id}
        unhealthy_phase2 = MagicMock()
        unhealthy_phase2.agent_id = "mock-phase2-agent"
        unhealthy_phase2.health_check.return_value = {"status": "down", "agent": unhealthy_phase2.agent_id}
        pipeline_phase2_unhealthy: list[tuple] = [
            (healthy, False),
            (unhealthy_phase2, True),
        ]
        assert run_health_checks(pipeline_phase2_unhealthy) is True


# ---------------------------------------------------------------------------
# Correlation ID propagation
# ---------------------------------------------------------------------------


class TestCorrelationIdPropagation:
    """Same correlation_id must appear in every log entry for a record."""

    @pytest.fixture
    def sample_posting(self) -> dict:
        return {
            "posting_id": 42,
            "source": "web_scrape",
            "title": "Test Engineer",
            "company": "Test Co",
            "location": "Remote",
        }

    def test_process_record_propagates_correlation_id(self, sample_posting: dict) -> None:
        """Every entry returned by process_record has the same correlation_id."""
        correlation_id = "test-correlation-42"
        entries = process_record(sample_posting, PIPELINE, correlation_id)
        assert len(entries) > 0
        for entry in entries:
            assert entry.get("correlation_id") == correlation_id, (
                f"Expected correlation_id {correlation_id} in every entry"
            )


# ---------------------------------------------------------------------------
# 8-stage processing
# ---------------------------------------------------------------------------


class TestEightStageProcessing:
    """One record produces 8 log entries (one per agent)."""

    @pytest.fixture
    def sample_posting(self) -> dict:
        return {
            "posting_id": 1,
            "source": "web_scrape",
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "location": "Redmond, WA",
        }

    def test_process_record_returns_one_entry_per_agent(self, sample_posting: dict) -> None:
        """process_record returns exactly len(PIPELINE) entries (8)."""
        entries = process_record(sample_posting, PIPELINE, "cid-1")
        assert len(entries) == len(PIPELINE), (
            f"Expected {len(PIPELINE)} entries, got {len(entries)}"
        )

    def test_process_record_agent_order_matches_pipeline(self, sample_posting: dict) -> None:
        """Agent IDs in the run log appear in the same order as PIPELINE."""
        entries = process_record(sample_posting, PIPELINE, "cid-1")
        assert len(entries) == len(_EXPECTED_AGENT_IDS)
        for i, entry in enumerate(entries):
            assert entry.get("agent_id") == _EXPECTED_AGENT_IDS[i], (
                f"Position {i}: expected {_EXPECTED_AGENT_IDS[i]}, got {entry.get('agent_id')}"
            )
