"""Checklist-aligned event bus contract tests for Week 3."""

from __future__ import annotations

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.message_bus import (
    ComparisonScenario,
    FakeKafkaBroker,
    FakeKafkaConsumer,
    FakeKafkaProducer,
    FakeRedisStreamsClient,
    InProcessEventBus,
    KafkaEventBus,
    RedisStreamsEventBus,
    TransportCandidate,
    compare_transport_candidates,
    run_transport_comparison,
)


def _build_kafka_bus(topic: str) -> KafkaEventBus:
    broker = FakeKafkaBroker()
    return KafkaEventBus(
        producer=FakeKafkaProducer(broker),
        consumer=FakeKafkaConsumer(broker, topic=topic),
        topic=topic,
    )


@pytest.mark.parametrize(
    ("transport", "bus_factory"),
    [
        ("in_process", InProcessEventBus),
        (
            "redis_streams",
            lambda: RedisStreamsEventBus(
                client=FakeRedisStreamsClient(),
                stream_name="exp004:event-bus-test-redis",
                group_name="exp004:event-bus-test-redis-group",
                consumer_name="exp004:event-bus-test-redis-consumer",
            ),
        ),
        ("kafka", lambda: _build_kafka_bus("exp004:event-bus-test-kafka")),
    ],
)
def test_event_bus_publish_subscribe_round_trip(
    transport: str,
    bus_factory,
) -> None:
    bus = bus_factory()
    received: list[str] = []

    bus.subscribe(
        "IngestBatch",
        lambda event: received.append(event.correlation_id),
        subscriber_id="normalization-agent",
    )
    bus.publish(
        EventEnvelope(
            correlation_id=f"{transport}-corr",
            agent_id="ingestion-agent",
            payload={"event_type": "IngestBatch", "batch_id": f"{transport}-batch"},
        )
    )

    consume = getattr(bus, "consume_available", None)
    if callable(consume):
        consume(max_events=10)

    assert received == [f"{transport}-corr"]
    assert bus.counters["published_events"] == 1
    assert bus.counters["delivered_events"] == 1
    assert bus.counters["handler_failures"] == 0


def test_event_bus_delivery_guarantees_hold_for_replay_capable_transports() -> None:
    results = compare_transport_candidates(
        [
            TransportCandidate(
                transport="in_process",
                backend="in_memory",
                factory=InProcessEventBus,
            ),
            TransportCandidate(
                transport="redis_streams",
                backend="fake_redis",
                factory=lambda: RedisStreamsEventBus(
                    client=FakeRedisStreamsClient(),
                    stream_name="exp004:event-bus-guarantee-redis",
                    group_name="exp004:event-bus-guarantee-redis-group",
                    consumer_name="exp004:event-bus-guarantee-redis-consumer",
                ),
            ),
            TransportCandidate(
                transport="kafka",
                backend="fake_kafka",
                factory=lambda: _build_kafka_bus("exp004:event-bus-guarantee-kafka"),
            ),
        ],
        scenario=ComparisonScenario(event_count=1000, crash_at=500),
    )

    by_transport = {result.transport: result for result in results}

    assert all(result.correctness_passed is True for result in results)
    assert all(result.published_events == 2000 for result in results)
    assert all(result.delivered_events == 2000 for result in results)
    assert by_transport["in_process"].crash_replay_complete is None
    assert by_transport["redis_streams"].crash_replay_complete is True
    assert by_transport["redis_streams"].replay_completeness_pct == 100.0
    assert by_transport["kafka"].crash_replay_complete is True
    assert by_transport["kafka"].replay_completeness_pct == 100.0
    assert all(result.producer_crash_loss_count == 500 for result in results)
    assert all(result.producer_resume_recovered_count == 500 for result in results)
    assert all(result.producer_resume_final_loss_count == 0 for result in results)
    assert all(result.producer_resume_complete is True for result in results)


def test_event_bus_1000_event_throughput_is_measured() -> None:
    result = run_transport_comparison(
        InProcessEventBus(),
        transport="in_process",
        backend="in_memory",
        scenario=ComparisonScenario(
            event_count=1000,
            include_crash_replay=False,
            crash_at=500,
        ),
        producer_crash_bus_factory=InProcessEventBus,
    )

    assert result.input_events == 1000
    assert result.latency_sample_count == 1000
    assert result.throughput_publish_events_per_sec > 0
    assert result.throughput_e2e_events_per_sec > 0
    assert result.producer_crash_loss_count == 500
    assert result.producer_resume_recovered_count == 500
