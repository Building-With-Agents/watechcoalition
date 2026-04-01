"""Tests for EnrichmentAgent — Pair D batch enrichment and RecordEnriched (issue #87).

Issue #96 acceptance: "classifier unavailable → EnrichmentDegraded alert" is not implemented on
EnrichmentAgent (no such event). Upstream sets ``is_spam=None`` → flagged tier; no alert emission here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent

_RECORD_ENRICHED_KEYS = frozenset(
    {
        "event_type",
        "record_enriched_schema_version",
        "batch_id",
        "enriched_count",
        "spam_rejected_count",
        "flagged_for_review_count",
        "temporal_period_distribution",
        "borderplex_subregion_distribution",
        "duplicate_count",
        "soc_classified_count",
        "naics_classified_count",
    }
)


class TestEnrichmentAgent:
    """Verify agent_id, health_check, and process behaviour."""

    def test_agent_id(self) -> None:
        agent = EnrichmentAgent()
        assert agent.agent_id == "enrichment-agent"

    def test_health_check_ok(self) -> None:
        """Returns 'ok' when the fixture file exists and is valid JSON."""
        agent = EnrichmentAgent()
        result = agent.health_check()
        assert result["status"] == "ok"

    def test_health_check_down_missing_file(self) -> None:
        """Returns 'down' when the fixture file does not exist."""
        agent = EnrichmentAgent()
        fake_path = Path("/nonexistent/fixture_enriched.json")
        with patch("agents.enrichment.agent._FIXTURE_PATH", fake_path):
            result = agent.health_check()
        assert result["status"] == "down"

    def test_process_emits_record_enriched(self, skills_event: EventEnvelope) -> None:
        """Output event_type is RecordEnriched with Week 5 counts + Week 6 metrics."""
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"
        assert set(out.payload.keys()) == _RECORD_ENRICHED_KEYS

    def test_process_passes_skills_into_enrich_record(self, skills_event: EventEnvelope) -> None:
        """Skills from the upstream event are passed on the posting dict to enrich_record."""
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

    def test_spam_rejected_skips_resolution(self, skills_event: EventEnvelope) -> None:
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

    def test_flagged_record_skips_resolution(self, skills_event: EventEnvelope) -> None:
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

    def test_record_enriched_payload_fields(self, skills_event: EventEnvelope) -> None:
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

    def test_graceful_degradation_when_enrich_record_raises(self, skills_event: EventEnvelope) -> None:
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

    def test_batch_multi_record_aggregates_counts(self, skills_event: EventEnvelope) -> None:
        """One RecordEnriched aggregates all SkillsExtracted.records (issue #87)."""
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

    def test_spam_score_thresholds_precedence_over_absent_is_spam(self, skills_event: EventEnvelope) -> None:
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

    def test_enrich_record_receives_merged_job_columns_from_batch_payload(self, skills_event: EventEnvelope) -> None:
        """Optional job_postings columns on the batch payload merge into each row."""
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

        assert set(out.payload.keys()) == _RECORD_ENRICHED_KEYS
        assert out.payload["enriched_count"] == 1
        assert len(captured) == 1
        rec = captured[0]
        assert rec["soc_code"] == "15-1252.00"
        assert rec["naics_code"] == "541511"
        assert rec["temporal_period"] == "agentic_era"
        assert rec["borderplex_subregion"] == "el_paso"
        assert rec["is_duplicate"] is False

    def test_enrich_record_return_can_include_job_postings_shape(self, skills_event: EventEnvelope) -> None:
        """enrich_record output may carry PR #97-style fields (city/state/country, UUID)."""
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

    def test_process_uses_session_scope_when_db_available(self, skills_event: EventEnvelope) -> None:
        """When check_db_connection is true, enrich_record receives the scoped Session."""
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

    def test_process_passes_none_session_when_db_unavailable(self, skills_event: EventEnvelope) -> None:
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

    def test_record_enriched_week6_aggregates_distributions(self, skills_event: EventEnvelope) -> None:
        """Week 6: temporal/borderplex distributions and classification counts on enriched rows."""
        payload = {
            **skills_event.payload,
            "batch_id": "batch-week6",
            "records": [
                {
                    "posting_id": 1,
                    "title": "Dev",
                    "company": "A",
                    "skills": [],
                    "is_spam": False,
                },
                {
                    "posting_id": 2,
                    "title": "Analyst",
                    "company": "B",
                    "skills": [],
                    "is_spam": False,
                },
            ],
        }
        event = EventEnvelope(
            correlation_id=skills_event.correlation_id,
            agent_id=skills_event.agent_id,
            payload=payload,
        )

        n = 0

        def enrich_side_effect(posting: dict, session: object) -> dict:
            nonlocal n
            n += 1
            row: dict = {"ok": True, "borderplex_subregion": "el_paso" if n == 1 else "unknown"}
            if n == 1:
                row["temporal_period"] = "agentic_era"
                row["soc_code"] = "15-1252"
                row["naics_code"] = "541511"
                row["is_duplicate"] = False
            else:
                row["temporal_period"] = "agentic_era"
                row["is_duplicate"] = True
            return row

        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", side_effect=enrich_side_effect),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(event)

        assert out.payload["enriched_count"] == 2
        assert out.payload["duplicate_count"] == 1
        assert out.payload["soc_classified_count"] == 1
        assert out.payload["naics_classified_count"] == 1
        assert out.payload["temporal_period_distribution"] == {"agentic_era": 2}
        assert out.payload["borderplex_subregion_distribution"] == {"el_paso": 1, "unknown": 1}

    def test_process_falls_back_when_session_scope_raises(self, skills_event: EventEnvelope) -> None:
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

    def test_process_e2e_extraction_spam_resolution_record_enriched(self) -> None:
        """E2E: SkillsExtracted ``records`` → spam/flag gates → real ``enrich_record`` → ``RecordEnriched`` (#96).

        Does not mock ``enrich_record`` logic; only DB boundary and resolver I/O are patched.
        Rejected and flagged rows must not call ``resolve_company`` / ``resolve_location``.
        """
        correlation_id = "e2e-issue-96"
        batch_id = "batch-e2e-96"
        skills = [{"name": "Python", "type": "Technical", "confidence": 0.92}]
        payload: dict[str, Any] = {
            "event_type": "SkillsExtracted",
            "batch_id": batch_id,
            "records": [
                {
                    "posting_id": 901,
                    "title": "Rejected posting",
                    "company": "SpamCo",
                    "location": "Internet",
                    "skills": skills,
                    "is_spam": True,
                },
                {
                    "posting_id": 902,
                    "title": "Flagged posting",
                    "company": "MaybeCo",
                    "location": "Unknown",
                    "skills": skills,
                    "is_spam": None,
                },
                {
                    "posting_id": 903,
                    "title": "Software Engineer",
                    "company": "GoodCorp",
                    "location": "El Paso, TX",
                    "skills": skills,
                    "is_spam": False,
                    "quality_score": 0.88,
                    "extraction_confidence": 0.91,
                    "taxonomy_coverage": 0.84,
                    "seniority": "mid",
                    "role_classification": "Software Engineering",
                    "soc_code": "15-1252",
                    "naics_code": "541511",
                    "temporal_period": "agentic_era",
                    "borderplex_subregion": "el_paso",
                    "is_duplicate": False,
                },
            ],
        }
        event = EventEnvelope(
            correlation_id=correlation_id,
            agent_id="skills-extraction-agent",
            payload=payload,
        )

        agent = EnrichmentAgent()
        enriched_from_record: list[dict[str, Any]] = []

        def spy_enrich_record(posting: dict[str, Any], session: object) -> dict[str, Any]:
            out = EnrichmentAgent.enrich_record(agent, posting, session)
            enriched_from_record.append(out)
            return out

        agent.enrich_record = spy_enrich_record  # type: ignore[method-assign]

        loc_uuid = "550e8400-e29b-41d4-a716-446655440096"
        with (
            patch("agents.enrichment.agent.check_db_connection", return_value=False),
            patch("agents.enrichment.agent.resolve_company", return_value=(4242, 0.97)) as mock_company,
            patch(
                "agents.enrichment.agent.resolve_location",
                return_value=(loc_uuid, 0.94, "El Paso, TX", "el_paso"),
            ) as mock_location,
            patch("agents.enrichment.agent.resolve_sector", return_value="sector-e2e") as mock_sector,
        ):
            out = agent.process(event)

        mock_company.assert_called_once_with("GoodCorp", None)
        mock_location.assert_called_once_with("El Paso, TX", None)
        mock_sector.assert_called_once_with("Software Engineering", session=None)

        assert len(enriched_from_record) == 1
        enriched = enriched_from_record[0]
        assert enriched["posting_id"] == 903
        assert enriched["company_id"] == 4242
        assert enriched["location_id"] == loc_uuid
        assert enriched["borderplex_subregion"] == "el_paso"
        assert "field_confidence" in enriched
        assert enriched["overall_confidence"] > 0

        assert out.correlation_id == correlation_id
        assert out.payload["event_type"] == "RecordEnriched"
        assert set(out.payload.keys()) == _RECORD_ENRICHED_KEYS
        assert out.payload["batch_id"] == batch_id
        assert out.payload["enriched_count"] == 1
        assert out.payload["spam_rejected_count"] == 1
        assert out.payload["flagged_for_review_count"] == 1
        assert out.payload["temporal_period_distribution"] == {"agentic_era": 1}
        assert out.payload["borderplex_subregion_distribution"] == {"el_paso": 1}
        assert out.payload["duplicate_count"] == 0
        assert out.payload["soc_classified_count"] == 1
        assert out.payload["naics_classified_count"] == 1
