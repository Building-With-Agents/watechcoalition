"""Transport comparison helpers for Week 3 event-bus experiments."""

from __future__ import annotations

import inspect
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import cast

from agents.common.event_envelope import EventEnvelope
from agents.common.events.ingest_batch_harness import generate_synthetic_ingest_batches
from agents.common.message_bus.base import EventBusBase
from agents.common.message_bus.kafka import KafkaHandlerExecutionError
from agents.common.message_bus.redis_streams import HandlerExecutionError
from agents.normalization.events import normalization_complete_payload


@dataclass(frozen=True, slots=True)
class ComparisonScenario:
    """Configuration for one transport comparison run."""

    name: str = "ingest_batch_to_normalization_complete"
    event_count: int = 1000
    seed: int = 42
    drain_batch_size: int = 256
    drain_iteration_limit: int = 10_000
    latency_sample_size: int | None = None
    include_crash_replay: bool = True
    crash_at: int = 500
    producer_crash_at: int | None = None


@dataclass(frozen=True, slots=True)
class TransportCandidate:
    """Factory-backed transport candidate used by the comparison runner."""

    transport: str
    backend: str
    factory: Callable[[], EventBusBase]
    replay_factory: Callable[[], EventBusBase] | None = None


@dataclass(frozen=True, slots=True)
class DrainStats:
    """Drain-loop summary for transports with explicit consumption."""

    drained_events: int
    iterations: int


@dataclass(frozen=True, slots=True)
class ProducerCrashResult:
    """Normalized producer-crash measurement for one transport."""

    published_before_crash: int
    delivered_before_crash: int
    loss_count: int
    recovered_count: int
    final_loss_count: int
    recovery_complete: bool


@dataclass(frozen=True, slots=True)
class TransportComparisonResult:
    """Normalized result row for one transport run."""

    scenario_name: str
    transport: str
    backend: str
    input_events: int
    throughput_publish_events_per_sec: float
    throughput_e2e_events_per_sec: float
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    latency_p99_ms: float | None
    latency_sample_count: int
    crash_replay_complete: bool | None
    replay_completeness_pct: float | None
    producer_crash_published_before_crash: int | None
    producer_crash_delivered_before_crash: int | None
    producer_crash_loss_count: int | None
    producer_resume_recovered_count: int | None
    producer_resume_final_loss_count: int | None
    producer_resume_complete: bool | None
    published_events: int
    delivered_events: int
    handler_failures: int
    queue_depth: int | None
    in_flight: int | None
    drain_iterations: int
    correctness_passed: bool
    max_in_flight: int | None
    replay_count: int | None
    correlation_id_propagation_passed: bool
    producer_crash_delivered: int | None
    producer_crash_events_lost: int | None
    events_lost_consumer_crash: int | None


