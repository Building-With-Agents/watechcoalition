# EXP-004 Event Bus — Findings & Testable Assets (merged)

**Date:** March 2026  
**Scope:** In-process, Redis Streams, and Kafka message buses; normalized comparison and report.

---

## What we tested

- **Transports:** in_process (in-memory), Redis Streams (fake_redis), Kafka (fake_kafka) in `agents/common/message_bus/`.
- **Scenario:** ingest_batch_to_normalization_complete, 1,000 input events (seed 42); optional 50k via CLI.
- **Metrics:** Publish and e2e throughput, latency (p50/p95/p99), correctness (published/delivered/handler_failures, queue_depth and in_flight after drain), peak queue depth and peak max in-flight during the run (Redis/Kafka).
- **Consumer crash at 500:** Replay and event loss for Redis/Kafka; in-process has no replay path.
- **Producer crash at 500:** Stop publication halfway, measure delivered vs lost, then resume; final loss reported per transport.
- **Other:** Correlation ID propagation; CLI and report (CSV, Markdown, optional HTML); `test_event_bus.py` (publish/subscribe, delivery, 1k throughput); transport and bus unit tests.

---

## What we found

- **In-process:** Highest throughput (~171k–198k publish/s, similar e2e), sub-ms latency (p50 ~0.005 ms, p95 ~0.01 ms). No queue_depth/in_flight (N/A). Producer crash: 500 delivered, 0 final loss. No consumer-crash replay (by design). Best for single-process / Phase 1.
- **Redis Streams / Kafka:** Lower e2e throughput (~31–46k events/s) and higher latency (~12–18 ms p50–p99, or higher at 50k). Both pass correctness (2,000 published/delivered, 0 handler failures, queue empty after drain). Peak queue depth and peak max in-flight are visible (e.g. 1001 and 1 at 1k events). Consumer crash: 501 replayed, 100% completeness, 0 lost. Producer crash: 500 delivered, 0 final loss. Correlation ID propagation passed. Replay and observability make them suitable when scaling or when persistence/recovery is required.

---

## Recommendation

- **Phase 1 / single-process / local dev:** Use **InProcessEventBus** — correct, fastest, and simplest; no persistence or replay.
- **When scaling or when durability/replay matters:** Use **Redis Streams or Kafka** for the ingestion → normalization handoff; both show 0 producer/consumer crash loss and full replay completeness in the benchmark.

---

## Tradeoffs

- **In-process:** Best latency and throughput, no queue/in-flight visibility, no replay; process failure loses in-memory state.
- **Redis/Kafka:** Replay, crash resilience, and peak queue_depth/max_in_flight visibility; lower e2e throughput and higher latency in the fake-backend benchmark, plus extra infrastructure and consumer-group complexity. Producer-crash measurement shows: transports can recover already-published events; events never emitted require the producer to resume (deterministic tail).

---

## Data/Evidence

- **CSV:** `agents/data/output/exp004_comparison.csv` (transport, backend, throughput, latency, queue_depth, in_flight after drain, max_in_flight peak, replay, producer_crash_*, events_lost_consumer_crash, etc.).
- **Charts (peak queue depth / in-flight):** Same directory — `exp004_throughput.png`, `exp004_latency.png`, `exp004_observability.png`, `exp004_replay.png`, `exp004_correlation_id.png`. For Redis/Kafka, queue_depth and max_in_flight in charts are peak during the run.
- **CLI:** `python -m agents.common.message_bus.run_comparison --count 1000 --seed 42 --crash-at 500 --format markdown --output agents/docs/exp004_transport_results.md` (or `--format csv`).
- **Report script:** `python -m agents.common.message_bus.run_comparison_and_report` — writes CSV, generates charts, prints summary.
- **Checked-in:** `agents/docs/exp004_transport_results.md`, optional `exp004_transport_report.html`; findings: `agents/docs/EXP-004_CURRENT_TESTABLE_ASSETS.txt`.
- **Tests:** `pytest agents/tests/test_transport_comparison.py agents/tests/test_redis_streams_event_bus.py agents/tests/test_kafka_event_bus.py agents/common/events/tests/test_event_bus.py -v` (all pass).

---

**Conclusion:** In-process is the preferred Phase 1 / single-process bus; Redis or Kafka are the preferred options when scaling or when replay and observability are required. Evidence is in the CSV, charts, and tests above.
