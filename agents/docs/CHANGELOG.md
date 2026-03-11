# Changelog

All notable changes to the agents pipeline are documented here.

---

## EXP-004 scope expansion (Emilio)

**Failure payloads, synthetic generators, typed events, and correlation propagation.**

### Changes

- **Failure payloads**
  - `agents/ingestion/events.py`: `source_failure_payload` extended with `error_type`, `severity` (default `"critical"`), and `error_reason`.
  - `agents/normalization/events.py`: `normalization_failed_payload` extended with the same three fields (`error_type`, `severity`, `error_reason`).
- **Synthetic generators** (`agents/common/events/synthetic_events.py`)
  - `generate_synthetic_normalization_complete(count, seed, typed=False)` — deterministic NormalizationComplete events.
  - `generate_synthetic_source_failures(count, seed, typed=False)` — deterministic SourceFailure events.
  - `generate_synthetic_normalization_failed(count, seed, typed=False)` — deterministic NormalizationFailed events.
  - All accept optional `typed=True` to yield typed event wrappers.
- **Typed events** (`agents/common/events/typed_events.py`)
  - `IngestBatchEvent`, `NormalizationCompleteEvent`, `SourceFailureEvent`, `NormalizationFailedEvent` — wrappers around `EventEnvelope` that validate `payload["event_type"]`.
- **Harness**
  - `ingest_batch_harness.py`: `generate_synthetic_ingest_batches(..., typed=False)`; when `typed=True`, yields `IngestBatchEvent` instances.
- **Tests**
  - `agents/common/events/tests/test_synthetic_events.py` — shape, `agent_id`, payload keys, determinism for synthetic generators.
  - `agents/common/events/tests/test_correlation_propagation.py` — one test that builds IngestBatch + NormalizationComplete with the same `correlation_id` and asserts they match (synthetic only).

---

## Test Harness (Emilio)

**EXP-004 Event Bus — synthetic IngestBatch generator and harness structure tests.**

### Changes

- **Added** `agents/common/events/ingest_batch_harness.py`
  - `generate_synthetic_ingest_batches(count=1000, seed=42)` — deterministic generator that yields `EventEnvelope` instances with IngestBatch payloads.
  - `assert_valid_ingest_batch_envelope(event)` — raises `ValueError` with a clear message if envelope or payload is invalid.
  - `is_valid_ingest_batch_envelope(event)` — returns `True`/`False` for single-event validation.
  - Constants: `INGEST_BATCH_PAYLOAD_KEYS`, `INGEST_BATCH_PAYLOAD_STR_KEYS`, `INGEST_BATCH_PAYLOAD_INT_KEYS` for payload validation.
- **Added** `agents/common/events/tests/__init__.py` — package marker for event tests.
- **Added** `agents/common/events/tests/test_harness_events.py` — 16 tests that validate only the harness (see **Harness tests explained** below).

No message bus implementation, throughput, crash recovery, or replay tests are included — those are owned by the event-bus experiment (Bryan).

---

### Harness tests explained

The file `agents/common/events/tests/test_harness_events.py` contains **16 tests** in six groups. Each test only checks the harness output (no bus, no network). Run them with:

```bash
cd agents && pytest common/events/tests/test_harness_events.py -v
```

#### 1. Envelope shape (3 tests)

These ensure every event is a proper `EventEnvelope` with the right metadata.

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_each_event_is_event_envelope** | Generates 1,000 events and checks each is an instance of `EventEnvelope`. | The harness never yields a raw dict or wrong type; downstream code can always treat items as `EventEnvelope`. |
| **test_agent_id_and_schema_version** | For all 1,000 events, asserts `agent_id == "ingestion_agent"` and `schema_version == "1.0"`. | Events are correctly tagged for the ingestion agent and schema version, so routing and versioning work. |
| **test_correlation_id_and_event_id_and_timestamp_set** | Generates 100 events and checks each has non-empty `correlation_id`, `event_id`, and non-null `timestamp`. | Every event is traceable and has a timestamp; no missing envelope fields. |

#### 2. Payload shape (3 tests)

These ensure every event’s payload has all IngestBatch keys and correct types.

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_assert_valid_passes_for_all_events** | Generates 1,000 events and runs `assert_valid_ingest_batch_envelope(event)` on every one (expects no exception). | All 1,000 events pass full validation; the harness output is valid for the whole run. |
| **test_first_last_middle_pass_validation** | Generates 1,000 events and checks `is_valid_ingest_batch_envelope(event)` is True for events at index 0, 499, and 999. | The validation helper agrees on valid events at start, middle, and end of the stream. |
| **test_payload_has_ingest_batch_keys** | Generates 10 events and verifies each payload has the eight required keys and `event_type == "IngestBatch"`. | Payloads match the IngestBatch contract (all required keys present, correct event type). |

