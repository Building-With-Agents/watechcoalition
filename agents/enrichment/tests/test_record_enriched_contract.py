"""Interface stability: ``RecordEnriched`` batch vs single-record shapes."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.enrichment.agent import EnrichmentAgent
from agents.enrichment.resolvers.events import RECORD_ENRICHED_SCHEMA_VERSION, build_record_enriched_event
from agents.enrichment.resolvers.record_enriched_contract import (
    RECORD_ENRICHED_BATCH_PAYLOAD_KEYS,
    RECORD_ENRICHED_DEDUP_BLOCK_KEYS,
    RECORD_ENRICHED_SINGLE_RECORD_CORE_KEYS,
)


def test_batch_build_record_enriched_exact_top_level_keys() -> None:
    ev = build_record_enriched_event(
        correlation_id="c",
        batch_id="b",
        enriched_count=1,
        spam_rejected_count=0,
        flagged_for_review_count=0,
        temporal_period_distribution={},
        borderplex_subregion_distribution={},
        duplicate_count=0,
        soc_classified_count=0,
        naics_classified_count=0,
    )
    assert set(ev.payload.keys()) == RECORD_ENRICHED_BATCH_PAYLOAD_KEYS
    assert ev.payload["record_enriched_schema_version"] == RECORD_ENRICHED_SCHEMA_VERSION


def test_batch_dedup_block_key_set_and_numeric_types() -> None:
    ev = build_record_enriched_event(
        correlation_id="c",
        batch_id="b",
        enriched_count=0,
        spam_rejected_count=0,
        flagged_for_review_count=0,
        temporal_period_distribution={},
        borderplex_subregion_distribution={},
        duplicate_count=0,
        soc_classified_count=0,
        naics_classified_count=0,
        dedup_stub_count=0,
        dedup_rows_with_duplicate_cluster_id=0,
        dedup_rows_with_matched_job_posting_id=0,
    )
    d = ev.payload["dedup"]
    assert set(d.keys()) == RECORD_ENRICHED_DEDUP_BLOCK_KEYS
    assert isinstance(d["cosine_threshold"], float)
    assert isinstance(d["rolling_window_days"], int)
    for k in (
        "stub_count",
        "rows_with_duplicate_cluster_id",
        "rows_with_matched_job_posting_id",
    ):
        assert isinstance(d[k], int)


def test_single_record_core_keys_subset_and_types(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTHON_DATABASE_URL", raising=False)
    skills_event = EventEnvelope(
        correlation_id="contract-single-1",
        agent_id="skills-extraction-agent",
        payload={
            "event_type": "SkillsExtracted",
            "batch_id": "b-contract",
            "posting_id": 1,
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "skills": [{"name": "Python", "type": "Technical", "confidence": 0.9}],
        },
    )
    agent = EnrichmentAgent()
    out = agent.process(skills_event)
    keys = set(out.payload.keys())
    assert keys >= RECORD_ENRICHED_SINGLE_RECORD_CORE_KEYS
    assert out.payload["event_type"] == "RecordEnriched"
    assert isinstance(out.payload["quality_score"], float)
    assert isinstance(out.payload["quality_components"], dict)
    assert isinstance(out.payload["skills"], list)
    assert "record_enriched_schema_version" not in out.payload


def test_batch_process_rollups_dedup_stub_from_posting_row() -> None:
    payload = {
        "event_type": "SkillsExtracted",
        "batch_id": "b-dedup-stub",
        "posting_id": 99,
        "records": [
            {
                "posting_id": 1,
                "title": "T",
                "company": "C",
                "skills": [],
                "is_spam": False,
                "stub": True,
            }
        ],
    }
    event = EventEnvelope(
        correlation_id="contract-batch-dedup",
        agent_id="skills-extraction-agent",
        payload=payload,
    )
    agent = EnrichmentAgent()
    with (
        patch.object(EnrichmentAgent, "enrich_record", return_value={"ok": True}),
        patch("agents.enrichment.agent.resolve_sector", return_value=None),
    ):
        out = agent.process(event)
    assert out.payload["dedup"]["stub_count"] == 1
    assert set(out.payload.keys()) == RECORD_ENRICHED_BATCH_PAYLOAD_KEYS
