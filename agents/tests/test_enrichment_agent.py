"""Tests for EnrichmentAgent — deterministic classification + walking-skeleton fixture."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import InProcessEventBus
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.agent import register_alert_bus as register_enrichment_alert_bus
from agents.enrichment.classification import classify_job
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
from agents.scripts.jsearch_enrichment_preview_lib import build_extraction_dict


class TestEnrichmentAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def _process_with_normalized_job_context(
        self,
        monkeypatch: pytest.MonkeyPatch,
        *,
        resolved_job_posting: dict[str, object],
    ) -> EventEnvelope:
        monkeypatch.setenv(
            "PYTHON_DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/db",
        )
        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="c-enrichment-output-fields",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtracted",
                "posting_id": 202,
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
            patch("agents.enrichment.agent.resolve_job_posting_row", return_value=resolved_job_posting),
            patch("agents.enrichment.agent.score_spam_preview", return_value=spam_ret),
            patch("agents.enrichment.agent.apply_enrichment_to_job_postings"),
        ):
            mock_scope.return_value.__enter__.return_value = mock_session
            mock_scope.return_value.__exit__.return_value = None
            return agent.process(ev)

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
        p = skills_event.payload
        ext = build_extraction_dict(p.get("skills"), [], [], [], [])
        exp_role, exp_sen = classify_job(
            "Senior Data Engineer",
            None,
            ext,
            list(agent._ensure_refs()[0]),
            list(agent._ensure_refs()[1]),
        )
        assert out.payload["role_classification"] == exp_role
        assert out.payload["seniority"] == exp_sen
        assert "quality_score" in out.payload
        assert isinstance(out.payload["quality_score"], float)
        assert 0.0 <= out.payload["quality_score"] <= 1.0
        assert "quality_components" in out.payload
        assert isinstance(out.payload["quality_components"], dict)

    def test_process_carries_skills_forward(
        self,
        skills_event: EventEnvelope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        out = agent.process(skills_event)
        assert out.payload["skills"] == skills_event.payload["skills"]

    def test_process_emits_temporal_period_on_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out = self._process_with_normalized_job_context(
            monkeypatch,
            resolved_job_posting={
                "job_posting_id": "11111111-1111-1111-1111-111111111111",
                "company_id": "22222222-2222-2222-2222-222222222222",
                "date_posted": datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc),
                "city": "Austin",
                "state_province": "Texas",
                "country": "United States",
                "is_remote": False,
                "work_arrangement": "on-site",
            },
        )

        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["temporal_period"] == "post_gpt4"

    def test_process_emits_borderplex_subregion_on_payload(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out = self._process_with_normalized_job_context(
            monkeypatch,
            resolved_job_posting={
                "job_posting_id": "11111111-1111-1111-1111-111111111111",
                "company_id": "22222222-2222-2222-2222-222222222222",
                "date_posted": datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc),
                "city": "El Paso",
                "state_province": "Texas",
                "country": "United States",
                "is_remote": False,
                "work_arrangement": "on-site",
            },
        )

        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["borderplex_subregion"] == "el_paso"

    def test_process_emits_temporal_period_and_borderplex_subregion_together(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        out = self._process_with_normalized_job_context(
            monkeypatch,
            resolved_job_posting={
                "job_posting_id": "11111111-1111-1111-1111-111111111111",
                "company_id": "22222222-2222-2222-2222-222222222222",
                "date_posted": datetime(2023, 6, 15, 12, 0, tzinfo=timezone.utc),
                "city": "El Paso",
                "state_province": "Texas",
                "country": "United States",
                "is_remote": False,
                "work_arrangement": "on-site",
            },
        )

        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["temporal_period"] == "post_gpt4"
        assert out.payload["borderplex_subregion"] == "el_paso"

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
            patch("agents.enrichment.agent.apply_enrichment_to_job_postings"),
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
        assert isinstance(out.payload["quality_score"], float)
        assert 0.0 <= out.payload["quality_score"] <= 1.0
        assert "completeness" in out.payload["quality_components"]
        mock_score.assert_called_once()
        kw = mock_score.call_args.kwargs
        assert kw["job_title"] == "Backend Engineer"
        assert kw["job_description"] == "Build APIs."
        assert kw["extraction_failed"] is False
        assert kw["extraction_empty"] is False

    def test_process_spam_degraded_emits_enrichment_degraded_alert(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv(
            "PYTHON_DATABASE_URL",
            "postgresql+psycopg2://user:pass@localhost:5432/db",
        )
        bus = InProcessEventBus()
        alerts: list[EventEnvelope] = []
        bus.subscribe(
            "EnrichmentDegraded",
            lambda event: alerts.append(event),
            subscriber_id="orchestration-agent",
        )
        register_enrichment_alert_bus(bus)

        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="c-spam-degraded",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtracted",
                "posting_id": 101,
                "normalized_job_id": 77,
                "title": "ML Engineer",
                "description": "Build production ML systems.",
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

        degraded_ret = SpamPreviewResult(
            spam_score=None,
            is_spam=None,
            tier="uncertain",
            field_confidence={},
            overall_confidence=None,
            rationale=None,
            degraded=True,
            extraction_note="empty_extraction",
            used_heuristic=False,
        )

        try:
            with (
                patch("agents.enrichment.agent.session_scope") as mock_scope,
                patch(
                    "agents.enrichment.agent.score_spam_preview",
                    return_value=degraded_ret,
                ),
                patch("agents.enrichment.agent.apply_enrichment_to_job_postings"),
            ):
                mock_scope.return_value.__enter__.return_value = mock_session
                mock_scope.return_value.__exit__.return_value = None
                out = agent.process(ev)
        finally:
            register_enrichment_alert_bus(None)

        assert out.payload["spam_score"] is None
        assert out.payload["is_spam"] is None
        assert out.payload["spam_tier"] == "uncertain"
        assert out.payload["spam_degraded"] is True

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.correlation_id == "c-spam-degraded"
        assert alert.agent_id == "enrichment-agent"
        assert alert.payload["event_type"] == "EnrichmentDegraded"
        assert alert.payload["posting_id"] == 101
        assert alert.payload["normalized_job_id"] == 77
        assert alert.payload["triggered_by_event_type"] == "SkillsExtracted"
        assert alert.payload["classifier"] == "spam_preview"
        assert alert.payload["reason"] == "spam_classifier_unavailable"
        assert alert.payload["extraction_note"] == "empty_extraction"
