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

## Commit 3 Redis usage

- Install dependency: `pip install redis` (or install from `agents/requirements.txt`).
- `publish(event)` appends serialized `EventEnvelope` JSON to a stream.
- `subscribe(event_type, handler, subscriber_id=...)` registers one handler.
- `consume_available(...)` reads pending + new entries and dispatches handlers:
  - `replay_pending=True` reprocesses unacked entries first.
  - `stop_on_handler_error=True` raises `HandlerExecutionError` and leaves the
    failed entry pending for replay.
