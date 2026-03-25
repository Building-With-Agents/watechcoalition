"""Tests for EnrichmentAgent — deterministic classification + walking-skeleton fixture."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.classification import classify_job
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult


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

    def test_process_spam_from_ei_uses_score_spam_preview(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "PYTHON_DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/db",
        )
        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="c-spam-1",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtracted",
                "posting_id": 99,
                "normalized_job_id": 42,
                "title": "Backend Engineer",
                "description": "Build APIs.",
                "company": "Acme",
                "skills": [],
            },
        )
        ei_row = {
            "skills": [{"label": "Python"}],
            "tools": [],
            "tasks": [],
            "responsibilities": [],
            "context": [],
            "extraction_failed": False,
        }
        mock_exec_result = MagicMock()
        mock_exec_result.mappings.return_value.first.return_value = ei_row
        mock_session = MagicMock()
        mock_session.execute.return_value = mock_exec_result

        spam_ret = SpamPreviewResult(
            spam_score=0.25,
            is_spam=False,
            tier="clean",
            field_confidence={"spam_score": 0.88},
            overall_confidence=0.88,
            rationale="unit_test",
            degraded=False,
            extraction_note=None,
            used_heuristic=False,
        )

        with (
            patch("agents.enrichment.agent.session_scope") as mock_scope,
            patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret) as mock_score,
        ):
            mock_scope.return_value.__enter__.return_value = mock_session
            mock_scope.return_value.__exit__.return_value = None
            out = agent.process(ev)

        assert out.payload["normalized_job_id"] == 42
        assert out.payload["spam_score"] == 0.25
        assert out.payload["is_spam"] is False
        assert out.payload["spam_tier"] == "clean"
        assert out.payload["field_confidence"]["spam_score"] == 0.88
        assert out.payload["spam_rationale"] == "unit_test"
        mock_score.assert_called_once()
        kw = mock_score.call_args.kwargs
        assert kw["job_title"] == "Backend Engineer"
        assert kw["job_description"] == "Build APIs."
        assert kw["extraction_failed"] is False
        assert kw["extraction_empty"] is False