#### 3. Count (2 tests)

These ensure the generator yields exactly the requested number of events.

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_default_count_is_1000** | Calls the generator with `count=1000, seed=42` and asserts the collected list has length 1000. | The default “full harness” run really yields 1,000 events. |
| **test_custom_count** | Calls the generator with `count=50, seed=1` and asserts the list has length 50. | The `count` argument is respected; you can generate any size run (e.g. 50 or 1000). |

#### 4. Determinism (2 tests)

These ensure the same seed always produces the same events, and a different seed produces different events.

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_same_seed_same_events** | Runs the generator twice with `count=1000, seed=42`, then compares the first and last event: same `event_id`, same `batch_id`, same full payload. | Same `(count, seed)` always produces the same events in the same order; experiments are reproducible. |
| **test_different_seed_different_events** | Generates 10 events with seed 1 and 10 with seed 2, then asserts the first event’s `event_id` and `batch_id` differ. | Changing the seed changes the stream; seeds are not ignored. |

#### 5. Uniqueness (1 test)

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_no_duplicate_event_ids** | Collects all 1,000 `event_id` values and checks the set has size 1,000 (all unique). | No duplicate event IDs in a single run; each event is uniquely identifiable. |

#### 6. Validation helper — bad structure (5 tests)

These ensure the validation helper rejects invalid events and accepts valid ones.

| Test | What it does | What you can infer |
|------|----------------|--------------------|
| **test_valid_event_does_not_raise** | Generates one event and calls `assert_valid_ingest_batch_envelope(events[0])`; expects no exception. | The assert helper does not raise on a correctly shaped event. |
| **test_valid_event_returns_true** | Same one event; asserts `is_valid_ingest_batch_envelope(events[0])` is True. | The boolean helper returns True for valid events. |
| **test_missing_payload_key_raises** | Builds an event whose payload is missing `error_count`; expects `assert_valid_ingest_batch_envelope` to raise `ValueError` with “missing required keys”, and `is_valid_ingest_batch_envelope` to return False. | The validator catches missing IngestBatch keys. |
| **test_wrong_payload_type_raises** | Builds an event with `total_fetched` as the string `"not-an-int"`; expects a `ValueError` mentioning “must be int” and `is_valid_ingest_batch_envelope` False. | Type errors in the payload are detected. |
| **test_wrong_event_type_raises** | Builds an event with `event_type="OtherEvent"`; expects `ValueError` with “must be 'IngestBatch'” and `is_valid_ingest_batch_envelope` False. | The validator enforces that the payload is actually an IngestBatch event. |

---

### How it works

- **Determinism:** For each index `i` in `0..count-1`, the harness derives:
  - `event_id` via `uuid.uuid5(NAMESPACE_DNS, f"harness-{seed}-{i}")`.
  - `timestamp` from a fixed base (2025-01-01 00:00:00) plus `timedelta(seconds=i)`.
  - `correlation_id` = `f"harness-{seed}"` for the whole run.
  - Payload via `ingest_batch_payload()` with `batch_id=f"harness-batch-{seed}-{i}"`, `source="harness"`, `region_id="us"`, and integer fields from `(seed + i)` modulo small constants.
- **Event shape:** Each event is an `EventEnvelope` with `agent_id="ingestion_agent"`, `schema_version="1.0"`, and a payload that matches the contract from `agents/ingestion/events.ingest_batch_payload()` (`event_type`, `batch_id`, `source`, `region_id`, `total_fetched`, `staged_count`, `dedup_count`, `error_count`).
- **Validation:** The helper checks that the envelope has the expected `agent_id`, that the payload is a dict with all required keys, that `event_type == "IngestBatch"`, and that each key has the correct type (str vs int). Tests use this to ensure every generated event is valid and to assert that invalid payloads are rejected.

---

### How to use it to test the event bus

1. **Run harness structure tests (no bus required)**  
   From repo root (with venv activated):
   ```bash
   cd agents && pytest common/events/tests/test_harness_events.py -v
   ```

2. **Generate the same 1,000 events in your bus experiment**  
   In the code that implements or tests the event bus (in-process, Redis Streams, or Kafka):
   ```python
   from agents.common.events.ingest_batch_harness import generate_synthetic_ingest_batches

   for event in generate_synthetic_ingest_batches(count=1000, seed=42):
       bus.publish(event)  # or your bus’s publish API
   ```
   Using the same `count` and `seed` (e.g. 1000 and 42) ensures every run gets the same 1,000 events, so throughput, crash-at-500, and replay experiments are comparable.