def run_transport_comparison(
    bus: EventBusBase,
    *,
    transport: str,
    backend: str = "custom",
    scenario: ComparisonScenario | None = None,
    replay_bus_factory: Callable[[], EventBusBase] | None = None,
    producer_crash_bus_factory: Callable[[], EventBusBase] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> TransportComparisonResult:
    """Run the shared harness scenario against one bus instance."""
    resolved = scenario or ComparisonScenario()
    _validate_scenario(resolved)

    harness_events = list(
        generate_synthetic_ingest_batches(
            count=resolved.event_count,
            seed=resolved.seed,
        )
    )
    publish_started_at: dict[str, float] = {}
    latency_ms: list[float] = []
    normalization_seen: list[str] = []
    completions_seen: list[str] = []

    def _normalization_handler(event: EventEnvelope) -> None:
        normalization_seen.append(event.event_id)
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

        started_at = publish_started_at.get(event.event_id)
        if started_at is None:
            return
        if (
            resolved.latency_sample_size is not None
            and len(latency_ms) >= resolved.latency_sample_size
        ):
            return
        latency_ms.append((clock() - started_at) * 1000)

    def _completion_handler(event: EventEnvelope) -> None:
        completions_seen.append(event.event_id)

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

    first_publish_started_at: float | None = None
    for event in harness_events:
        started_at = clock()
        if first_publish_started_at is None:
            first_publish_started_at = started_at
        publish_started_at[event.event_id] = started_at
        bus.publish(event)
    publish_completed_at = clock()

    drain_stats = drain_bus(
        bus,
        batch_size=resolved.drain_batch_size,
        iteration_limit=resolved.drain_iteration_limit,
    )
    finished_at = clock()

    if first_publish_started_at is None:
        raise RuntimeError("comparison scenario did not publish any events")

    publish_seconds = max(publish_completed_at - first_publish_started_at, 1e-9)
    e2e_seconds = max(finished_at - first_publish_started_at, 1e-9)
    counters = snapshot_counters(bus)

    replay_complete: bool | None = None
    replay_completeness_pct: float | None = None
    replay_count: int | None = None
    replay_factory = replay_bus_factory
    events_lost_consumer_crash: int | None = None
    if resolved.include_crash_replay and replay_factory is not None and has_consumer(bus):
        replay_complete, replay_completeness_pct, replay_count = measure_crash_replay(
            replay_factory,
            scenario=resolved,
        )
        if replay_count is not None:
            recovered = (resolved.crash_at - 1) + replay_count
            events_lost_consumer_crash = max(0, resolved.event_count - recovered)

    producer_crash_delivered: int | None = None
    producer_crash_events_lost: int | None = None
    if (
        resolved.producer_crash_at is not None
        and replay_bus_factory is not None
    ):
        producer_crash_delivered, producer_crash_events_lost = (
            _measure_producer_crash_delivered_lost(
                replay_bus_factory,
                scenario=resolved,
            )
        )

    producer_crash = (
        measure_producer_crash(
            producer_crash_bus_factory,
            scenario=resolved,
        )
        if producer_crash_bus_factory is not None
        else None
    )

    expected_total_events = resolved.event_count * 2
    correctness_passed = (
        len(normalization_seen) == resolved.event_count
        and len(completions_seen) == resolved.event_count
        and counters["published_events"] == expected_total_events
        and counters["delivered_events"] == expected_total_events
        and counters["handler_failures"] == 0
        and counters["queue_depth"] in {None, 0}
        and counters["in_flight"] in {None, 0}
    )

    queue_depth_result = (
        counters.get("max_queue_depth_seen")
        if counters.get("max_queue_depth_seen") is not None
        else counters["queue_depth"]
    )
    max_in_flight_result = (
        counters.get("max_in_flight_seen")
        if counters.get("max_in_flight_seen") is not None
        else counters.get("in_flight")
    )

    return TransportComparisonResult(
        scenario_name=resolved.name,
        transport=transport,
        backend=backend,
        input_events=resolved.event_count,
        throughput_publish_events_per_sec=resolved.event_count / publish_seconds,
        throughput_e2e_events_per_sec=resolved.event_count / e2e_seconds,
        latency_p50_ms=percentile(latency_ms, 50),
        latency_p95_ms=percentile(latency_ms, 95),
        latency_p99_ms=percentile(latency_ms, 99),
        latency_sample_count=len(latency_ms),
        crash_replay_complete=replay_complete,
        replay_completeness_pct=replay_completeness_pct,
        producer_crash_published_before_crash=(
            producer_crash.published_before_crash if producer_crash is not None else None
        ),
        producer_crash_delivered_before_crash=(
            producer_crash.delivered_before_crash if producer_crash is not None else None
        ),
        producer_crash_loss_count=(
            producer_crash.loss_count if producer_crash is not None else None
        ),
        producer_resume_recovered_count=(
            producer_crash.recovered_count if producer_crash is not None else None
        ),
        producer_resume_final_loss_count=(
            producer_crash.final_loss_count if producer_crash is not None else None
        ),
        producer_resume_complete=(
            producer_crash.recovery_complete if producer_crash is not None else None
        ),
        published_events=counters["published_events"],
        delivered_events=counters["delivered_events"],
        handler_failures=counters["handler_failures"],
        queue_depth=queue_depth_result,
        in_flight=counters["in_flight"],
        drain_iterations=drain_stats.iterations,
        correctness_passed=correctness_passed,
        max_in_flight=max_in_flight_result,
        replay_count=replay_count,
        correlation_id_propagation_passed=correctness_passed,
        producer_crash_delivered=producer_crash_delivered,
        producer_crash_events_lost=producer_crash_events_lost,
        events_lost_consumer_crash=events_lost_consumer_crash,
    )


def compare_transport_candidates(
    candidates: Sequence[TransportCandidate],
    *,
    scenario: ComparisonScenario | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> list[TransportComparisonResult]:
    """Run one normalized scenario against multiple transport factories."""
    resolved = scenario or ComparisonScenario()
    return [
        run_transport_comparison(
            candidate.factory(),
            transport=candidate.transport,
            backend=candidate.backend,
            scenario=resolved,
            replay_bus_factory=candidate.replay_factory or candidate.factory,
            producer_crash_bus_factory=candidate.factory,
            clock=clock,
        )
        for candidate in candidates
    ]


def drain_bus(
    bus: EventBusBase,
    *,
    batch_size: int = 256,
    iteration_limit: int = 10_000,
) -> DrainStats:
    """Consume until a bus reports no more pending or new messages."""
    _validate_drain_args(batch_size, iteration_limit)
    consume = getattr(bus, "consume_available", None)
    if not callable(consume):
        return DrainStats(drained_events=0, iterations=0)

    total_drained = 0
    kwargs = _build_consume_kwargs(consume, max_events=batch_size)
    for iteration in range(1, iteration_limit + 1):
        consumed = cast(int, consume(**kwargs))
        total_drained += consumed
        if consumed == 0:
            return DrainStats(drained_events=total_drained, iterations=iteration)

    raise RuntimeError(
        f"bus did not drain within iteration_limit={iteration_limit}"
    )


def has_consumer(bus: EventBusBase) -> bool:
    """True when the bus requires explicit consume/drain operations."""
    return callable(getattr(bus, "consume_available", None))


def measure_crash_replay(
    bus_factory: Callable[[], EventBusBase],
    *,
    scenario: ComparisonScenario | None = None,
) -> tuple[bool, float, int]:
    """Run the crash-at-N then replay scenario on a fresh transport instance.

    Returns:
        (replay_complete, replay_completeness_pct, replay_count)
        where replay_count is the number of events processed after the crash.
    """
    resolved = scenario or ComparisonScenario()
    _validate_scenario(resolved)

    bus = bus_factory()
    if not has_consumer(bus):
        raise ValueError("crash replay requires a bus with consume_available()")

    harness_events = list(
        generate_synthetic_ingest_batches(
            count=resolved.event_count,
            seed=resolved.seed,
        )
    )
    published_ids = [event.event_id for event in harness_events]
    first_run_processed_ids: list[str] = []
    replay_processed_ids: list[str] = []
    replay_mode = False
    seen = 0
    crash_at = _effective_crash_at(resolved)

    def _crash_once_handler(event: EventEnvelope) -> None:
        nonlocal replay_mode, seen
        if replay_mode:
            replay_processed_ids.append(event.event_id)
            return

        seen += 1
        if seen == crash_at:
            raise RuntimeError(f"simulated crash at event index {crash_at}")
        first_run_processed_ids.append(event.event_id)

    bus.subscribe(
        "IngestBatch",
        _crash_once_handler,
        subscriber_id="normalization-agent",
    )

    for event in harness_events:
        bus.publish(event)

    crashed = False
    while True:
        try:
            consumed = consume_once(bus, max_events=1)
        except (HandlerExecutionError, KafkaHandlerExecutionError):
            crashed = True
            break

        if consumed == 0:
            break

    replay_mode = True
    drain_bus(
        bus,
        batch_size=resolved.drain_batch_size,
        iteration_limit=resolved.drain_iteration_limit,
    )

    combined_ids = first_run_processed_ids + replay_processed_ids
    replay_completeness_pct = (
        len(set(combined_ids).intersection(published_ids)) / len(published_ids)
    ) * 100
    replay_complete = (
        crashed
        and len(combined_ids) == len(published_ids)
        and set(combined_ids) == set(published_ids)
    )
    replay_count = len(replay_processed_ids)
    return replay_complete, replay_completeness_pct, replay_count


def _measure_producer_crash_delivered_lost(
    bus_factory: Callable[[], EventBusBase],
    *,
    scenario: ComparisonScenario | None = None,
) -> tuple[int, int]:
    """Publish first producer_crash_at events then drain; return (delivered, events_lost)."""
    resolved = scenario or ComparisonScenario()
    _validate_scenario(resolved)
    n = resolved.producer_crash_at
    if n is None or n <= 0:
        raise ValueError("producer_crash_at must be set and > 0")

    bus = bus_factory()
    harness_events = list(
        generate_synthetic_ingest_batches(
            count=resolved.event_count,
            seed=resolved.seed,
        )
    )
    to_publish = harness_events[:n]
    delivered_ids: list[str] = []

    def _count_handler(event: EventEnvelope) -> None:
        delivered_ids.append(event.event_id)

    bus.subscribe(
        "IngestBatch",
        _count_handler,
        subscriber_id="normalization-agent",
    )

    for event in to_publish:
        bus.publish(event)

    if has_consumer(bus):
        drain_bus(
            bus,
            batch_size=resolved.drain_batch_size,
            iteration_limit=resolved.drain_iteration_limit,
        )

    delivered = len(delivered_ids)
    events_lost = n - delivered
    return delivered, events_lost


def measure_producer_crash(
    bus_factory: Callable[[], EventBusBase],
    *,
    scenario: ComparisonScenario | None = None,
) -> ProducerCrashResult:
    """Publish until crash_at, stop, then resume publishing and measure loss."""
    resolved = scenario or ComparisonScenario()
    _validate_scenario(resolved)
    crash_at = _effective_crash_at(resolved)

    bus = bus_factory()
    harness_events = list(
        generate_synthetic_ingest_batches(
            count=resolved.event_count,
            seed=resolved.seed,
        )
    )
    first_batch = harness_events[:crash_at]
    resume_batch = harness_events[crash_at:]
    delivered_before_resume: list[str] = []
    delivered_after_resume: list[str] = []
    capture_before_resume = True

    def _normalization_handler(event: EventEnvelope) -> None:
        delivered_after_resume.append(event.event_id)
        if capture_before_resume:
            delivered_before_resume.append(event.event_id)

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

    bus.subscribe(
        "IngestBatch",
        _normalization_handler,
        subscriber_id="normalization-agent",
    )
    bus.subscribe(
        "NormalizationComplete",
        lambda _: None,
        subscriber_id="analytics-agent",
    )

    for event in first_batch:
        bus.publish(event)

    drain_bus(
        bus,
        batch_size=resolved.drain_batch_size,
        iteration_limit=resolved.drain_iteration_limit,
    )

    delivered_before_crash = len(set(delivered_before_resume))
    loss_count = max(resolved.event_count - delivered_before_crash, 0)

    capture_before_resume = False
    for event in resume_batch:
        bus.publish(event)

    drain_bus(
        bus,
        batch_size=resolved.drain_batch_size,
        iteration_limit=resolved.drain_iteration_limit,
    )

    final_delivered_count = len(set(delivered_after_resume))
    recovered_count = max(final_delivered_count - delivered_before_crash, 0)
    final_loss_count = max(resolved.event_count - final_delivered_count, 0)

    return ProducerCrashResult(
        published_before_crash=len(first_batch),
        delivered_before_crash=delivered_before_crash,
        loss_count=loss_count,
        recovered_count=recovered_count,
        final_loss_count=final_loss_count,
        recovery_complete=final_loss_count == 0,
    )


def consume_once(bus: EventBusBase, *, max_events: int = 1) -> int:
    """Consume one iteration with handler failures surfaced to the caller."""
    consume = getattr(bus, "consume_available", None)
    if not callable(consume):
        raise ValueError("consume_once requires a bus with consume_available()")
    kwargs = _build_consume_kwargs(consume, max_events=max_events)
    kwargs["stop_on_handler_error"] = True
    return cast(int, consume(**kwargs))


def snapshot_counters(bus: EventBusBase) -> dict[str, int | None]:
    """Return normalized transport counters across all bus variants."""
    raw_counters = getattr(bus, "counters", {})
    counters = raw_counters if isinstance(raw_counters, dict) else {}
    out: dict[str, int | None] = {
        "published_events": int(counters.get("published_events", 0)),
        "delivered_events": int(counters.get("delivered_events", 0)),
        "handler_failures": int(counters.get("handler_failures", 0)),
        "queue_depth": _maybe_int(counters.get("queue_depth")),
        "in_flight": _maybe_int(counters.get("in_flight")),
    }
    max_qd = _maybe_int(counters.get("max_queue_depth_seen"))
    max_if = _maybe_int(counters.get("max_in_flight_seen"))
    if max_qd is not None:
        out["max_queue_depth_seen"] = max_qd
    if max_if is not None:
        out["max_in_flight_seen"] = max_if
    return out


def results_to_rows(
    results: Sequence[TransportComparisonResult],
) -> list[dict[str, object]]:
    """Return CSV-friendly rows for one or more comparison results."""
    return [
        {
            "transport": result.transport,
            "backend": result.backend,
            "throughput_publish_events_per_sec": result.throughput_publish_events_per_sec,
            "throughput_e2e_events_per_sec": result.throughput_e2e_events_per_sec,
            "latency_p50_ms": result.latency_p50_ms,
            "latency_p95_ms": result.latency_p95_ms,
            "latency_p99_ms": result.latency_p99_ms,
            "crash_replay_complete": result.crash_replay_complete,
            "replay_completeness_pct": result.replay_completeness_pct,
            "producer_crash_published_before_crash": result.producer_crash_published_before_crash,
            "producer_crash_delivered_before_crash": result.producer_crash_delivered_before_crash,
            "producer_crash_loss_count": result.producer_crash_loss_count,
            "producer_resume_recovered_count": result.producer_resume_recovered_count,
            "producer_resume_final_loss_count": result.producer_resume_final_loss_count,
            "producer_resume_complete": result.producer_resume_complete,
            "published_events": result.published_events,
            "delivered_events": result.delivered_events,
            "handler_failures": result.handler_failures,
            "queue_depth": result.queue_depth,
            "in_flight": result.in_flight,
            "correctness_passed": result.correctness_passed,
            "max_in_flight": result.max_in_flight,
            "replay_count": result.replay_count,
            "correlation_id_propagation_passed": result.correlation_id_propagation_passed,
            "producer_crash_delivered": result.producer_crash_delivered,
            "producer_crash_events_lost": result.producer_crash_events_lost,
            "events_lost_consumer_crash": result.events_lost_consumer_crash,
        }
        for result in results
    ]


def format_results_markdown_table(
    results: Sequence[TransportComparisonResult],
) -> str:
    """Render one or more comparison rows as Markdown."""
    headers = [
        "transport",
        "backend",
        "throughput_publish_events_per_sec",
        "throughput_e2e_events_per_sec",
        "latency_p50_ms",
        "latency_p95_ms",
        "latency_p99_ms",
        "crash_replay_complete",
        "replay_completeness_pct",
        "producer_crash_published_before_crash",
        "producer_crash_delivered_before_crash",
        "producer_crash_loss_count",
        "producer_resume_recovered_count",
        "producer_resume_final_loss_count",
        "producer_resume_complete",
        "published_events",
        "delivered_events",
        "handler_failures",
        "queue_depth",
        "in_flight",
        "correctness_passed",
        "max_in_flight",
        "replay_count",
        "correlation_id_propagation_passed",
        "producer_crash_delivered",
        "producer_crash_events_lost",
        "events_lost_consumer_crash",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in results_to_rows(results):
        lines.append(
            "| " + " | ".join(_format_cell(row[header]) for header in headers) + " |"
        )

    return "\n".join(lines)


def percentile(values: Sequence[float], pct: float) -> float | None:
    """Return a linear-interpolated percentile from a sequence of values."""
    if not values:
        return None
    if len(values) == 1:
        return values[0]

    ordered = sorted(values)
    rank = (len(ordered) - 1) * (pct / 100)
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]

    weight = rank - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * weight)


def _build_consume_kwargs(
    consume: Callable[..., int],
    *,
    max_events: int,
) -> dict[str, object]:
    params = inspect.signature(consume).parameters
    kwargs: dict[str, object] = {"max_events": max_events}
    if "replay_pending" in params:
        kwargs["replay_pending"] = True
    if "block_ms" in params:
        kwargs["block_ms"] = 0
    if "timeout_ms" in params:
        kwargs["timeout_ms"] = 0
    return kwargs


def _validate_scenario(scenario: ComparisonScenario) -> None:
    if scenario.event_count <= 0:
        raise ValueError("event_count must be > 0")
    if scenario.drain_batch_size <= 0:
        raise ValueError("drain_batch_size must be > 0")
    if scenario.drain_iteration_limit <= 0:
        raise ValueError("drain_iteration_limit must be > 0")
    if scenario.latency_sample_size is not None and scenario.latency_sample_size <= 0:
        raise ValueError("latency_sample_size must be > 0 when provided")
    if scenario.crash_at <= 0:
        raise ValueError("crash_at must be > 0")
    if scenario.include_crash_replay and scenario.crash_at > scenario.event_count:
        raise ValueError("crash_at must be <= event_count when replay is enabled")
    if scenario.producer_crash_at is not None:
        if scenario.producer_crash_at <= 0:
            raise ValueError("producer_crash_at must be > 0 when provided")
        if scenario.producer_crash_at > scenario.event_count:
            raise ValueError("producer_crash_at must be <= event_count")


def _validate_drain_args(batch_size: int, iteration_limit: int) -> None:
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    if iteration_limit <= 0:
        raise ValueError("iteration_limit must be > 0")


def _maybe_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _format_cell(value: object) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _effective_crash_at(scenario: ComparisonScenario) -> int:
    return min(scenario.crash_at, scenario.event_count)


__all__ = [
    "ComparisonScenario",
    "DrainStats",
    "ProducerCrashResult",
    "TransportCandidate",
    "TransportComparisonResult",
    "compare_transport_candidates",
    "consume_once",
    "drain_bus",
    "format_results_markdown_table",
    "has_consumer",
    "measure_crash_replay",
    "measure_producer_crash",
    "percentile",
    "results_to_rows",
    "run_transport_comparison",
    "snapshot_counters",
]
