"""Enrichment Agent outbound event builders."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope


def build_record_enriched_event(
    correlation_id: str,
    batch_id: str,
    *,
    enriched_count: int,
    spam_rejected_count: int,
    flagged_for_review_count: int,
) -> EventEnvelope:
    """Build one ``RecordEnriched`` event for the whole batch (Week 5 lite contract, issue #87)."""
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="enrichment-agent",
        payload={
            "event_type": "RecordEnriched",
            "batch_id": batch_id,
            "enriched_count": enriched_count,
            "spam_rejected_count": spam_rejected_count,
            "flagged_for_review_count": flagged_for_review_count,
        },
    )
