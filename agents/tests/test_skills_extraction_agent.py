"""Tests for SkillsExtractionAgent — Week 4 hybrid bridge."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

from agents.common.event_envelope import EventEnvelope
from agents.common.types import JobRecord
from agents.skills_extraction.agent import ExtractionWorkItem, SkillsExtractionAgent


class TestSkillsExtractionAgent:
    """Verify agent_id, health_check (incl. failure modes), and process behaviour."""

    def test_agent_id(self) -> None:
        agent = SkillsExtractionAgent()
        assert agent.agent_id == "skills-extraction-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when both the fixture and DB-backed mode are available."""
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
        agent = SkillsExtractionAgent()
        agent.health_check()  # pre-load fixture
        out = agent.process(normalization_event)
        skills = out.payload["skills"]
        assert isinstance(skills, list)
        assert len(skills) > 0
        for skill in skills:
            assert "name" in skill
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

    def test_process_emits_batch_payload_for_inline_job_list(self) -> None:
        """Batch payloads should produce aggregate metrics and per-record summaries."""
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