3. **Validate a single event (e.g. after consume)**  
   To check that an event produced or consumed by the bus has correct structure:
   ```python
   from agents.common.events.ingest_batch_harness import (
       assert_valid_ingest_batch_envelope,
       is_valid_ingest_batch_envelope,
   )

   # Raises ValueError with a clear message if invalid
   assert_valid_ingest_batch_envelope(event)

   # Or check without raising
   if is_valid_ingest_batch_envelope(event):
       process(event)
   ```

4. **Typical experiment flow**  
   - Publish 1,000 events from the harness to the bus.  
   - Consume with the normalization agent (or a test consumer).  
   - Measure throughput and latency.  
   - Simulate consumer crash at event 500 and verify no event loss (or measure loss).  
   - Simulate producer crash and measure loss.  
   - Test replay using the same 1,000 events (same seed) for reproducibility.

The harness does not implement or test the bus; it only provides a deterministic, validated stream of IngestBatch events so the event-bus implementation can be tested under identical load.

---

## For Bryan: Using the harness to test the event bus

This section is a quick reference so you can plug the harness into your event_bus tests (in-process, Redis, Kafka) and get replayable, identical load every run.

### Functions you can use

| Function | Where | What it does | How to use it |
|----------|--------|--------------|----------------|
| **`generate_synthetic_ingest_batches(count=1000, seed=42)`** | `agents.common.events.ingest_batch_harness` | Yields `EventEnvelope` instances with IngestBatch payloads. Same `(count, seed)` always gives the same events in the same order. | Iterate and publish each event to your bus, or feed to a consumer. Use `count=1000, seed=42` for the standard replayable run. |
| **`assert_valid_ingest_batch_envelope(event)`** | Same module | Validates envelope + IngestBatch payload. Raises `ValueError` with a clear message if invalid (missing key, wrong type, wrong `event_type`). | Call after consuming an event from the bus to ensure structure is still correct; use in tests to fail fast. |
| **`is_valid_ingest_batch_envelope(event)`** | Same module | Same checks as above; returns `True` or `False` (does not raise). | Use when you want to branch: `if is_valid_ingest_batch_envelope(event): process(event)`. |

**Optional constants** (if you need to check payload keys yourself):  
`INGEST_BATCH_PAYLOAD_KEYS`, `INGEST_BATCH_PAYLOAD_STR_KEYS`, `INGEST_BATCH_PAYLOAD_INT_KEYS`.

### How to implement in your event_bus tester

1. **Import the generator** (and optionally the validation helper):
   ```python
   from agents.common.events.ingest_batch_harness import (
       generate_synthetic_ingest_batches,
       assert_valid_ingest_batch_envelope,  # optional
   )
   ```

2. **Produce the same 1,000 events every run** (replayable load):
   ```python
   for event in generate_synthetic_ingest_batches(count=1000, seed=42):
       bus.publish(event)   # or your bus’s equivalent
   ```

3. **In a consumer test, validate after consume** (optional but recommended):
   ```python
   consumed = bus.consume_one()  # or your API
   assert_valid_ingest_batch_envelope(consumed)
   ```

4. **Crash / replay experiments:** Use the same `count=1000, seed=42` so event 0, 500, 999, etc. are identical across runs. You can stop after 500, crash, restart, and replay with the same generator to compare behavior.

### Commands (run from repo root, venv activated)

| Command | What it does |
|---------|----------------|
| **`python -m agents.common.events.view_harness`** | Generates 5 events (seed 42), validates them, prints first/last event and uniqueness/determinism. Quick sanity check. |
| **`python -m agents.common.events.view_harness --count 1000`** | Full 1,000 events; validates all, prints first and last only. Use to confirm the full harness run. |
| **`python -m agents.common.events.view_harness --count 1 --json`** | Prints the first event as JSON (e.g. for debugging or tooling). |
| **`python -m agents.common.events.view_harness --count 10 --seed 99`** | 10 events with seed 99 (different stream than 42). |
| **`cd agents && pytest common/events/tests/test_harness_events.py -v`** | Runs the 16 harness-structure tests (envelope, payload, count, determinism, uniqueness, validation). No bus required. |

**Note:** Run Python commands from the **repo root** (`watechcoalition`) so `agents` is importable, or set `PYTHONPATH` to the repo root.
