"""Enrichment Agent outbound event builders."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope

# Increment when ``RecordEnriched`` payload gains backward-incompatible fields.
RECORD_ENRICHED_SCHEMA_VERSION = 2


def build_record_enriched_event(
    correlation_id: str,
    batch_id: str,
    *,
    enriched_count: int,
    spam_rejected_count: int,
    flagged_for_review_count: int,
    temporal_period_distribution: dict[str, int],
    borderplex_subregion_distribution: dict[str, int],
    duplicate_count: int,
    soc_classified_count: int,
    naics_classified_count: int,
) -> EventEnvelope:
    """Build one ``RecordEnriched`` event for the whole batch (Week 5 counts + Week 6 metrics)."""
    return EventEnvelope(
        correlation_id=correlation_id,
        agent_id="enrichment-agent",
        payload={
            "event_type": "RecordEnriched",
            "record_enriched_schema_version": RECORD_ENRICHED_SCHEMA_VERSION,
            "batch_id": batch_id,
            "enriched_count": enriched_count,
            "spam_rejected_count": spam_rejected_count,
            "flagged_for_review_count": flagged_for_review_count,
            "temporal_period_distribution": dict(temporal_period_distribution),
            "borderplex_subregion_distribution": dict(borderplex_subregion_distribution),
            "duplicate_count": duplicate_count,
            "soc_classified_count": soc_classified_count,
            "naics_classified_count": naics_classified_count,
        },
    )
