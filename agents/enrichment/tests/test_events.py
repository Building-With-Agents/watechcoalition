"""Tests for enrichment event builders."""

from __future__ import annotations

from agents.enrichment.resolvers.events import (
    RECORD_ENRICHED_SCHEMA_VERSION,
    build_record_enriched_event,
)

_EXPECTED_KEYS = frozenset(
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


def _sample_metrics() -> dict:
    return {
        "temporal_period_distribution": {"agentic_era": 3, "unknown": 2},
        "borderplex_subregion_distribution": {"el_paso": 4, "unknown": 1},
        "duplicate_count": 1,
        "soc_classified_count": 4,
        "naics_classified_count": 3,
    }


def test_record_enriched_event_type_and_counts() -> None:
    enriched_count = 5
    spam = 2
    flagged = 3
    total_records = enriched_count + spam + flagged
    m = _sample_metrics()

    event = build_record_enriched_event(
        correlation_id="corr-abc",
        batch_id="batch-001",
        enriched_count=enriched_count,
        spam_rejected_count=spam,
        flagged_for_review_count=flagged,
        **m,
    )

    assert set(event.payload.keys()) == _EXPECTED_KEYS
    assert event.payload["event_type"] == "RecordEnriched"
    assert event.payload["record_enriched_schema_version"] == RECORD_ENRICHED_SCHEMA_VERSION
    assert event.payload["batch_id"] == "batch-001"
    assert event.payload["enriched_count"] == enriched_count
    assert event.payload["spam_rejected_count"] == spam
    assert event.payload["flagged_for_review_count"] == flagged
    assert event.payload["duplicate_count"] == 1
    assert event.payload["soc_classified_count"] == 4
    assert event.payload["naics_classified_count"] == 3

    assert (
        event.payload["enriched_count"]
        + event.payload["spam_rejected_count"]
        + event.payload["flagged_for_review_count"]
        == total_records
    )


def test_correlation_id_unchanged() -> None:
    m = _sample_metrics()
    event = build_record_enriched_event(
        correlation_id="run-xyz-99",
        batch_id="b",
        enriched_count=0,
        spam_rejected_count=0,
        flagged_for_review_count=0,
        **m,
    )
    assert event.correlation_id == "run-xyz-99"


def test_agent_id_enrichment() -> None:
    m = _sample_metrics()
    event = build_record_enriched_event(
        correlation_id="c",
        batch_id="b",
        enriched_count=0,
        spam_rejected_count=0,
        flagged_for_review_count=0,
        **m,
    )
    assert event.agent_id == "enrichment-agent"
