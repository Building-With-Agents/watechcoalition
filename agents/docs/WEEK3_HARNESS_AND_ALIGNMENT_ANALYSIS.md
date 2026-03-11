# Week 3: Harness (Emilio) and Alignment (Bryan) — EXP-004

**Purpose:** Single reference for the test harness scope, Bryan’s principles, and the **agreed experiment design** (crashes, event loss, replay, observability) for Day 2 and ADR-004.

**Branch state:** Harness module (`agents.common.events.ingest_batch_harness`, `view_harness`, `common/events/tests/test_harness_events.py`) lives on Emilio’s branch. Bus tests use deterministic fallback generation in `tests/message_bus_stream_fixtures.py` (batch-level IngestBatch, `seed=42`). When the harness is merged, tests use `generate_synthetic_ingest_batches` via try/except import.

---

## 1. Harness scope (Emilio)

| Deliverable | Description |
|-------------|-------------|
| **Generator** | `generate_synthetic_ingest_batches(count=1000, seed=42)` — yields `EventEnvelope` with IngestBatch payloads. |
| **Validation** | `assert_valid_ingest_batch_envelope(event)` / `is_valid_ingest_batch_envelope(event)` — envelope + payload shape. |
| **CLI** | `python -m agents.common.events.view_harness` — `--count`, `--seed`, `--json`. |
| **Tests** | `pytest common/events/tests/test_harness_events.py` — shape, count, determinism, uniqueness. |

Integration: same stream every time — `for event in generate_synthetic_ingest_batches(count=1000, seed=42): bus.publish(event)`.

The harness provides **structure, determinism, and validation** only. Crashes, event loss, replay, and observability are defined in the agreed experiment design below; the harness (or shared test runner) may measure some of them when driving the bus.

---

## 2. Bryan’s principles vs harness

| Principle | Assessment |
|-----------|------------|
| Default = in-process unless experiment fails | Harness is transport-agnostic; all three buses consume the same stream. ✅ |
| Comparability first | Same seed → same 1,000 events, shared validation. ✅ |
| Agent-facing code independent of transport | Agents see `EventEnvelope`; bus contract is `EventBusBase.publish(event)`. Harness doesn’t couple to transport. ✅ |

No conflict between harness and these principles.

---

## 3. Agreed experiment design (canonical)

Definitions below are agreed with Emilio. Use them for in-process, Redis, and Kafka so results are comparable.

### Crashes

- **Simulation:** Raise an exception in the consumer at a specific **event index** (e.g. N = 500).
- Same index for all three buses so the scenario is comparable.

### Event loss (Option A)

- **Event loss** = an event that was **produced but never consumed**.
- **Consumed** = eventually handled: handler ran to completion without re-raising, or (for Redis/Kafka) acknowledged. If the bus retries and the handler succeeds on a retry, the event counts as **consumed**.
- **Not consumed** = never successfully handled (e.g. never delivered, or delivered but handler always threw and retries exhausted). Those count as **loss**.
- Duplicate delivery counts as **one** consumed (idempotent count).

### Replay

- **Replay count** — number of events processed in the replay run.
- **Replay completeness** — `(replay_count / expected_count) * 100`.
- **Same event_ids as first run** — after replay, compare event_ids to the initial run to check idempotency/deduplication.

### Observability

| Metric | Meaning | Where |
|--------|--------|--------|
| Throughput | Events consumed per second | Harness or test runner (wall-clock ÷ count). |
| Latency | Publish → consumed (handler finished) | Harness/runner; keeps in-process, Redis, Kafka comparable. Optional: publish → acknowledged for Redis/Kafka only. |
| Queue depth | Events pending in queue | Bus (Redis/Kafka); in-process may report 0 or pending. |
| In-flight | Sent but not yet acknowledged | Bus (Redis/Kafka); in-process typically 0 or 1. |
| Replay count | Events in replay run | Test runner. |
| Correlation ID propagation | % events with correlation_id preserved | Tests + findings doc. |
| Published / delivered / handler_failures | Bus counters | Bus (all three implementations). |

**Split:** Harness (or shared test runner) measures throughput and latency when driving the 1,000-event stream. Each bus exposes published, delivered, handler_failures (and optionally queue_depth, in-flight). Harness keeps generating and validating shape; no transport-specific logic in the harness.

---

## 4. Compatibility with codebase

- **EventEnvelope** and **EventBusBase.publish(event)** — compatible. ✅  
- **Routing:** `extract_event_type(event)` uses `payload["event_type"]`; IngestBatch must include it. ✅  
- **Payload shape:** Bus only requires `event_type`; normalization agent needs full agreed IngestBatch shape. Confirm with Emilio that harness validation matches the payload used in Day 2 (batch-level vs posting-level).

---

## 5. Gary’s runbook (Exercise 3.4) — coordination

| Item | Note |
|------|------|
| Four event types | IngestBatch (done), NormalizationComplete, SourceFailure, NormalizationFailed. Commit 2 uses IngestBatch → NormalizationComplete; others for Week 6 / combined review. |
| Typed event classes | Sync with Emilio: Pydantic classes inheriting from EventEnvelope. Bus can stay on `EventEnvelope` + `extract_event_type()` for Commit 2. |
| Failure payload fields | `error_type`, `severity`, `error_reason` on SourceFailure / NormalizationFailed. Payload builders in `ingestion/events.py` and `normalization/events.py` updated. |
| APScheduler chaining | Optional after Commit 2; in-process testable via direct test first. |
| End-to-end chain test | correlation_id IngestBatch → NormalizationComplete; Commit 2 test covers this. |

---

## 6. Next steps

1. **Day 2:** Implement Redis (Commit 3) and Kafka (Commit 4) behind the same contract; run 1,000-event and crash/replay scenarios using the definitions above.
2. **ADR-004:** Document experiment, results, and recommendation; cite (a) default in-process, (b) comparability first, (c) transport-agnostic agents, (d) harness as source of truth for stream/validation, (e) agreed crash/loss/replay/observability definitions.

---

## 7. Summary

Harness provides a deterministic, validated 1,000-event IngestBatch stream and fits Bryan’s principles. Experiment design (crashes at event index, event loss Option A, replay metrics, observability split) is agreed; in-process bus is testable with the fixture (or harness when merged) and correlation_id preserved end-to-end. Day 2 adds Redis and Kafka under the same rules for ADR-004.
