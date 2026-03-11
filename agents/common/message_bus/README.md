# Message Bus Contracts (Week 3 Commit 1-2)

This package defines the transport-agnostic event bus contract used by Week 3
experiments.

## Assumptions

- Events are batch-triggered and routed by `payload["event_type"]`.
- The transport unit is `EventEnvelope` for all implementations.
- orchestration-only control events (`*Failed`, `*Alert`,
  `SourceFailure`, `DemandAnomaly`) are reserved for
  `orchestration-agent` only.

## Scope

- Commit 1: transport-agnostic abstractions, shared typing, and validation
  helpers.
- Commit 2: baseline `InProcessEventBus` with in-memory subscriptions and
  minimal counters (`published_events`, `delivered_events`, `handler_failures`).
- Commit 3: `RedisStreamsEventBus` candidate with Redis Streams
  publish/consume (`xadd`, `xreadgroup`, `xack`), envelope
  serialization/deserialization, and transport counters
  (`published_events`, `delivered_events`, `handler_failures`,
  `queue_depth`, `in_flight`).
- Commit 4: `KafkaEventBus` candidate with Kafka publish/consume
  (`send`, `poll`, per-message `commit`), envelope
  serialization/deserialization, and transport counters
  (`published_events`, `delivered_events`, `handler_failures`,
  `queue_depth`, `in_flight`).

## Commit 3 Redis usage

- Install dependency: `pip install redis` (or install from `agents/requirements.txt`).
- `publish(event)` appends serialized `EventEnvelope` JSON to a stream.
- `subscribe(event_type, handler, subscriber_id=...)` registers one handler.
- `consume_available(...)` reads pending + new entries and dispatches handlers:
  - `replay_pending=True` reprocesses unacked entries first.
  - `stop_on_handler_error=True` raises `HandlerExecutionError` and leaves the
    failed entry pending for replay.

## Commit 4 Kafka usage

- Install dependency if using live brokers: `pip install kafka-python`
  (or install from `agents/requirements.txt`).
- `publish(event)` sends serialized `EventEnvelope` JSON to a topic.
- `subscribe(event_type, handler, subscriber_id=...)` registers one handler.
- `consume_available(...)` polls and dispatches handlers:
  - successful messages are committed per message.
  - failed messages are not committed and are seeked for replay.
  - released-for-replay messages are removed from `in_flight` immediately.
  - `stop_on_handler_error=True` raises `KafkaHandlerExecutionError`
    on the first handler failure and keeps that message replayable.
- kafka-python adapter uses synchronous producer ack (`future.get(timeout=10)`)
  for deterministic experiment counters; production can switch to async/callback.

## Transport comparison utilities

- `comparison.py` adds one shared benchmark runner for transport comparisons.
- `run_transport_comparison(...)` runs the standard harness scenario against one
  bus instance and returns a normalized result row with:
  - publish throughput (`throughput_publish_events_per_sec`)
  - end-to-end throughput (`throughput_e2e_events_per_sec`)
  - publish-to-handler latency (`latency_p50_ms`, `latency_p95_ms`, `latency_p99_ms`)
  - parity counters (`published_events`, `delivered_events`, `handler_failures`,
    `queue_depth`, `in_flight`)
  - optional crash/replay completeness (`crash_replay_complete`,
    `replay_completeness_pct`) when a replay-capable bus factory is provided
- `compare_transport_candidates(...)` is the multi-bus entry point. Pass a list
  of `TransportCandidate` factories and it returns one normalized result row per
  transport/backend.
- `format_results_markdown_table(...)` and `results_to_rows(...)` convert those
  result rows into a Markdown table or CSV-friendly dictionaries for ADRs or
  findings docs.
- CLI entry point:
  - `python -m agents.common.message_bus.run_comparison`
  - useful flags:
    - `--count 1000 --seed 42`
    - `--format markdown|csv|json`
    - `--output agents/docs/exp004_transport_results.md`
    - `--redis-url redis://...` to swap fake Redis for live Redis
    - `--kafka-bootstrap-servers localhost:9092` to swap fake Kafka for live Kafka
