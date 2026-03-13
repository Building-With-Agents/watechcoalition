"""Tests for Commit 2 in-process event bus behavior."""

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import InProcessEventBus
from agents.normalization.events import normalization_complete_payload
from agents.tests.message_bus_stream_fixtures import generate_ingest_batches


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
    ingest_events = list(generate_ingest_batches(count=1000, seed=42))
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
