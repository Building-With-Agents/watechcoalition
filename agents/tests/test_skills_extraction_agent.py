"""Tests for SkillsExtractionAgent — Week 4 hybrid bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import delete

from agents.common.data_store.database import session_scope
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob
from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord
from agents.skills_extraction.agent import ExtractionWorkItem, SkillsExtractionAgent


class TestSkillsExtractionAgent:
    """Verify agent_id, health_check (incl. failure modes), and process behaviour."""

    def test_agent_id(self) -> None:
        agent = SkillsExtractionAgent()
        assert agent.agent_id == "skills-extraction-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fixture loads and the DB is reachable."""
        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.check_db_connection", return_value=True):
            result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_degraded_fixture_only(self) -> None:
        """Returns 'degraded' when the fixture works but the DB is unavailable."""
        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.check_db_connection", return_value=False):
            result = agent.health_check()
        assert result["status"] == "degraded"

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = SkillsExtractionAgent()
        fake_path = Path("/nonexistent/fixture_skills_extracted.json")
        with (
            patch("agents.skills_extraction.agent._FIXTURE_PATH", fake_path),
            patch("agents.skills_extraction.agent.check_db_connection", return_value=False),
        ):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_health_check_down_bad_json(self, tmp_path: Path) -> None:
        """Returns 'down' when the fixture file contains invalid JSON."""
        bad_file = tmp_path / "fixture_skills_extracted.json"
        bad_file.write_text("NOT VALID JSON {{{", encoding="utf-8")
        agent = SkillsExtractionAgent()
        with (
            patch("agents.skills_extraction.agent._FIXTURE_PATH", bad_file),
            patch("agents.skills_extraction.agent.check_db_connection", return_value=False),
        ):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_skills_extracted(
        self, normalization_event: EventEnvelope
    ) -> None:
        """Output event_type is SkillsExtracted."""
        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = ([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0})
            out = agent.process(normalization_event)
        assert out.payload["event_type"] == "SkillsExtracted"
        assert out.payload["tasks_count"] == 0
        assert out.payload["responsibilities_count"] == 0
        assert out.payload["context_count"] == 0
        assert out.agent_id == "skills-extraction-agent"

    def test_process_returns_fixture_skills(
        self, normalization_event: EventEnvelope
    ) -> None:
        """Output contains a non-empty skills list with expected keys."""
        from agents.common.types import SkillRecord, SpanRecord

        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        mock_skill = SkillRecord(
            skill_name="Python",
            type="Technical",
            confidence=0.9,
            source_span=SpanRecord(
                text="Python", field_source="description", start_char=0, end_char=6
            ),
        )
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = ([mock_skill], {"extraction_failed": False, "tokens_used": 50, "cost_usd": 0.0})
            out = agent.process(normalization_event)
        skills = out.payload["skills"]
        assert isinstance(skills, list)
        assert len(skills) > 0
        for skill in skills:
            assert "skill_name" in skill
            assert "type" in skill
            assert "confidence" in skill

    def test_process_extracts_tools_from_inline_normalized_payload(self) -> None:
        """Inline normalized payloads should run through the real Pass 1 tool extractor."""
        event = EventEnvelope(
            correlation_id="test-inline-tools",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-inline-1",
                "title": "Platform Engineer",
                "company": "Acme",
                "description": "Build Python services with Docker and Terraform.",
                "source": "web_scrape",
                "external_id": "job-inline-1",
            },
        )

        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = ([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0})
            out = agent.process(event)

        assert out.payload["job_ids"] == ["job-inline-1"]
        assert out.payload["tools_count"] == 3
        assert out.payload["tasks_count"] == 0
        assert out.payload["responsibilities_count"] == 0
        assert out.payload["context_count"] == 0
        assert [tool["tool_name"] for tool in out.payload["tools"]] == [
            "Python",
            "Docker",
            "Terraform",
        ]
        assert out.payload["skills"] == []

    @pytest.mark.skipif(not os.getenv("PYTHON_DATABASE_URL"), reason="requires database")
    def test_process_emits_batch_payload_for_inline_job_list(self) -> None:
        """Batch payloads should produce aggregate metrics and per-record summaries."""
        # ExtractionStore persists to extracted_intelligence with FK to normalized_jobs.
        # Session-scoped truncates in other test modules leave normalized_jobs empty; seed
        # parent rows for the inline normalized_job_id values used below.
        run_id = "pytest-batch-inline-2"
        with session_scope() as session:
            session.execute(
                delete(ExtractedIntelligence).where(
                    ExtractedIntelligence.normalized_job_id.in_((11, 12))
                )
            )
            session.execute(delete(NormalizedJob).where(NormalizedJob.id.in_((11, 12))))
            session.add_all(
                [
                    NormalizedJob(
                        id=11,
                        ingestion_run_id=run_id,
                        source="web_scrape",
                        external_id="job-11",
                        title="Backend Engineer",
                        company="Acme",
                        description="Python and PostgreSQL experience required.",
                    ),
                    NormalizedJob(
                        id=12,
                        ingestion_run_id=run_id,
                        source="web_scrape",
                        external_id="job-12",
                        title="Cloud Engineer",
                        company="Acme",
                        description="Work with AWS and Terraform daily.",
                    ),
                ]
            )

        event = EventEnvelope(
            correlation_id="test-batch-tools",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-inline-2",
                "normalized_jobs": [
                    {
                        "normalized_job_id": 11,
                        "title": "Backend Engineer",
                        "company": "Acme",
                        "description": "Python and PostgreSQL experience required.",
                        "source": "web_scrape",
                        "external_id": "job-11",
                    },
                    {
                        "normalized_job_id": 12,
                        "title": "Cloud Engineer",
                        "company": "Acme",
                        "description": "Work with AWS and Terraform daily.",
                        "source": "web_scrape",
                        "external_id": "job-12",
                    },
                ],
            },
        )

        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = ([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0})
            out = agent.process(event)

        assert out.payload["batch_id"] == "batch-inline-2"
        assert out.payload["job_ids"] == [11, 12]
        assert out.payload["tools_count"] == 4
        assert out.payload["tasks_count"] == 0
        assert out.payload["responsibilities_count"] == 0
        assert out.payload["context_count"] == 0
        assert len(out.payload["records"]) == 2
        assert out.payload["failed_count"] == 0

    def test_process_passes_results_to_injected_store(self) -> None:
        """The integration layer should hand extracted records to the persistence store."""

        @dataclass
        class _FakeLoader:
            work_items: list

            def load(self, event: EventEnvelope) -> list:
                return self.work_items

        class _FakeStore:
            def __init__(self) -> None:
                self.saved_results = []

            def save(self, results) -> None:
                self.saved_results = list(results)

        work_item = ExtractionWorkItem(
            job_id=99,
            posting_id=None,
            normalized_job_id=99,
            title="Platform Engineer",
            company="Acme",
            job_record=JobRecord(
                source="web_scrape",
                external_id="job-99",
                title="Platform Engineer",
                company="Acme",
                description="Python and Docker experience required.",
            ),
        )
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader([work_item]),
            extraction_store=store,
        )

        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = ([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0})
            out = agent.process(
                EventEnvelope(
                    correlation_id="test-store",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-store"},
                )
            )

        assert out.payload["tools_count"] == 2
        assert len(store.saved_results) == 1
        assert [tool.tool_name for tool in store.saved_results[0].tools] == ["Python", "Docker"]

    def test_process_payload_has_taxonomy_coverage_and_cost_when_llm_used(self) -> None:
        """When extract_skills returns skills and metadata, payload has taxonomy_coverage and extraction_cost_usd."""
        from agents.common.types import SkillRecord, SpanRecord

        event = EventEnvelope(
            correlation_id="test-metrics",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-metrics",
                "title": "Data Engineer",
                "company": "Acme",
                "description": "Python and SQL required.",
                "source": "test",
                "external_id": "job-metrics",
            },
        )
        skill_with_esco = SkillRecord(
            label="Python",
            type="Technical",
            confidence=0.9,
            esco_uri="http://data.europa.eu/esco/skill/abc",
            is_genai_extension=False,
            source_span=SpanRecord(
                text="Python", field_source="description", start_char=0, end_char=6
            ),
        )
        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = (
                [skill_with_esco],
                {"extraction_failed": False, "tokens_used": 100, "cost_usd": 0.002, "latency_ms": 500},
            )
            out = agent.process(event)
        assert out.payload["taxonomy_coverage"] >= 0
        assert out.payload["extraction_cost_usd"] == 0.002
        assert out.payload["llm_call_logged"] is True
        assert len(out.payload["skills"]) == 1
        assert out.payload["skills"][0]["skill_name"] == "Python"

    def test_process_payload_has_skills_extraction_alert_when_metadata_alert_true(self) -> None:
        """When extract_skills returns alert_skills_extraction True, payload has skills_extraction_alert."""
        event = EventEnvelope(
            correlation_id="test-alert",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-alert",
                "title": "Engineer",
                "company": "Acme",
                "description": "Python required.",
                "source": "test",
                "external_id": "job-alert",
            },
        )
        agent = SkillsExtractionAgent()
        with patch("agents.skills_extraction.agent.extract_skills") as mock_skills:
            mock_skills.return_value = (
                [],
                {"extraction_failed": True, "alert_skills_extraction": True, "tokens_used": 0, "cost_usd": 0.0},
            )
            out = agent.process(event)
        assert out.payload.get("skills_extraction_alert") is True
