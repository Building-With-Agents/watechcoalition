"""Enrichment Agent outbound event builders."""

from __future__ import annotations

from typing import Any

from agents.common.event_envelope import EventEnvelope


def build_record_enriched_event(
    correlation_id: str,
    batch_id: str,
    enriched_records: list[Any],
    spam_rejected: int,
    flagged_count: int,
) -> EventEnvelope:
    """Build one ``RecordEnriched`` event for the whole batch."""
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="enrichment-agent",
        payload={
            "event_type": "RecordEnriched",
            "batch_id": batch_id,
            "enriched_count": len(enriched_records),
            "spam_rejected_count": spam_rejected,
            "flagged_for_review_count": flagged_count,
        },
    )
