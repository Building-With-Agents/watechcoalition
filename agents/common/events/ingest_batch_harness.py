"""
EXP-004 test harness: deterministic generator of synthetic IngestBatch events.

Used to produce 1,000 identical events for event-bus experiments (in-process,
Redis, Kafka). Harness only — no bus implementation or throughput/crash tests.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import datetime, timedelta

from agents.common.event_envelope import EventEnvelope
from agents.ingestion.events import ingest_batch_payload

# Keys required in an IngestBatch payload (must match ingest_batch_payload()).
INGEST_BATCH_PAYLOAD_KEYS = frozenset({
    "event_type",
    "batch_id",
    "source",
    "region_id",
    "total_fetched",
    "staged_count",
    "dedup_count",
    "error_count",
})

# Types expected for each payload key (str or int).
INGEST_BATCH_PAYLOAD_STR_KEYS = frozenset({"event_type", "batch_id", "source", "region_id"})
INGEST_BATCH_PAYLOAD_INT_KEYS = frozenset({"total_fetched", "staged_count", "dedup_count", "error_count"})


def generate_synthetic_ingest_batches(
    count: int = 1000,
    seed: int = 42,
) -> Iterator[EventEnvelope]:
    """
    Yield exactly `count` deterministic IngestBatch events.

    Same (count, seed) always produces the same events in the same order.
    """
    base_ts = datetime(2025, 1, 1, 0, 0, 0)
    correlation_id = f"harness-{seed}"

    for i in range(count):
        event_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"harness-{seed}-{i}"))
        timestamp = base_ts + timedelta(seconds=i)
        batch_id = f"harness-batch-{seed}-{i}"
        # Deterministic counts from seed and index
        total_fetched = (seed + i) % 100 + 1
        staged_count = (seed + i) % 50 + 1
        dedup_count = (seed + i) % 10
        error_count = (seed + i) % 5

        payload = ingest_batch_payload(
            batch_id=batch_id,
            source="harness",
            region_id="us",
            total_fetched=total_fetched,
            staged_count=staged_count,
            dedup_count=dedup_count,
            error_count=error_count,
        )
        yield EventEnvelope(
            event_id=event_id,
            correlation_id=correlation_id,
            agent_id="ingestion_agent",
            timestamp=timestamp,
            schema_version="1.0",
            payload=payload,
        )


def is_valid_ingest_batch_envelope(event: EventEnvelope) -> bool:
    """
    Return True if the event has valid envelope and IngestBatch payload structure.

    Checks: envelope fields set, payload has all required keys and correct types,
    and event_type == "IngestBatch".
    """
    try:
        assert_valid_ingest_batch_envelope(event)
        return True
    except ValueError:
        return False


def assert_valid_ingest_batch_envelope(event: EventEnvelope) -> None:
    """
    Raise ValueError with a clear message if envelope or payload is invalid.

    Valid: EventEnvelope with agent_id, schema_version, and payload containing
    all IngestBatch keys with correct types and event_type == "IngestBatch".
    """
    if not event.agent_id:
        raise ValueError("Envelope missing agent_id")
    if not event.schema_version:
        raise ValueError("Envelope missing schema_version")
    if event.agent_id != "ingestion_agent":
        raise ValueError(f"Expected agent_id 'ingestion_agent', got {event.agent_id!r}")

    payload = event.payload
    if not isinstance(payload, dict):
        raise ValueError(f"Payload must be a dict, got {type(payload).__name__}")

    missing = INGEST_BATCH_PAYLOAD_KEYS - set(payload)
    if missing:
        raise ValueError(f"Payload missing required keys: {sorted(missing)}")

    if payload.get("event_type") != "IngestBatch":
        raise ValueError(
            f"Payload event_type must be 'IngestBatch', got {payload.get('event_type')!r}"
        )

    for key in INGEST_BATCH_PAYLOAD_STR_KEYS:
        if not isinstance(payload[key], str):
            raise ValueError(
                f"Payload key {key!r} must be str, got {type(payload[key]).__name__}"
            )

    for key in INGEST_BATCH_PAYLOAD_INT_KEYS:
        if not isinstance(payload[key], int):
            raise ValueError(
                f"Payload key {key!r} must be int, got {type(payload[key]).__name__}"
            )
