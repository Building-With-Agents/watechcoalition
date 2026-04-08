"""Tests for SkillsExtractionAgent — Week 4 hybrid bridge."""

from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import delete, inspect

from agents.common.data_store.database import check_db_connection, get_engine, session_scope
from agents.common.data_store.models import ExtractedIntelligence, NormalizedJob
from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord
from agents.skills_extraction.agent import ExtractionWorkItem, SkillsExtractionAgent


def _integration_db_available() -> bool:
    if not os.getenv("PYTHON_DATABASE_URL"):
        return False
    if not check_db_connection():
        return False
    try:
        tables = set(inspect(get_engine()).get_table_names(schema="dbo"))
    except Exception:
        return False
    return {"normalized_jobs", "extracted_intelligence"}.issubset(tables)


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


def _make_work_item(
    job_id: int,
    *,
    title: str | None = None,
    company: str = "Acme",
    description: str = "Python required.",
) -> ExtractionWorkItem:
    title = title or f"Engineer {job_id}"
    return ExtractionWorkItem(
        job_id=job_id,
        posting_id=None,
        normalized_job_id=job_id,
        title=title,
        company=company,
        job_record=JobRecord(
            source="test",
            external_id=f"job-{job_id}",
            title=title,
            company=company,
            description=description,
        ),
    )


