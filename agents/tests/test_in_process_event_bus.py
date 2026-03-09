"""Tests for Commit 2 in-process event bus behavior."""

from __future__ import annotations

import random
from collections.abc import Iterable

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import InProcessEventBus
from agents.ingestion.events import ingest_batch_payload
from agents.normalization.events import normalization_complete_payload

try:
    from agents.common.events.ingest_batch_harness import (  # pragma: no cover
        generate_synthetic_ingest_batches as _harness_generator,
    )
except ImportError:  # pragma: no cover
    _harness_generator = None


def _fixture_synthetic_ingest_batches(
    *, count: int = 1000, seed: int = 42
) -> Iterable[EventEnvelope]:
    """Deterministic fallback stream until the shared harness module is merged."""
    rng = random.Random(seed)

    for index in range(count):
        total_fetched = rng.randint(20, 120)
        dedup_count = rng.randint(0, 10)
        error_count = rng.randint(0, 5)
        staged_count = max(total_fetched - dedup_count - error_count, 0)
        batch_id = f"batch-{index:04d}-{rng.randint(1000, 9999)}"
        region_id = f"region-{rng.randint(1, 8):02d}"
        correlation_id = f"corr-{seed}-{index:04d}-{rng.randint(10000, 99999)}"

        yield EventEnvelope(
            correlation_id=correlation_id,
            agent_id="ingestion-agent",
            payload=ingest_batch_payload(
                batch_id=batch_id,
                source="synthetic-harness-fixture",
                region_id=region_id,
                total_fetched=total_fetched,
                staged_count=staged_count,
                dedup_count=dedup_count,
                error_count=error_count,
            ),
        )


def _generate_ingest_batches(
    *, count: int = 1000, seed: int = 42
) -> Iterable[EventEnvelope]:
    """Use the shared harness generator when available, otherwise fallback fixture."""
    if _harness_generator is not None:
        yield from _harness_generator(count=count, seed=seed)
        return
    yield from _fixture_synthetic_ingest_batches(count=count, seed=seed)


def test_in_process_publish_subscribe_synchronous_delivery() -> None:
    bus = InProcessEventBus()
    received: list[EventEnvelope] = []

    bus.subscribe(
        "IngestBatch",
        lambda event: received.append(event),
        subscriber_id="normalization-agent",
    )

    event = EventEnvelope(
        correlation_id="c-1",
        agent_id="ingestion-agent",
        payload={"event_type": "IngestBatch", "batch_id": "batch-1"},
    )
    bus.publish(event)

    assert len(received) == 1
    assert received[0].correlation_id == "c-1"
    assert bus.counters == {
        "published_events": 1,
        "delivered_events": 1,
        "handler_failures": 0,
    }


def test_in_process_tracks_handler_failures_and_continues_delivery() -> None:
    bus = InProcessEventBus()
    delivered: list[str] = []

    def _failing_handler(_: EventEnvelope) -> None:
        raise RuntimeError("boom")

    def _healthy_handler(event: EventEnvelope) -> None:
        delivered.append(event.correlation_id)

    bus.subscribe("IngestBatch", _failing_handler, subscriber_id="normalization-agent")
    bus.subscribe("IngestBatch", _healthy_handler, subscriber_id="analytics-agent")

    bus.publish(
        EventEnvelope(
            correlation_id="c-2",
            agent_id="ingestion-agent",
            payload={"event_type": "IngestBatch", "batch_id": "batch-2"},
        )
    )

    assert delivered == ["c-2"]
    assert bus.counters == {
        "published_events": 1,
        "delivered_events": 1,
        "handler_failures": 1,
    }


def test_harness_equivalent_stream_preserves_correlation_end_to_end() -> None:
    bus = InProcessEventBus()
    ingest_events = list(_generate_ingest_batches(count=1000, seed=42))
    normalization_seen_correlation_ids: list[str] = []
    emitted_completions: list[EventEnvelope] = []

    def _normalization_handler(event: EventEnvelope) -> None:
        normalization_seen_correlation_ids.append(event.correlation_id)
        completion = EventEnvelope(
            correlation_id=event.correlation_id,
            agent_id="normalization-agent",
            payload=normalization_complete_payload(
                batch_id=str(event.payload.get("batch_id", "")),
                region_id=str(event.payload.get("region_id", "")),
                normalized_count=int(event.payload.get("staged_count", 0)),
                quarantined_count=int(event.payload.get("error_count", 0)),
                normalization_status="success",
            ),
        )
        bus.publish(completion)

    def _completion_handler(event: EventEnvelope) -> None:
        emitted_completions.append(event)

    bus.subscribe(
        "IngestBatch",
        _normalization_handler,
        subscriber_id="normalization-agent",
    )
    bus.subscribe(
        "NormalizationComplete",
        _completion_handler,
        subscriber_id="analytics-agent",
    )

    for event in ingest_events:
        bus.publish(event)

    published_correlation_ids = [event.correlation_id for event in ingest_events]
    completion_correlation_ids = [event.correlation_id for event in emitted_completions]

    assert len(normalization_seen_correlation_ids) == 1000
    assert len(emitted_completions) == 1000
    assert normalization_seen_correlation_ids == published_correlation_ids
    assert completion_correlation_ids == published_correlation_ids
    assert bus.counters == {
        "published_events": 2000,
        "delivered_events": 2000,
        "handler_failures": 0,
    }
