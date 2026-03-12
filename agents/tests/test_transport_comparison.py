"""Tests for normalized transport comparison utilities."""

from __future__ import annotations

from agents.common.message_bus import (
    ComparisonScenario,
    FakeKafkaBroker,
    FakeKafkaConsumer,
    FakeKafkaProducer,
    FakeRedisStreamsClient,
    InProcessEventBus,
    KafkaEventBus,
    ProducerCrashResult,
    RedisStreamsEventBus,
    TransportCandidate,
    build_transport_candidates,
    compare_transport_candidates,
    format_results_markdown_table,
    measure_producer_crash,
    results_to_rows,
    run_transport_comparison,
)


def _build_kafka_bus(topic: str) -> KafkaEventBus:
    broker = FakeKafkaBroker()
    return KafkaEventBus(
        producer=FakeKafkaProducer(broker),
        consumer=FakeKafkaConsumer(broker, topic=topic),
        topic=topic,
    )


def test_run_transport_comparison_in_process_returns_normalized_metrics() -> None:
    result = run_transport_comparison(
        InProcessEventBus(),
        transport="in_process",
        backend="in_memory",
        scenario=ComparisonScenario(
            event_count=50,
            include_crash_replay=False,
        ),
        producer_crash_bus_factory=InProcessEventBus,
    )

    assert result.transport == "in_process"
    assert result.backend == "in_memory"
    assert result.input_events == 50
    assert result.published_events == 100
    assert result.delivered_events == 100
    assert result.handler_failures == 0
    assert result.queue_depth is None
    assert result.in_flight is None
    assert result.crash_replay_complete is None
    assert result.replay_completeness_pct is None
    assert result.producer_crash_published_before_crash == 50
    assert result.producer_crash_delivered_before_crash == 50
    assert result.producer_crash_loss_count == 0
    assert result.producer_resume_recovered_count == 0
    assert result.producer_resume_final_loss_count == 0
    assert result.producer_resume_complete is True
    assert result.latency_sample_count == 50
    assert result.latency_p50_ms is not None
    assert result.latency_p95_ms is not None
    assert result.latency_p99_ms is not None
    assert result.throughput_publish_events_per_sec > 0
    assert result.throughput_e2e_events_per_sec > 0
    assert result.correctness_passed is True


def test_compare_transport_candidates_builds_rows_for_all_buses() -> None:
    scenario = ComparisonScenario(
        event_count=25,
        include_crash_replay=True,
        crash_at=10,
    )
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
                    stream_name="exp004:compare-redis",
                    group_name="exp004:compare-redis-group",
                    consumer_name="exp004:compare-redis-consumer",
                ),
            ),
            TransportCandidate(
                transport="kafka",
                backend="fake_kafka",
                factory=lambda: _build_kafka_bus("exp004:compare-kafka"),
            ),
        ],
        scenario=scenario,
    )

    assert len(results) == 3

    by_transport = {result.transport: result for result in results}
    assert by_transport["in_process"].crash_replay_complete is None
    assert by_transport["in_process"].producer_crash_published_before_crash == 10
    assert by_transport["in_process"].producer_crash_loss_count == 15
    assert by_transport["in_process"].producer_resume_recovered_count == 15
    assert by_transport["in_process"].producer_resume_final_loss_count == 0
    assert by_transport["in_process"].producer_resume_complete is True
    assert by_transport["redis_streams"].crash_replay_complete is True
    assert by_transport["redis_streams"].replay_completeness_pct == 100.0
    assert by_transport["redis_streams"].producer_crash_delivered_before_crash == 10
    assert by_transport["redis_streams"].producer_crash_loss_count == 15
    assert by_transport["redis_streams"].producer_resume_recovered_count == 15
    assert by_transport["redis_streams"].producer_resume_final_loss_count == 0
    assert by_transport["redis_streams"].producer_resume_complete is True
    assert by_transport["redis_streams"].queue_depth == 0
    assert by_transport["redis_streams"].in_flight == 0
    assert by_transport["kafka"].crash_replay_complete is True
    assert by_transport["kafka"].replay_completeness_pct == 100.0
    assert by_transport["kafka"].producer_crash_delivered_before_crash == 10
    assert by_transport["kafka"].producer_crash_loss_count == 15
    assert by_transport["kafka"].producer_resume_recovered_count == 15
    assert by_transport["kafka"].producer_resume_final_loss_count == 0
    assert by_transport["kafka"].producer_resume_complete is True
    assert by_transport["kafka"].queue_depth == 0
    assert by_transport["kafka"].in_flight == 0

    rows = results_to_rows(results)
    assert rows[0]["transport"] in {"in_process", "redis_streams", "kafka"}
    assert all(row["published_events"] == 50 for row in rows)
    assert all(row["delivered_events"] == 50 for row in rows)
    assert all(row["handler_failures"] == 0 for row in rows)
    assert all(row["producer_resume_final_loss_count"] == 0 for row in rows)

    table = format_results_markdown_table(results)
    assert "throughput_publish_events_per_sec" in table
    assert "producer_crash_loss_count" in table
    assert "redis_streams" in table
    assert "fake_kafka" in table


def test_build_transport_candidates_defaults_to_three_way_fake_comparison() -> None:
    candidates = build_transport_candidates()

    assert [candidate.transport for candidate in candidates] == [
        "in_process",
        "redis_streams",
        "kafka",
    ]
    assert [candidate.backend for candidate in candidates] == [
        "in_memory",
        "fake_redis",
        "fake_kafka",
    ]


def test_measure_producer_crash_reports_loss_then_full_recovery() -> None:
    result = measure_producer_crash(
        InProcessEventBus,
        scenario=ComparisonScenario(
            event_count=1000,
            crash_at=500,
            include_crash_replay=False,
        ),
    )

    assert result == ProducerCrashResult(
        published_before_crash=500,
        delivered_before_crash=500,
        loss_count=500,
        recovered_count=500,
        final_loss_count=0,
        recovery_complete=True,
    )
