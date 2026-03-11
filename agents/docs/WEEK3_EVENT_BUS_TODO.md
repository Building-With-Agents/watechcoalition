# Week 3 Event Bus TODO

Owner: Bryan
Experiment: `EXP-004`
Timebox: 2 days

## Day 1

### Commit 1: scaffold event bus abstractions and shared contracts
- [x] Create `agents/common/message_bus/` package.
- [x] Add `EventBusBase` with `publish()` and `subscribe()` contract.
- [x] Add shared typing/helpers needed by all bus implementations.
- [x] Keep the interface transport-agnostic so Redis Streams and Kafka can use the same contract later.
- [x] Document assumptions: batch-trigger events, `EventEnvelope` transport, orchestrator-only `*Failed` and `*Alert` subscriptions.

Definition of done:
- [x] Base abstraction exists.
- [x] Imports are clean and minimal.
- [x] No changes yet to `pipeline_runner.py`.

### Commit 2: implement in-process event bus baseline
- [x] Add `InProcessEventBus` with in-memory subscriber registry.
- [x] Support publish/subscribe for the `IngestBatch -> NormalizationComplete` handoff.
- [x] Add basic instrumentation counters for: published events, delivered events, handler failures.
- [x] Add minimal tests for synchronous publish/subscribe behavior.
- [x] Add a test that drives the bus with the same event stream as the harness (use `generate_synthetic_ingest_batches` from `agents.common.events.ingest_batch_harness` when Emilio’s branch is merged; until then use `_fixture_synthetic_ingest_batches` in `tests/test_in_process_event_bus.py` with batch-level payload and `seed=42`). Test asserts delivery count and correlation_id preserved from IngestBatch to emitted NormalizationComplete.

Definition of done:
- [x] In-process bus can deliver an `IngestBatch` event to a normalization handler.
- [x] Correlation ID is preserved end-to-end (IngestBatch → handler → NormalizationComplete).
- [x] Test coverage exists for basic delivery behavior (sync delivery, handler-failure counter, harness-equivalent stream at count=1000, seed=42).
- [x] In-process approach is testable: `cd agents && .venv/bin/python -m pytest tests/test_message_bus_contracts.py tests/test_in_process_event_bus.py -q` (13 passed).

## Known inconsistencies / follow-up

- **Harness module not in branch:** Tests use fallback deterministic fixtures in `tests/message_bus_stream_fixtures.py` until Emilio’s harness is merged; then `generate_synthetic_ingest_batches` via try/except.
- **IngestBatch shape:** Unify batch-level vs posting-level with Emilio before Redis/Kafka parity so all buses see the same payload shape.
- **Sync vs async:** Document or tighten semantics before parity testing so all three buses behave consistently for async handlers.

## Day 2 — Agreed experiment design

**Canonical definitions** (crashes, event loss Option A, replay, observability) are in `WEEK3_HARNESS_AND_ALIGNMENT_ANALYSIS.md` §3. Use them for Commits 3 and 4 so all three buses are comparable.

### Commit 3: implement Redis Streams candidate
- [x] Add Redis-backed event bus behind `EventBusBase`.
- [x] Serialize/publish `EventEnvelope` consistently; consume `IngestBatch`, emit `NormalizationComplete`.
- [x] Expose same bus counters as in-process: published, delivered, handler_failures; optionally queue_depth, in-flight.
- [x] Add test or runner that drives 1,000-event stream (harness or fixture, seed=42); assert delivery count and correlation_id.
- [x] Add crash scenario: consumer raises at a fixed event index (e.g. 500); document replay behavior (replay count, completeness, same event_ids) for ADR.

Definition of done:
- [x] Redis candidate runs the same handoff contract as in-process.
- [x] Envelope serialization/deserialization is stable.
- [x] Ready for throughput, crash, replay, and observability testing per agreed design.

Implementation notes:
- `agents/common/message_bus/redis_streams.py` adds `RedisStreamsEventBus` (xadd/xreadgroup/xack + counters + replay).
- `agents/tests/test_redis_streams_event_bus.py` covers 1,000-event parity and crash/replay at index 500 (replay_count=501, replay_completeness=100%, event_id-set parity).

### Commit 4: implement Kafka candidate and experiment integration
- [ ] Add Kafka-backed event bus behind `EventBusBase`.
- [ ] Align topic/event routing with the same contract; same bus counters (published, delivered, handler_failures; optional queue_depth, in-flight).
- [ ] Same 1,000-event and crash/replay scenarios as Redis; capture caveats for findings doc and ADR.
- [ ] Add or extend tests for transport parity across all three implementations.

Definition of done:
- Kafka candidate supports the same two-agent handoff.
- All three implementations are swappable and tested under the same experiment rules.
- Ready for ADR-004: throughput, crash, replay, observability (event loss Option A, latency publish→consumed, etc.).

## Dependencies and coordination

- **Emilio:** 1,000-event harness and validation. Alignment on experiment design is **done**; definitions are in `WEEK3_HARNESS_AND_ALIGNMENT_ANALYSIS.md`.

### Runbook (Gary — Exercise 3.4)
- **Event types:** IngestBatch → NormalizationComplete for Commits 3–4; add SourceFailure, NormalizationFailed for Week 6 / combined review.
- **Typed event classes:** Sync with Emilio when introducing Pydantic subclasses of EventEnvelope; bus can stay on `EventEnvelope` + `extract_event_type()` for Day 2.
- **Failure payload fields:** `error_type`, `severity`, `error_reason` — already in `ingestion/events.py` and `normalization/events.py`.
- **APScheduler chaining:** Optional after Commit 2; in-process testable via direct test first.
- **End-to-end chain test:** Commit 2 covers correlation_id IngestBatch → NormalizationComplete.

## How to test in-process after Commit 2

1. **With Emilio’s harness merged:**  
   `cd agents && pytest common/events/tests/test_harness_events.py -v` (harness structure). Then run the bus test that does:
   ```python
   from agents.common.events.ingest_batch_harness import generate_synthetic_ingest_batches
   bus = InProcessEventBus()
   bus.subscribe("IngestBatch", normalization_handler, subscriber_id="normalization-agent")
   for event in generate_synthetic_ingest_batches(count=1000, seed=42):
       bus.publish(event)
   # Assert: delivered count == 1000, correlation_id preserved on each handler call / NormalizationComplete
   ```
2. **Before harness merge (current state):** The bus tests use deterministic fallback generation in `tests/message_bus_stream_fixtures.py`, which builds `EventEnvelope` instances with batch-level IngestBatch payload (via `ingest_batch_payload`) and deterministic `seed=42`. Same assertions: delivery count and correlation_id end-to-end.

## Notes for ADR-004

- Default recommendation: in-process pub/sub unless the experiment justifies Redis or Kafka.
- Cite agreed experiment design: crash at event index, event loss Option A (consumed = eventually handled; loss = never consumed), replay metrics (count, completeness, same event_ids), observability (throughput, latency publish→consumed, bus counters). See `WEEK3_HARNESS_AND_ALIGNMENT_ANALYSIS.md` §3.
- Principles: comparability first; agent-facing code independent of transport.
