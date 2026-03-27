"""Tests for enrichment event builders."""

from __future__ import annotations

from agents.enrichment.resolvers.events import build_record_enriched_event


def test_record_enriched_event_type_and_counts() -> None:
    enriched_count = 5
    spam = 2
    flagged = 3
    total_records = enriched_count + spam + flagged

    event = build_record_enriched_event(
        correlation_id="corr-abc",
        batch_id="batch-001",
        enriched_count=enriched_count,
        spam_rejected_count=spam,
        flagged_for_review_count=flagged,
    )

    assert set(event.payload.keys()) == {
        "event_type",
        "batch_id",
        "enriched_count",
        "spam_rejected_count",
        "flagged_for_review_count",
        "spam_tier_counts",
    }
    assert event.payload["spam_tier_counts"] == {
        "clean": 0,
        "flagged": 0,
        "rejected": 0,
        "uncertain": 0,
    }
    assert event.payload["event_type"] == "RecordEnriched"
    assert event.payload["batch_id"] == "batch-001"
    assert event.payload["enriched_count"] == enriched_count
    assert event.payload["spam_rejected_count"] == spam
    assert event.payload["flagged_for_review_count"] == flagged

    assert (
        event.payload["enriched_count"]
        + event.payload["spam_rejected_count"]
        + event.payload["flagged_for_review_count"]
        == total_records
    )


def test_correlation_id_unchanged() -> None:
    event = build_record_enriched_event(
        correlation_id="run-xyz-99",
        batch_id="b",
        enriched_count=0,
        spam_rejected_count=0,
        flagged_for_review_count=0,
    )
    assert event.correlation_id == "run-xyz-99"


def test_agent_id_enrichment() -> None:
    event = build_record_enriched_event(
        correlation_id="c",
        batch_id="b",
        enriched_count=0,
        spam_rejected_count=0,
        flagged_for_review_count=0,
    )
    assert event.agent_id == "enrichment-agent"