def _normalize_saved_results(saved_results: list[Any]) -> list[dict[str, Any]]:
    """Strip execution-mode-only timing so serial and parallel outputs compare cleanly."""
    normalized: list[dict[str, Any]] = []
    for result in saved_results:
        extraction_metadata = dict(result.extraction_metadata or {})
        extraction_metadata.pop("extraction_duration_ms", None)
        normalized.append(
            {
                "job_id": result.work_item.job_id,
                "posting_id": result.work_item.posting_id,
                "normalized_job_id": result.work_item.normalized_job_id,
                "title": result.work_item.title,
                "company": result.work_item.company,
                "skills": list(result.skills),
                "tools": [tool.model_dump() for tool in result.tools],
                "tasks": list(result.tasks),
                "responsibilities": list(result.responsibilities),
                "context": list(result.context),
                "extraction_status": result.extraction_status,
                "extraction_tokens_used": result.extraction_tokens_used,
                "extraction_cost_usd": result.extraction_cost_usd,
                "alert_skills_extraction": result.alert_skills_extraction,
                "extraction_warnings": list(result.extraction_warnings),
                "extraction_metadata": extraction_metadata,
                "persisted_extraction_version": result.persisted_extraction_version,
                "persisted_extraction_model": result.persisted_extraction_model,
            }
        )
    return normalized


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
            patch(
                "agents.skills_extraction.agent.time.perf_counter",
                side_effect=[10.0, 10.01, 10.02, 10.27, 10.28, 10.29],
            ),
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

    def test_process_parallel_batch_respects_configured_concurrency(self) -> None:
        """Inter-job parallel mode should cap in-flight work by the configured semaphore."""
        work_items = [_make_work_item(i) for i in range(1, 6)]
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=store,
        )
        in_flight = 0
        max_in_flight = 0

        def _success_meta() -> dict[str, Any]:
            return {
                "success": True,
                "extraction_failed": False,
                "extraction_status": "success",
                "error_reason": None,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "latency_ms": 0,
                "extraction_warnings": [],
                "alert_skills_extraction": False,
                "provider": "azure-openai",
                "model": "skills-deployment",
                "context_signals": [],
                "tasks": [],
                "responsibilities": [],
                "dimension_metas": {},
                "pass2_llm_calls": 3,
                "pass2_llm_dimensions": ["tasks", "responsibilities", "skills"],
                "pass2_dimensions_succeeded": ["tasks", "responsibilities", "skills"],
                "pass2_dimensions_failed": [],
            }

        async def _fake_extract(item: ExtractionWorkItem) -> tuple[list, list, dict[str, Any], bool]:
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            try:
                await asyncio.sleep(0.01)
                return [], [], _success_meta(), True
            finally:
                in_flight -= 1

        with (
            patch.dict(
                os.environ,
                {
                    "SKILLS_EXTRACTION_PARALLEL": "1",
                    "SKILLS_EXTRACTION_CONCURRENCY": "2",
                    "SKILLS_EXTRACTION_DELAY": "9",
                    "SKILLS_EXTRACTION_CHUNK_SIZE": "1",
                    "SKILLS_EXTRACTION_CHUNK_COOLDOWN": "9",
                },
                clear=False,
            ),
            patch.object(
                agent,
                "_extract_work_item_no_taxonomy_async",
                new=AsyncMock(side_effect=_fake_extract),
            ),
            patch("agents.skills_extraction.agent.time.sleep") as m_sleep,
        ):
            out = agent.process(
                EventEnvelope(
                    correlation_id="test-parallel-concurrency",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-parallel-concurrency"},
                )
            )

        assert max_in_flight == 2
        assert len(store.saved_results) == 5
        assert out.payload["failed_count"] == 0
        assert m_sleep.call_count == 0

    def test_process_parallel_batch_isolates_job_level_failures(self) -> None:
        """One unexpected job failure should not abort the rest of the parallel batch."""
        work_items = [_make_work_item(i) for i in range(1, 4)]
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=store,
        )

        def _success_meta() -> dict[str, Any]:
            return {
                "success": True,
                "extraction_failed": False,
                "extraction_status": "success",
                "error_reason": None,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "latency_ms": 0,
                "extraction_warnings": [],
                "alert_skills_extraction": False,
                "provider": "azure-openai",
                "model": "skills-deployment",
                "context_signals": [],
                "tasks": [],
                "responsibilities": [],
                "dimension_metas": {},
                "pass2_llm_calls": 3,
                "pass2_llm_dimensions": ["tasks", "responsibilities", "skills"],
                "pass2_dimensions_succeeded": ["tasks", "responsibilities", "skills"],
                "pass2_dimensions_failed": [],
            }

        async def _fake_extract(item: ExtractionWorkItem) -> tuple[list, list, dict[str, Any], bool]:
            await asyncio.sleep(0)
            if item.job_id == 2:
                raise RuntimeError("job exploded")
            return [], [], _success_meta(), True

        with (
            patch.dict(
                os.environ,
                {"SKILLS_EXTRACTION_PARALLEL": "1", "SKILLS_EXTRACTION_CONCURRENCY": "2"},
                clear=False,
            ),
            patch.object(
                agent,
                "_extract_work_item_no_taxonomy_async",
                new=AsyncMock(side_effect=_fake_extract),
            ),
        ):
            out = agent.process(
                EventEnvelope(
                    correlation_id="test-parallel-job-failure",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-parallel-job-failure"},
                )
            )

        statuses = {record["job_id"]: record["extraction_status"] for record in out.payload["records"]}
        assert statuses[1] == "success"
        assert statuses[2] == "failed"
        assert statuses[3] == "success"
        assert out.payload["failed_count"] == 1
        assert len(store.saved_results) == 3

    def test_process_parallel_batch_falls_back_to_serial_when_loop_running(self) -> None:
        """Embedded callers with a running loop should use the serial fallback path."""
        event = EventEnvelope(
            correlation_id="test-loop-fallback",
            agent_id="normalization-agent",
            payload={
                "event_type": "NormalizationComplete",
                "batch_id": "batch-loop-fallback",
                "title": "Engineer",
                "company": "Acme",
                "description": "Python required.",
                "source": "test",
                "external_id": "job-loop-fallback",
            },
        )
        agent = SkillsExtractionAgent()
        with (
            patch.dict(os.environ, {"SKILLS_EXTRACTION_PARALLEL": "1"}, clear=False),
            patch("agents.skills_extraction.agent.asyncio.get_running_loop", return_value=object()),
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

    def test_process_serial_mode_respects_legacy_throttles(self) -> None:
        """Serial fallback should still honor the deprecated chunk and delay env vars."""
        work_items = [_make_work_item(i) for i in range(1, 4)]
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=store,
        )

        with (
            patch.dict(
                os.environ,
                {
                    "SKILLS_EXTRACTION_PARALLEL": "0",
                    "SKILLS_EXTRACTION_CONCURRENCY": "99",
                    "SKILLS_EXTRACTION_DELAY": "1.25",
                    "SKILLS_EXTRACTION_CHUNK_SIZE": "2",
                    "SKILLS_EXTRACTION_CHUNK_COOLDOWN": "7.5",
                },
                clear=False,
            ),
            _patch_skills_extraction_pass2_llm(
                skills_list=[],
                skills_meta={"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0},
            ),
            patch("agents.skills_extraction.agent.time.sleep") as m_sleep,
        ):
            out = agent.process(
                EventEnvelope(
                    correlation_id="test-serial-throttles",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-serial-throttles"},
                )
            )

        assert [call.args[0] for call in m_sleep.call_args_list] == [1.25, 7.5, 1.25]
        assert out.payload["failed_count"] == 0
        assert len(store.saved_results) == 3

    def test_process_parallel_batch_matches_serial_output(self) -> None:
        """Parallel and serial batch execution should match result-for-result on extraction output."""
        from agents.common.types import (
            ResponsibilityRecord,
            SkillRecord,
            SpanRecord,
            TaskRecord,
            TaxonomyResult,
        )

        work_items = [
            _make_work_item(11, description="Design APIs with Python and mentor engineers."),
            _make_work_item(12, description="Design APIs with Python and mentor engineers."),
        ]
        serial_store = _FakeStore()
        parallel_store = _FakeStore()
        serial_agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=serial_store,
        )
        parallel_agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=parallel_store,
        )
        skill = SkillRecord(
            skill_name="Python",
            type="Technical",
            confidence=0.9,
            source_span=SpanRecord(text="Python", field_source="description", start_char=0, end_char=6),
        )
        task = TaskRecord(
            task_description="Design APIs",
            task_category="technical",
            seniority_signal="senior",
            confidence=0.88,
            source_span=SpanRecord(
                text="Design APIs",
                field_source="description",
                start_char=0,
                end_char=11,
            ),
        )
        responsibility = ResponsibilityRecord(
            responsibility_description="Mentor engineers",
            scope="team",
            requires_ai_competency=False,
            confidence=0.84,
            source_span=SpanRecord(
                text="mentor engineers",
                field_source="description",
                start_char=24,
                end_char=40,
            ),
        )
        taxonomy = TaxonomyResult(
            original_label="Python",
            esco_uri="http://data.europa.eu/esco/skill/python",
            is_genai_extension=False,
            resolution_step=2,
        )
        ctx_meta = {
            "tokens_used": 0,
            "cost_usd": 0.0,
            "latency_ms": 0,
            "extraction_failed": False,
            "provider": "pattern-matching",
            "model": "none",
            "extraction_metadata": {"context_signals": 0},
        }
        tasks_meta = {
            "success": True,
            "extraction_failed": False,
            "tokens_used": 17,
            "cost_usd": 0.0012,
            "latency_ms": 40,
            "provider": "azure-openai",
            "model": "tasks-deployment",
            "extraction_metadata": {"dimension": "tasks"},
        }
        responsibilities_meta = {
            "success": True,
            "extraction_failed": False,
            "tokens_used": 19,
            "cost_usd": 0.0015,
            "latency_ms": 45,
            "provider": "azure-openai",
            "model": "responsibilities-deployment",
            "extraction_metadata": {"dimension": "responsibilities"},
        }
        skills_meta = {
            "success": True,
            "extraction_failed": False,
            "tokens_used": 50,
            "cost_usd": 0.001,
            "latency_ms": 40,
            "provider": "azure-openai",
            "model": "skills-deployment",
            "extraction_metadata": {"dimension": "skills"},
        }
        event = EventEnvelope(
            correlation_id="test-serial-vs-parallel",
            agent_id="normalization-agent",
            payload={"event_type": "NormalizationComplete", "batch_id": "batch-serial-vs-parallel"},
        )

        with (
            patch("agents.skills_extraction.agent.extract_context", return_value=([], ctx_meta)),
            patch("agents.skills_extraction.agent.extract_tasks", return_value=([task], tasks_meta)),
            patch(
                "agents.skills_extraction.agent.extract_tasks_async",
                new=AsyncMock(return_value=([task], tasks_meta)),
            ),
            patch(
                "agents.skills_extraction.agent.extract_responsibilities",
                return_value=([responsibility], responsibilities_meta),
            ),
            patch(
                "agents.skills_extraction.agent.extract_responsibilities_async",
                new=AsyncMock(return_value=([responsibility], responsibilities_meta)),
            ),
            patch(
                "agents.skills_extraction.agent.extract_skills_no_taxonomy",
                return_value=([skill], skills_meta),
            ),
            patch(
                "agents.skills_extraction.agent.extract_skills_no_taxonomy_async",
                new=AsyncMock(return_value=([skill], skills_meta)),
            ),
            patch(
                "agents.skills_extraction.agent.resolve_taxonomy_batch",
                return_value=[taxonomy],
            ),
        ):
            with patch.dict(os.environ, {"SKILLS_EXTRACTION_PARALLEL": "0"}, clear=False):
                serial_out = serial_agent.process(event)
            with patch.dict(
                os.environ,
                {"SKILLS_EXTRACTION_PARALLEL": "1", "SKILLS_EXTRACTION_CONCURRENCY": "2"},
                clear=False,
            ):
                parallel_out = parallel_agent.process(event)

        assert serial_out.payload == parallel_out.payload
        assert _normalize_saved_results(serial_store.saved_results) == _normalize_saved_results(
            parallel_store.saved_results
        )

    def test_process_parallel_batch_short_circuits_empty_text_jobs(self) -> None:
        """Jobs with no normalized text should fail fast without consuming async extractor calls."""
        work_items = [
            _make_work_item(21, description=""),
            _make_work_item(22, description="Python required."),
        ]
        store = _FakeStore()
        agent = SkillsExtractionAgent(
            work_item_loader=_FakeLoader(work_items),
            extraction_store=store,
        )

        with (
            patch.dict(
                os.environ,
                {"SKILLS_EXTRACTION_PARALLEL": "1", "SKILLS_EXTRACTION_CONCURRENCY": "2"},
                clear=False,
            ),
            patch(
                "agents.skills_extraction.agent.extract_context",
                return_value=(
                    [],
                    {
                        "tokens_used": 0,
                        "cost_usd": 0.0,
                        "latency_ms": 0,
                        "extraction_failed": False,
                        "provider": "pattern-matching",
                        "model": "none",
                        "extraction_metadata": {},
                    },
                ),
            ),
            patch(
                "agents.skills_extraction.agent.extract_tasks_async",
                new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}})),
            ) as m_tasks,
            patch(
                "agents.skills_extraction.agent.extract_responsibilities_async",
                new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}})),
            ) as m_resp,
            patch(
                "agents.skills_extraction.agent.extract_skills_no_taxonomy_async",
                new=AsyncMock(return_value=([], {"extraction_failed": False, "tokens_used": 0, "cost_usd": 0.0, "latency_ms": 10, "extraction_metadata": {}, "model": "skills-deployment"})),
            ) as m_skills,
        ):
            out = agent.process(
                EventEnvelope(
                    correlation_id="test-empty-text-parallel",
                    agent_id="normalization-agent",
                    payload={"event_type": "NormalizationComplete", "batch_id": "batch-empty-text-parallel"},
                )
            )

        statuses = {record["job_id"]: record["extraction_status"] for record in out.payload["records"]}
        assert statuses[21] == "failed"
        assert statuses[22] == "success"
        assert m_tasks.await_count == 1
        assert m_resp.await_count == 1
        assert m_skills.await_count == 1
        assert len(store.saved_results) == 2
