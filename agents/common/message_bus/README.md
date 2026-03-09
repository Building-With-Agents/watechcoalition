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
