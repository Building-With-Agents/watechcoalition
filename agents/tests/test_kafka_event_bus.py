"""Tests for Commit 4 Kafka event bus behavior."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import KafkaEventBus, KafkaHandlerExecutionError
from agents.normalization.events import normalization_complete_payload
from agents.tests.message_bus_stream_fixtures import generate_ingest_batches


@dataclass(frozen=True)
class _FakeKafkaRecord:
    """Minimal consumed record shape used by KafkaEventBus tests."""

    topic: str
    partition: int
    offset: int
    value: bytes
    key: bytes | None = None


class _FakeKafkaBroker:
    """Shared in-memory topic storage for fake producer/consumer clients."""

    def __init__(self) -> None:
        self._topics: dict[str, list[_FakeKafkaRecord]] = defaultdict(list)

    def append(self, topic: str, value: bytes, *, key: bytes | None = None) -> _FakeKafkaRecord:
        stream = self._topics[topic]
        record = _FakeKafkaRecord(
            topic=topic,
            partition=0,
            offset=len(stream),
            value=value,
            key=key,
        )
        stream.append(record)
        return record

    def read(self, topic: str, offset: int, limit: int) -> Sequence[_FakeKafkaRecord]:
        if limit <= 0:
            return []
        stream = self._topics[topic]
        return stream[offset : offset + limit]


class _FakeKafkaProducer:
    """In-memory producer used for deterministic Kafka bus tests."""

    def __init__(self, broker: _FakeKafkaBroker) -> None:
        self._broker = broker

    def send(self, topic: str, value: bytes, *, key: bytes | None = None) -> _FakeKafkaRecord:
        return self._broker.append(topic, value, key=key)


class _FakeKafkaConsumer:
    """In-memory consumer with poll/commit/seek semantics for replay tests."""

    def __init__(self, broker: _FakeKafkaBroker, *, topic: str) -> None:
        self._broker = broker
        self._topic = topic
        self._next_offset = 0
        self._committed_offset = 0

    def poll(
        self,
        *,
        timeout_ms: int = 0,
        max_records: int | None = None,
    ) -> Sequence[_FakeKafkaRecord]:
        del timeout_ms
        limit = max_records if max_records is not None else 1
        records = self._broker.read(self._topic, self._next_offset, limit)
        self._next_offset += len(records)
        return records

    def commit(self, message: _FakeKafkaRecord) -> None:
        self._committed_offset = max(self._committed_offset, message.offset + 1)

    def seek(self, message: _FakeKafkaRecord) -> None:
        self._next_offset = message.offset


def _build_bus(topic: str = "exp004:kafka-test") -> KafkaEventBus:
    broker = _FakeKafkaBroker()
    return KafkaEventBus(
        producer=_FakeKafkaProducer(broker),
        consumer=_FakeKafkaConsumer(broker, topic=topic),
        topic=topic,
    )


def _drain_bus(bus: KafkaEventBus, *, max_iterations: int = 10_000) -> None:
    """Consume until no more replay/new entries are available."""
    for _ in range(max_iterations):
        consumed = bus.consume_available(max_events=256)
        if consumed == 0:
            return
    raise AssertionError("bus did not drain within iteration guard")


def test_kafka_round_trip_serialization() -> None:
    """Round-trip all envelope fields for contract consistency with other buses."""
    event = EventEnvelope(
        correlation_id="corr-1",
        agent_id="ingestion-agent",
        payload={"event_type": "IngestBatch", "batch_id": "batch-1"},
    )

    serialized = KafkaEventBus.serialize_envelope(event)
    decoded = KafkaEventBus.deserialize_envelope(serialized)

    assert decoded.event_id == event.event_id
    assert decoded.correlation_id == event.correlation_id
    assert decoded.agent_id == event.agent_id
    assert decoded.schema_version == event.schema_version
    assert decoded.timestamp == event.timestamp
    assert decoded.payload == event.payload


def test_kafka_harness_equivalent_stream_preserves_correlation() -> None:
    bus = _build_bus(topic="exp004:kafka-harness")
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

    _drain_bus(bus)

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
        "queue_depth": 0,
        "in_flight": 0,
    }


def test_kafka_crash_and_replay_preserves_event_id_set() -> None:
    bus = _build_bus(topic="exp004:kafka-crash")
    ingest_events = list(generate_ingest_batches(count=1000, seed=42))
    published_event_ids = [event.event_id for event in ingest_events]
    first_run_processed_event_ids: list[str] = []
    replay_processed_event_ids: list[str] = []
    replay_mode = False
    seen = 0

    def _crash_once_handler(event: EventEnvelope) -> None:
        nonlocal seen
        if replay_mode:
            replay_processed_event_ids.append(event.event_id)
            return

        seen += 1
        if seen == 500:
            raise RuntimeError("simulated crash at event index 500")
        first_run_processed_event_ids.append(event.event_id)

    bus.subscribe(
        "IngestBatch",
        _crash_once_handler,
        subscriber_id="normalization-agent",
    )

    for event in ingest_events:
        bus.publish(event)

    crash_triggered = False
    while True:
        try:
            consumed = bus.consume_available(
                max_events=1,
                stop_on_handler_error=True,
            )
        except KafkaHandlerExecutionError:
            crash_triggered = True
            break

        if consumed == 0:
            break

    assert crash_triggered is True
    assert len(first_run_processed_event_ids) == 499
    assert bus.counters["in_flight"] == 0

    replay_mode = True
    _drain_bus(bus)

    combined_ids = first_run_processed_event_ids + replay_processed_event_ids
    replay_count = len(replay_processed_event_ids)
    replay_completeness = (len(combined_ids) / len(published_event_ids)) * 100

    assert replay_count == 501
    assert replay_completeness == 100.0
    assert len(combined_ids) == len(published_event_ids)
    assert set(combined_ids) == set(published_event_ids)
    assert bus.counters == {
        "published_events": 1000,
        "delivered_events": 1000,
        "handler_failures": 1,
        "queue_depth": 0,
        "in_flight": 0,
    }
