"""Tests for EnrichmentAgent — deterministic classification + walking-skeleton fixture."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classification import classify_job


class TestEnrichmentAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = EnrichmentAgent()
        assert agent.agent_id == "enrichment-agent"

    def test_health_check_degraded_without_db_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        result = agent.health_check()
        assert result["status"] == "degraded"
        assert result["metrics"].get("reason") == "PYTHON_DATABASE_URL not set"

    def test_health_check_ok_when_db_reachable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(
            "PYTHON_DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/db",
        )
        with patch("agents.enrichment.agent.check_db_connection", return_value=True):
            agent = EnrichmentAgent()
            result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_down_when_db_unreachable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(
            "PYTHON_DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/db",
        )
        with patch("agents.enrichment.agent.check_db_connection", return_value=False):
            agent = EnrichmentAgent()
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_record_enriched(
        self,
        skills_event: EventEnvelope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"
        exp_role, exp_sen = classify_job(
            "Senior Data Engineer",
            None,
            None,
            list(agent._ensure_refs()[0]),
            list(agent._ensure_refs()[1]),
        )
        assert out.payload["role_classification"] == exp_role
        assert out.payload["seniority"] == exp_sen

    def test_process_carries_skills_forward(
        self,
        skills_event: EventEnvelope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        out = agent.process(skills_event)
        assert out.payload["skills"] == skills_event.payload["skills"]
