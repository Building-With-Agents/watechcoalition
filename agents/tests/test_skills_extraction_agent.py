"""Tests for SkillsExtractionAgent — Week 4 hybrid bridge."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete

from agents.common.data_store.database import check_db_connection, session_scope
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob
from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord
from agents.skills_extraction.agent import ExtractionWorkItem, SkillsExtractionAgent


def _integration_db_available() -> bool:
    if not os.getenv("PYTHON_DATABASE_URL"):
        return False
    return check_db_connection()


@contextmanager
def _patch_skills_extraction_pass2_llm(
    *,
    skills_list: list[Any],
    skills_meta: dict[str, Any],
) -> Any:
    """Mock Pass 2 LLM paths; Pass 1 (context + tools) stays real."""
    with (
        patch("agents.skills_extraction.agent.extract_context") as m_ctx,
        patch("agents.skills_extraction.agent.extract_tasks") as m_tasks,
        patch("agents.skills_extraction.agent.extract_tasks_async", new_callable=AsyncMock) as m_tasks_async,
        patch("agents.skills_extraction.agent.extract_responsibilities") as m_resp,
        patch(
            "agents.skills_extraction.agent.extract_responsibilities_async",
            new_callable=AsyncMock,
        ) as m_resp_async,
        patch("agents.skills_extraction.agent.extract_skills_no_taxonomy") as m_skills,
        patch(
            "agents.skills_extraction.agent.extract_skills_no_taxonomy_async",
            new_callable=AsyncMock,
        ) as m_skills_async,
    ):
        m_ctx.return_value = (
            [],
            {
                "tokens_used": 0,
                "cost_usd": 0.0,
                "extraction_failed": False,
                "extraction_metadata": {},
            },
        )
        m_tasks.return_value = (
            [],
            {
                "extraction_failed": False,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "extraction_metadata": {},
            },
        )
        m_tasks_async.return_value = m_tasks.return_value
        m_resp.return_value = (
            [],
            {
                "extraction_failed": False,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "extraction_metadata": {},
            },
        )
        m_resp_async.return_value = m_resp.return_value
        m_skills.return_value = (skills_list, skills_meta)
        m_skills_async.return_value = (skills_list, skills_meta)
        yield


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

    def test_process_emits_skills_extracted(self, normalization_event: EventEnvelope) -> None:
        """Output event_type is SkillsExtracted."""
        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        with _patch_skills_extraction_pass2_llm(
            skills_list=[],
            skills_meta={"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0},
        ):
            out = agent.process(normalization_event)
        assert out.payload["event_type"] == "SkillsExtracted"
        assert out.payload["tasks_count"] == 0
        assert out.payload["responsibilities_count"] == 0
        assert out.payload["context_count"] == 0
        assert out.payload.get("context_signals_count") == 0
        assert out.agent_id == "skills-extraction-agent"

    def test_process_returns_fixture_skills(self, normalization_event: EventEnvelope) -> None:
        """Output contains a non-empty skills list with expected keys."""
        from agents.common.types import SkillRecord, SpanRecord, TaxonomyResult

        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        mock_skill = SkillRecord(
            skill_name="Python",
            type="Technical",
            confidence=0.9,
            source_span=SpanRecord(text="Python", field_source="description", start_char=0, end_char=6),
        )
        mock_taxonomy = TaxonomyResult(original_label="Python", esco_uri=None, resolution_step=6)
        with (
            _patch_skills_extraction_pass2_llm(
                skills_list=[mock_skill],
                skills_meta={"extraction_failed": False, "tokens_used": 50, "cost_usd": 0.0},
            ),
            patch(
                "agents.skills_extraction.agent.resolve_taxonomy_batch",
                return_value=[mock_taxonomy],
            ),
        ):
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
        with _patch_skills_extraction_pass2_llm(
            skills_list=[],
            skills_meta={"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0},
        ):
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

    @pytest.mark.skipif(not _integration_db_available(), reason="requires reachable PostgreSQL")
    def test_process_emits_batch_payload_for_inline_job_list(self) -> None:
        """Batch payloads should produce aggregate metrics and per-record summaries."""
        # ExtractionStore persists to extracted_intelligence with FK to normalized_jobs.
        # Session-scoped truncates in other test modules leave normalized_jobs empty; seed
        # parent rows for the inline normalized_job_id values used below.
        run_id = "pytest-batch-inline-2"
        with session_scope() as session:
            session.execute(delete(ExtractedIntelligence).where(ExtractedIntelligence.normalized_job_id.in_((11, 12))))
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
        with _patch_skills_extraction_pass2_llm(
            skills_list=[],
            skills_meta={"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0},
        ):
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

        with _patch_skills_extraction_pass2_llm(
            skills_list=[],
            skills_meta={"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0},
        ):
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
        """When skills extraction returns skills and metadata, payload has cost and coverage."""
        from agents.common.types import SkillRecord, SpanRecord, TaxonomyResult

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
            skill_name="Python",
            type="Technical",
            confidence=0.9,
            source_span=SpanRecord(text="Python", field_source="description", start_char=0, end_char=6),
        )
        mock_taxonomy = TaxonomyResult(
            original_label="Python",
            esco_uri="http://data.europa.eu/esco/skill/abc",
            is_genai_extension=False,
            resolution_step=2,
        )
        agent = SkillsExtractionAgent()
        with (
            _patch_skills_extraction_pass2_llm(
                skills_list=[skill_with_esco],
                skills_meta={
                    "extraction_failed": False,
                    "tokens_used": 100,
                    "cost_usd": 0.002,
                    "latency_ms": 500,
                },
            ),
            patch(
                "agents.skills_extraction.agent.resolve_taxonomy_batch",
                return_value=[mock_taxonomy],
            ),
        ):
            out = agent.process(event)
        assert out.payload["taxonomy_coverage"] >= 0
        assert out.payload["extraction_cost_usd"] == 0.002
        assert out.payload["llm_call_logged"] is True
        assert len(out.payload["skills"]) == 1
        assert out.payload["skills"][0]["skill_name"] == "Python"

    def test_process_payload_has_skills_extraction_alert_when_metadata_alert_true(self) -> None:
        """When extract_skills_no_taxonomy signals rate-limit alert, payload reflects it."""
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
        with _patch_skills_extraction_pass2_llm(
            skills_list=[],
            skills_meta={
                "extraction_failed": True,
                "alert_skills_extraction": True,
                "tokens_used": 0,
                "cost_usd": 0.0,
            },
        ):
            out = agent.process(event)
        assert out.payload.get("skills_extraction_alert") is True

    def test_process_parallel_path_degrades_when_async_dimension_raises(self) -> None:
        """One failed async dimension should not cancel the others for the same job."""
        from agents.common.types import SkillRecord, SpanRecord, TaxonomyResult

        event = EventEnvelope(
            correlation_id="test-parallel-degraded",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-parallel-degraded",
                "title": "Platform Engineer",
                "company": "Acme",
                "description": "Python required for platform work.",
                "source": "test",
                "external_id": "job-parallel-degraded",
            },
        )
        agent = SkillsExtractionAgent()
        skill = SkillRecord(
            skill_name="Python",
            type="Technical",
            confidence=0.9,
            source_span=SpanRecord(
                text="Python",
                field_source="description",
                start_char=0,
                end_char=6,
            ),
        )
        with (
            patch.dict(os.environ, {"SKILLS_EXTRACTION_PARALLEL": "1"}, clear=False),
            patch("agents.skills_extraction.agent.extract_context", return_value=([], {"tokens_used": 0, "cost_usd": 0.0, "latency_ms": 5, "extraction_failed": False, "extraction_metadata": {}})),
            patch("agents.skills_extraction.agent.extract_tasks_async", new=AsyncMock(side_effect=RuntimeError("tasks boom"))),
            patch(
                "agents.skills_extraction.agent.extract_responsibilities_async",
                new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 7, "cost_usd": 0.001, "latency_ms": 50, "extraction_metadata": {}})),
            ),
            patch(
                "agents.skills_extraction.agent.extract_skills_no_taxonomy_async",
                new=AsyncMock(return_value=([skill], {"extraction_failed": False, "tokens_used": 13, "cost_usd": 0.002, "latency_ms": 70, "model": "skills-deployment"})),
            ),
            patch(
                "agents.skills_extraction.agent.resolve_taxonomy_batch",
                return_value=[TaxonomyResult(original_label="Python", resolution_step=6)],
            ),
        ):
            out = agent.process(event)

        assert out.payload["failed_count"] == 0
        assert out.payload["skills_count"] == 1
        assert out.payload["tasks_count"] == 0
        assert out.payload["records"][0]["extraction_status"] == "degraded"

    def test_process_parallel_path_uses_wall_clock_latency_not_sum(self) -> None:
        """Parallel pass-2 latency should reflect wall-clock gather time, not sum of dimension latencies."""

        @dataclass
        class _FakeLoader:
            work_items: list[ExtractionWorkItem]

            def load(self, event: EventEnvelope) -> list[ExtractionWorkItem]:
                return self.work_items

        class _FakeStore:
            def __init__(self) -> None:
                self.saved_results = []

            def save(self, results) -> None:
                self.saved_results = list(results)

        work_item = ExtractionWorkItem(
            job_id=501,
            posting_id=None,
            normalized_job_id=501,
            title="Engineer",
            company="Acme",
            job_record=JobRecord(
                source="test",
                external_id="job-501",
                title="Engineer",
                company="Acme",
                description="Python and SQL required.",
            ),
        )
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader([work_item]),
            extraction_store=store,
        )

        with (
            patch.dict(os.environ, {"SKILLS_EXTRACTION_PARALLEL": "1"}, clear=False),
            patch("agents.skills_extraction.agent.extract_context", return_value=([], {"tokens_used": 0, "cost_usd": 0.0, "latency_ms": 40, "extraction_failed": False, "extraction_metadata": {}})),
            patch("agents.skills_extraction.agent.extract_tasks_async", new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 10, "cost_usd": 0.001, "latency_ms": 200, "extraction_metadata": {}}))),
            patch("agents.skills_extraction.agent.extract_responsibilities_async", new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 11, "cost_usd": 0.001, "latency_ms": 300, "extraction_metadata": {}}))),
            patch("agents.skills_extraction.agent.extract_skills_no_taxonomy_async", new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 12, "cost_usd": 0.001, "latency_ms": 500, "extraction_metadata": {}, "model": "skills-deployment"}))),
            patch("agents.skills_extraction.agent.time.perf_counter", side_effect=[100.0, 100.25]),
        ):
            agent.process(
                EventEnvelope(
                    correlation_id="test-wall-clock",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-wall-clock"},
                )
            )

        assert len(store.saved_results) == 1
        extraction_meta = store.saved_results[0].extraction_metadata or {}
        assert extraction_meta["extraction_duration_ms"] == 290

    def test_process_serial_fallback_when_parallel_disabled(self) -> None:
        """Disabling the env flag should keep the existing sync extractor path."""
        event = EventEnvelope(
            correlation_id="test-serial-fallback",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-serial-fallback",
                "title": "Engineer",
                "company": "Acme",
                "description": "Python required.",
                "source": "test",
                "external_id": "job-serial-fallback",
            },
        )
        agent = SkillsExtractionAgent()
        with (
            patch.dict(os.environ, {"SKILLS_EXTRACTION_PARALLEL": "0"}, clear=False),
            patch("agents.skills_extraction.agent.extract_tasks", return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}})) as m_tasks,
            patch("agents.skills_extraction.agent.extract_responsibilities", return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}})) as m_resp,
            patch("agents.skills_extraction.agent.extract_skills_no_taxonomy", return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}})) as m_skills,
            patch("agents.skills_extraction.agent.extract_tasks_async", new=AsyncMock(side_effect=AssertionError("async path should not run"))),
            patch("agents.skills_extraction.agent.extract_responsibilities_async", new=AsyncMock(side_effect=AssertionError("async path should not run"))),
            patch("agents.skills_extraction.agent.extract_skills_no_taxonomy_async", new=AsyncMock(side_effect=AssertionError("async path should not run"))),
        ):
            out = agent.process(event)

        assert out.payload["event_type"] == "SkillsExtracted"
        assert m_tasks.called
        assert m_resp.called
        assert m_skills.called
