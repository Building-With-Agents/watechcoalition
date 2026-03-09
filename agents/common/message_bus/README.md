# Message Bus Contracts (Week 3 Commit 1)

This package defines the transport-agnostic event bus contract used by Week 3
experiments.

## Assumptions

- Events are batch-triggered and routed by `payload["event_type"]`.
- The transport unit is `EventEnvelope` for all implementations.
- orchestration-only control events (`*Failed`, `*Alert`,
  `SourceFailure`, `DemandAnomaly`) are reserved for
  `orchestration-agent` only.

## Scope

Commit 1 includes abstractions, shared typing, and validation helpers only.
No transport-specific bus implementation is included in this package yet.
