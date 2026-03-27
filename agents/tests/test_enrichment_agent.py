"""Tests for EnrichmentAgent: batch RecordEnriched, classification, and EI spam preview."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import InProcessEventBus
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.agent import register_alert_bus as register_enrichment_alert_bus
from agents.enrichment.classification import classify_job
from agents.enrichment.classifiers.spam_preview import SpamPreviewResult
from agents.scripts.jsearch_enrichment_preview_lib import build_extraction_dict

BATCH_RECORD_ENRICHED_KEYS = frozenset({
    "event_type",
    "batch_id",
    "enriched_count",
    "spam_rejected_count",
    "flagged_for_review_count",
    "spam_tier_counts",
})


class TestEnrichmentAgent:
    """Verify agent_id, health_check, and batch process behaviour."""

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

    def test_process_emits_batch_record_enriched(
        self,
        skills_event: EventEnvelope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"
        assert set(out.payload.keys()) == BATCH_RECORD_ENRICHED_KEYS
        tiers = out.payload["spam_tier_counts"]
        assert sum(tiers.values()) == 1

    def test_process_passes_skills_into_enrich_record(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        captured: dict = {}

        def capture_enrich(posting: dict, session: object) -> dict:
            captured["skills"] = posting.get("skills")
            return {"enriched": True}

        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", side_effect=capture_enrich),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            agent.process(skills_event)
        assert captured.get("skills") == skills_event.payload["skills"]

    def test_spam_rejected_skips_resolution(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": True}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with patch.object(EnrichmentAgent, "enrich_record") as mock_enrich:
            out = agent.process(event)
        mock_enrich.assert_not_called()
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["spam_rejected_count"] == 1
        assert out.payload["enriched_count"] == 0

    def test_flagged_record_skips_resolution(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": None}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with patch.object(EnrichmentAgent, "enrich_record") as mock_enrich:
            out = agent.process(event)
        mock_enrich.assert_not_called()
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["flagged_for_review_count"] == 1
        assert out.payload["enriched_count"] == 0

    def test_record_enriched_payload_fields(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)
        assert "enriched_count" in out.payload
        assert "spam_rejected_count" in out.payload
        assert "flagged_for_review_count" in out.payload
        assert "spam_tier_counts" in out.payload

    def test_graceful_degradation_when_enrich_record_raises(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", side_effect=Exception("fail")),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["enriched_count"] == 0

    def test_batch_multi_record_aggregates_counts(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {
            **skills_event.payload,
            "batch_id": "batch-multi",
            "records": [
                {"posting_id": 1, "title": "A", "company": "C1", "skills": [], "is_spam": True},
                {"posting_id": 2, "title": "B", "company": "C2", "skills": [], "is_spam": None},
                {
                    "posting_id": 3,
                    "title": "C",
                    "company": "C3",
                    "skills": [],
                    "is_spam": False,
                },
                {
                    "posting_id": 4,
                    "title": "D",
                    "company": "C4",
                    "skills": [],
                    "spam_score": 0.95,
                },
                {
                    "posting_id": 5,
                    "title": "E",
                    "company": "C5",
                    "skills": [],
                    "spam_score": 0.75,
                },
                {
                    "posting_id": 6,
                    "title": "F",
                    "company": "C6",
                    "skills": [],
                    "spam_score": 0.5,
                },
            ],
        }
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)
        assert out.payload["batch_id"] == "batch-multi"
        assert out.payload["spam_rejected_count"] == 2
        assert out.payload["flagged_for_review_count"] == 2
        assert out.payload["enriched_count"] == 2

    def test_spam_score_thresholds_precedence_over_absent_is_spam(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {
            **skills_event.payload,
            "records": [
                {"posting_id": 1, "title": "A", "company": "X", "skills": [], "spam_score": 0.91},
            ],
        }
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with patch.object(EnrichmentAgent, "enrich_record") as mock_enrich:
            out = agent.process(event)
        mock_enrich.assert_not_called()
        assert out.payload["spam_rejected_count"] == 1

    def test_enrich_record_receives_merged_job_columns_from_batch_payload(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        captured: list[dict[str, Any]] = []

        def capture_enrich(posting: dict, session: object) -> dict:
            captured.append(posting)
            return {"ok": True}

        payload = {
            **skills_event.payload,
            "is_spam": False,
            "batch_id": "b97",
            "records": [
                {
                    "posting_id": 1,
                    "title": "Dev",
                    "company": "Acme",
                    "skills": [],
                }
            ],
            "soc_code": "15-1252.00",
            "naics_code": "541511",
            "temporal_period": "agentic_era",
            "borderplex_subregion": "el_paso",
            "is_duplicate": False,
            "duplicate_cluster_id": None,
        }
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", side_effect=capture_enrich),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)

        assert set(out.payload.keys()) == BATCH_RECORD_ENRICHED_KEYS
        assert out.payload["enriched_count"] == 1
        assert len(captured) == 1
        rec = captured[0]
        assert rec["soc_code"] == "15-1252.00"
        assert rec["naics_code"] == "541511"
        assert rec["temporal_period"] == "agentic_era"
        assert rec["borderplex_subregion"] == "el_paso"
        assert rec["is_duplicate"] is False

    def test_enrich_record_return_can_include_job_postings_shape(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        company_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        mock_enriched = {
            "posting_id": skills_event.payload.get("posting_id"),
            "title": skills_event.payload.get("title"),
            "company": skills_event.payload.get("company"),
            "soc_code": "15-1252.00",
            "naics_code": "541511",
            "temporal_period": "agentic_era",
            "borderplex_subregion": "el_paso",
            "is_duplicate": False,
            "duplicate_cluster_id": None,
            "company_id": company_uuid,
            "city": "El Paso",
            "state": "TX",
            "country": "US",
        }
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value=mock_enriched),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)

        assert out.payload["enriched_count"] == 1
        assert out.payload["event_type"] == "RecordEnriched"

    def test_process_uses_session_scope_when_db_available(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        mock_session = MagicMock()
        cm = MagicMock()
        cm.__enter__.return_value = mock_session
        cm.__exit__.return_value = None

        agent = EnrichmentAgent()
        with (
            patch("agents.enrichment.agent.check_db_connection", return_value=True),
            patch("agents.enrichment.agent.session_scope", return_value=cm),
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}) as mock_enrich,
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            agent.process(event)

        mock_enrich.assert_called_once()
        assert mock_enrich.call_args.kwargs.get("session") is mock_session

    def test_process_passes_none_session_when_db_unavailable(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        agent = EnrichmentAgent()
        with (
            patch("agents.enrichment.agent.check_db_connection", return_value=False),
            patch("agents.enrichment.agent.session_scope") as mock_scope,
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}) as mock_enrich,
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            agent.process(event)

        mock_scope.assert_not_called()
        mock_enrich.assert_called_once()
        assert mock_enrich.call_args.kwargs.get("session") is None

    def test_process_falls_back_when_session_scope_raises(
        self, skills_event: EventEnvelope, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        payload = {**skills_event.payload, "is_spam": False}
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )
        cm = MagicMock()
        cm.__enter__.side_effect = RuntimeError("session failed")
        cm.__exit__.return_value = None

        agent = EnrichmentAgent()
        with (
            patch("agents.enrichment.agent.check_db_connection", return_value=True),
            patch("agents.enrichment.agent.session_scope", return_value=cm),
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}) as mock_enrich,
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            agent.process(event)

        mock_enrich.assert_called_once()
        assert mock_enrich.call_args.kwargs.get("session") is None

    def test_classification_runs_before_enrich_offline(
        self,
        skills_event: EventEnvelope,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
        agent = EnrichmentAgent()
        captured: dict[str, Any] = {}

        def capture_enrich(posting: dict, session: object) -> dict:
            captured["role_classification"] = posting.get("role_classification")
            return {"ok": True}

        with (
            patch.object(EnrichmentAgent, "enrich_record", side_effect=capture_enrich),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            agent.process(skills_event)

        p = skills_event.payload
        ext = build_extraction_dict(p.get("skills"), [], [], [], [])
        exp_role, _exp_sen = classify_job(
            "Senior Data Engineer",
            None,
            ext,
            list(agent._ensure_refs()[0]),
            list(agent._ensure_refs()[1]),
        )
        assert captured.get("role_classification") == exp_role

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
                "batch_id": "b-spam",
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
            patch("agents.enrichment.agent.apply_enrichment_to_job_postings") as mock_promo,
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
            patch("agents.enrichment.agent.check_db_connection", return_value=True),
        ):
            mock_scope.return_value.__enter__.return_value = mock_session
            mock_scope.return_value.__exit__.return_value = None
            out = agent.process(ev)

        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["batch_id"] == "b-spam"
        assert out.payload["enriched_count"] == 1
        mock_score.assert_called_once()
        kw = mock_score.call_args.kwargs
        assert kw["job_title"] == "Backend Engineer"
        assert kw["job_description"] == "Build APIs."
        assert kw["extraction_failed"] is False
        assert kw["extraction_empty"] is False
        mock_promo.assert_called_once()

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
            lambda e: alerts.append(e),
            subscriber_id="orchestration-agent",
        )
        register_enrichment_alert_bus(bus)

        agent = EnrichmentAgent()
        ev = EventEnvelope(
            correlation_id="c-spam-degraded",
            agent_id="skills-extraction-agent",
            payload={
                "event_type": "SkillsExtracted",
                "batch_id": "b-deg",
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
                patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
                patch("agents.enrichment.agent.resolve_sector", return_value=None),
                patch("agents.enrichment.agent.check_db_connection", return_value=True),
            ):
                mock_scope.return_value.__enter__.return_value = mock_session
                mock_scope.return_value.__exit__.return_value = None
                out = agent.process(ev)
        finally:
            register_enrichment_alert_bus(None)

        assert out.payload["event_type"] == "RecordEnriched"
        assert out.payload["flagged_for_review_count"] == 1
        assert out.payload["enriched_count"] == 0

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
