"""Tests for EnrichmentAgent — Week 2 stub."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.resolvers.events import build_record_enriched_event


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

    def test_process_emits_record_enriched(
        self, skills_event: EventEnvelope
    ) -> None:
        """Output event_type is RecordEnriched."""
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
        ):
            out = agent.process(skills_event)
        assert out.payload["event_type"] == "RecordEnriched"
        assert out.agent_id == "enrichment-agent"

    def test_process_passes_skills_into_enrich_record(
        self, skills_event: EventEnvelope
    ) -> None:
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

    def test_graceful_degradation_when_enrich_record_raises(
        self, skills_event: EventEnvelope
    ) -> None:
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

    def test_record_enriched_payload_includes_new_job_postings_columns(
        self, skills_event: EventEnvelope
    ) -> None:
        """Week 5 columns flow through enrich_record into the batch envelope."""

        def build_with_records(*args: Any, **kwargs: Any) -> EventEnvelope:
            ev = build_record_enriched_event(*args, **kwargs)
            recs = kwargs.get("enriched_records", [])
            ev.payload = {**dict(ev.payload), "records": list(recs)}
            return ev

        payload = {
            **skills_event.payload,
            "is_spam": False,
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
        company_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        mock_enriched = {
            "posting_id": payload.get("posting_id"),
            "title": payload.get("title"),
            "company": payload.get("company"),
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
        agent = EnrichmentAgent()
        with (
            patch.object(EnrichmentAgent, "enrich_record", return_value=mock_enriched),
            patch("agents.enrichment.agent.resolve_sector", return_value=None),
            patch(
                "agents.enrichment.agent.build_record_enriched_event",
                side_effect=build_with_records,
            ),
        ):
            out = agent.process(event)

        assert out.payload["event_type"] == "RecordEnriched"
        records = out.payload["records"]
        assert len(records) == 1
        rec = records[0]
        assert rec["soc_code"] == "15-1252.00"
        assert rec["naics_code"] == "541511"
        assert rec["temporal_period"] == "agentic_era"
        assert rec["borderplex_subregion"] == "el_paso"
        assert rec["is_duplicate"] is False
