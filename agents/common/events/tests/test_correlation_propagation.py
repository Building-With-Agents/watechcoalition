"""
Correlation ID propagation test for Ingestion -> Normalization handoff.

This test uses synthetic events only. Once Bryan's Ingestion -> Normalization
handoff is in place, this assertion can be run against the real chain.
"""

from __future__ import annotations

from datetime import datetime

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.events import ingest_batch_payload
from agents.normalization.events import normalization_complete_payload


def test_correlation_id_propagates_from_ingest_batch_to_normalization_complete() -> None:
    """
    Assert that correlation_id on a NormalizationComplete event is identical
    to the correlation_id on the IngestBatch event (propagation rule for the chain).
    """
    shared_correlation_id = "chain-correlation-001"
    base_ts = datetime(2025, 1, 1, 0, 0, 0)

    ingest_payload = ingest_batch_payload(
        batch_id="batch-1",
        source="harness",
        region_id="us",
        total_fetched=10,
        staged_count=10,
        dedup_count=0,
        error_count=0,
    )
    ingest_event = EventEnvelope(
        event_id="e1",
        correlation_id=shared_correlation_id,
        agent_id="ingestion-agent",
        timestamp=base_ts,
        schema_version="1.0",
        payload=ingest_payload,
    )

    norm_payload = normalization_complete_payload(
        batch_id="batch-1",
        region_id="us",
        normalized_count=10,
        quarantined_count=0,
        normalization_status="success",
    )
    norm_event = EventEnvelope(
        event_id="e2",
        correlation_id=shared_correlation_id,
        agent_id="normalization-agent",
        timestamp=base_ts,
        schema_version="1.0",
        payload=norm_payload,
    )

    assert ingest_event.correlation_id == norm_event.correlation_id, (
        "correlation_id must propagate unchanged from IngestBatch to NormalizationComplete"
    )
    assert ingest_event.correlation_id == shared_correlation_id
    assert norm_event.correlation_id == shared_correlation_id
