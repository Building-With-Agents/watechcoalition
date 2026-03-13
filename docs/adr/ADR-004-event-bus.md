# EXP-004 Event Bus — Findings & Testable Assets

March 2026 · In-process, Redis Streams, and Kafka message buses; normalized comparison and report.

---

## 1. What We Tested

**Transports.** We tested three implementations in `agents/common/message_bus/`: in-process (in-memory), Redis Streams (fake_redis), and Kafka (fake_kafka).

**Scenario.** The flow was ingest_batch_to_normalization_complete with 1,000 input events (seed 42); an optional 50k run is available via CLI.

**Metrics.** We measured publish and end-to-end throughput, latency (p50, p95, p99), and correctness (published/delivered/handler_failures, queue_depth and in_flight after drain). For Redis and Kafka we also captured peak queue depth and peak max in-flight during the run.

**Consumer crash at 500.** We evaluated replay and event loss for Redis and Kafka; in-process has no replay path by design.

**Producer crash at 500.** We stopped publication halfway, measured delivered vs lost, then resumed and reported final loss per transport.

**Other.** We verified correlation ID propagation end-to-end. We also used the CLI and report (CSV, Markdown, optional HTML), `test_event_bus.py` for publish/subscribe, delivery, and 1k throughput, plus transport and bus unit tests.

---

## 2. What We Found

### In-Process Bus

In-process showed the highest throughput (around 171k–198k publish/s, with similar end-to-end numbers) and sub-millisecond latency (p50 around 0.005 ms, p95 around 0.01 ms). Queue depth and in-flight are not applicable. On producer crash we saw 500 delivered and 0 final loss. There is no consumer-crash replay by design. It is the best fit for single-process and Phase 1.

### Redis Streams and Kafka

Both Redis Streams and Kafka had lower end-to-end throughput (around 31–46k events/s) and higher latency (around 12–18 ms p50–p99, or higher at 50k). Both passed correctness: 2,000 published and delivered, 0 handler failures, and queue empty after drain. Peak queue depth and peak max in-flight were visible (e.g. 1001 and 1 at 1k events). On consumer crash we saw 501 replayed with 100% completeness and 0 lost. On producer crash, 500 delivered and 0 final loss. Correlation ID propagation passed. Replay and observability make these suitable when scaling or when persistence and recovery are required.

---

## 3. Recommendation

For **Phase 1, single-process, or local development**, use **InProcessEventBus**. It is correct, fastest, and simplest, with no persistence or replay.

When **scaling or when durability and replay matter**, use **Redis Streams** for the ingestion-to-normalization handoff. Both Redis and Kafka showed 0 producer/consumer crash loss and full replay completeness in the benchmark; Redis achieved the overall best results.

---

## 4. Tradeoffs

**In-process.** It gives the best latency and throughput but no queue or in-flight visibility and no replay; a process failure loses in-memory state.

**Redis and Kafka.** They provide replay, crash resilience, and visibility into peak queue_depth and max_in_flight, at the cost of lower end-to-end throughput and higher latency in the fake-backend benchmark, plus extra infrastructure and consumer-group complexity. Producer-crash measurement showed that transports can recover already-published events; events that were never emitted require the producer to resume.

---

## 5. Data and Evidence

**CSV.** Results are in `agents/data/output/exp004_comparison.csv`, with columns for transport, backend, throughput, latency, queue_depth, in_flight after drain, max_in_flight peak, replay, producer_crash_*, events_lost_consumer_crash, and related fields.

**Charts.** The same directory contains `exp004_throughput.png`, `exp004_latency.png`, `exp004_observability.png`, `exp004_replay.png`, and `exp004_correlation_id.png`. For Redis and Kafka, queue_depth and max_in_flight in the charts are peak values during the run.

**Checked-in artifacts.** We have `agents/docs/exp004_transport_results.md`, optional `exp004_transport_report.html`, and findings in `agents/docs/EXP-004_CURRENT_TESTABLE_ASSETS.txt`.

**Report script.** Run `python -m agents.common.message_bus.run_comparison_and_report` to write the CSV, generate the charts, and log the summary.

**CLI.** For a custom run you can use `python -m agents.common.message_bus.run_comparison --count 1000 --seed 42 --crash-at 500 --format markdown --output agents/docs/exp004_transport_results.md` (or `--format csv` for CSV).

**Tests.** Run `pytest agents/tests/test_transport_comparison.py agents/tests/test_redis_streams_event_bus.py agents/tests/test_kafka_event_bus.py agents/common/events/tests/test_event_bus.py -v`; all pass.

---

## 6. Conclusion

In-process is the preferred bus for Phase 1 and single-process use; Redis or Kafka are the preferred options when scaling or when replay and observability are required. The evidence is in the CSV, charts, and tests described above.
