# ADR-014: Message Bus Technology

**Status:** Proposed  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #14

---

## Context and problem statement

Agents communicate via typed, versioned events (EventEnvelope). We need a mechanism to deliver events from one agent to the next (or to the Orchestrator) in Phase 1. The pipeline is batch-first and in-process for the 12-week curriculum; adding an external message broker would require another service and operational complexity. Unit tests must be able to run without a live bus. The event envelope (event_id, correlation_id, agent_id, timestamp, schema_version, payload) must be preserved regardless of transport.

## Considered options

* **In-process Python events** — Direct function calls or a simple in-process pub/sub that passes EventEnvelope objects. No separate process or network. Reference implementation for Phase 1.
* **Kafka** — Durable, scalable log. Requires a Kafka cluster; serialization/deserialization of EventEnvelope; overkill for single-runner Phase 1.
* **RabbitMQ** — Message broker with queues and routing. Requires a broker process; same serialization and ops concerns.
* **Redis Streams** — Lightweight stream abstraction. Still requires Redis; adds dependency for Phase 1.

## Decision outcome

**Chosen option:** In-process Python events for Phase 1; external bus deferred to Phase 2.

**Rationale:** The curriculum and ARCHITECTURE_DEEP assume a single runner that triggers the pipeline (e.g. via APScheduler), passes events between agents in memory, and logs every event. In-process delivery keeps tests simple (no broker to start), preserves the exact EventEnvelope contract without serialization, and matches the “walking skeleton” and Week 2–6 scope. Kafka, RabbitMQ, and Redis Streams are viable for Phase 2 when we need durability, multiple consumers, or cross-process delivery; they are not required for correctness or evaluation in Phase 1. The migration path is to introduce a bus adapter that implements the same “publish event / subscribe by type” interface so agent code does not depend on the transport.

## Consequences

* **Positive:** No extra infrastructure; tests run without a message service; event envelope stays in Python objects; fast iteration.
* **Negative:** No durability across process restarts; single process only; Phase 2 will require a bus abstraction and possibly a new ADR to choose Kafka/RabbitMQ/Redis.
* **Neutral:** Agent code should depend on an abstract “send event / receive event” interface so that Phase 2 can swap in an external bus behind that interface.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #14 options and evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — event catalog, agents communicate via events only
* agents/common/event_envelope.py — EventEnvelope contract
