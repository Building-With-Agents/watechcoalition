"""
Sample: how the event bus could be used — run with no errors, with errors, and crash/recover.

This is an IN-MEMORY simulation (list as queue). Real implementation would use
Redis Streams, Kafka, or the in-process message bus. Run from repo root:

  python -m agents.common.events.demo_bus_flow

Scenarios:
  A. Happy path: publish 20 events, consume all.
  B. Stream with errors: publish mix of success + failure events; consumer counts and "handles" failures.
  C. Crash and recover: publish 50, consumer "crashes" after 20; replay from same generator to show recovery.
"""
# ruff: noqa: T201

from __future__ import annotations

from agents.common.event_envelope import EventEnvelope
from agents.common.events.ingest_batch_harness import (
    assert_valid_ingest_batch_envelope,
    generate_synthetic_ingest_batches,
)
from agents.common.events.synthetic_events import (
    generate_synthetic_source_failures,
)


def _event_type(e: EventEnvelope) -> str:
    return e.payload.get("event_type", "?")


# -----------------------------------------------------------------------------
# In-memory "bus" simulation (list as queue; real bus would be Redis/Kafka/etc.)
# -----------------------------------------------------------------------------


class SimpleInMemoryBus:
    """
    Minimal bus interface: publish appends, consume pops from the front.
    In production you'd replace this with Redis Streams, Kafka, or the project's
    message bus — same publish/consume pattern.
    """

    def __init__(self) -> None:
        self._queue: list[EventEnvelope] = []

    def publish(self, event: EventEnvelope) -> None:
        self._queue.append(event)

    def consume_one(self) -> EventEnvelope | None:
        if not self._queue:
            return None
        return self._queue.pop(0)

    def size(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()


# -----------------------------------------------------------------------------
# Consumer that treats failure events as "handled by orchestration" (count only)
# -----------------------------------------------------------------------------


def consume_until_empty(
    bus: SimpleInMemoryBus,
    validate_ingest_batch: bool = True,
) -> tuple[int, int, int]:
    """
    Consume all events. Count success (IngestBatch), source failures, other.
    Orchestration would react to *Failed / *Alert events; here we just count.
    Returns (success_count, source_failure_count, other_count).
    """
    success = 0
    source_failure = 0
    other = 0
    while True:
        event = bus.consume_one()
        if event is None:
            break
        et = _event_type(event)
        if et == "IngestBatch":
            if validate_ingest_batch:
                assert_valid_ingest_batch_envelope(event)
            success += 1
        elif et == "SourceFailure":
            source_failure += 1
        else:
            other += 1
    return success, source_failure, other


# -----------------------------------------------------------------------------
# Scenario A: Happy path — no errors
# -----------------------------------------------------------------------------


def run_happy_path() -> None:
    print("\n--- Scenario A: Happy path (no errors) ---\n")
    bus = SimpleInMemoryBus()
    count = 20
    for event in generate_synthetic_ingest_batches(count=count, seed=42):
        bus.publish(event)
    print(f"  Published {bus.size()} IngestBatch events (seed=42).")
    success, src_fail, other = consume_until_empty(bus)
    print(f"  Consumed: success={success}, source_failures={src_fail}, other={other}")
    print("  Result: all events processed, no failures.\n")


# -----------------------------------------------------------------------------
# Scenario B: Stream with errors — mix of success and SourceFailure
# -----------------------------------------------------------------------------


def run_with_errors() -> None:
    print("\n--- Scenario B: Stream with errors ---\n")
    bus = SimpleInMemoryBus()
    # Interleave: 10 IngestBatch, 3 SourceFailure, 7 IngestBatch, 2 SourceFailure
    for i, event in enumerate(
        generate_synthetic_ingest_batches(count=17, seed=100, typed=False)
    ):
        bus.publish(event)
        if i in (3, 6, 9):
            # Inject a failure after every 3rd success
            fail = next(
                generate_synthetic_source_failures(count=1, seed=100 + i, typed=False)
            )
            bus.publish(fail)
    print(f"  Published {bus.size()} events (17 IngestBatch + 3 SourceFailure interleaved).")
    success, src_fail, other = consume_until_empty(bus)
    print(f"  Consumed: success={success}, source_failures={src_fail}, other={other}")
    print("  Result: consumer sees both success and failure events; orchestration would alert on failures.\n")


# -----------------------------------------------------------------------------
# Scenario C: Crash and recover — consumer stops after N, then "recover" by replay
# -----------------------------------------------------------------------------


def run_crash_and_recover() -> None:
    print("\n--- Scenario C: Crash and recover ---\n")
    bus = SimpleInMemoryBus()
    total = 50
    crash_at = 20
    seed = 99
    for event in generate_synthetic_ingest_batches(count=total, seed=seed):
        bus.publish(event)
    print(f"  Published {total} events (seed={seed}).")
    # "Consume" until crash_at, then "crash" (stop without draining)
    consumed = 0
    while consumed < crash_at:
        event = bus.consume_one()
        if event is None:
            break
        assert_valid_ingest_batch_envelope(event)
        consumed += 1
    remaining_before = bus.size()
    print(f"  Consumer 'crashed' after processing {consumed} events. Remaining in bus: {remaining_before}")

    # "Recover": consume the rest from the bus
    success, src_fail, other = consume_until_empty(bus)
    print(f"  After recovery: consumed remaining {success} events from bus. Left in bus: {bus.size()}")

    # Replay from same generator (determinism): same seed => same events
    replay_events = list(generate_synthetic_ingest_batches(count=total, seed=seed))
    print(f"  Replay (same seed={seed}): first event_id = {replay_events[0].event_id} (deterministic).")
    print("  Result: same seed gives same events; can replay after crash for exactly-once or testing.\n")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main() -> None:
    print("=" * 70)
    print("EXP-004 Sample: Event bus flow (in-memory simulation)")
    print("  A. Happy path   B. Stream with errors   C. Crash and recover")
    print("=" * 70)
    run_happy_path()
    run_with_errors()
    run_crash_and_recover()
    print("=" * 70)
    print("Done. Real bus: replace SimpleInMemoryBus with Redis/Kafka/bus adapter.")
    print("=" * 70)


if __name__ == "__main__":
    main()
