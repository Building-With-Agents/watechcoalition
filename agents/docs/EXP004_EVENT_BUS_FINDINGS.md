# EXP-004 Event Bus Findings

**Date:** March 12, 2026  
**Baseline commits reviewed:** `2bc888e2` (transport comparison runner + CLI, March 11, 2026) and `a2f57f53` (HTML report generator + README refactor, March 12, 2026)

## What I Tested

- The current event bus implementations in `agents/common/message_bus/` for in-process, Redis Streams, and Kafka.
- The normalized comparison harness in `agents/common/message_bus/comparison.py` using the standard 1,000-event deterministic scenario (`seed=42`).
- Consumer crash and replay at event 500 for replay-capable transports.
- Producer crash at event 500 by stopping publication halfway, measuring immediate loss, then resuming the remaining deterministic events.
- Checklist-path coverage in `agents/common/events/tests/test_event_bus.py` for publish/subscribe, delivery guarantees, and 1,000-event throughput.
- The CLI/report surfaces that turn the measurements into checked-in evidence files.

## What I Found

- The recent commits already put us in a good position for comparison work: `2bc888e2` added the common benchmark runner and `a2f57f53` added the HTML report, but neither covered producer-side crash loss.
- The missing producer-crash scenario is now implemented in the shared comparison layer and reported per transport.
- All three transports show the same producer-crash pattern in the fake-backend benchmark: 500 events are missing immediately after the producer stops at event 500, all 500 are recovered after resuming publication, and final loss is 0.
- Redis Streams and Kafka still show 100% consumer crash replay completeness at event 500. In-process still has no replay path, which matches its design.
- In-process remains the strongest Phase 1 candidate: highest throughput, lowest latency, no handler failures, and full correctness on the 1,000-event scenario.

## Recommendation

Use `InProcessEventBus` for Phase 1 and keep Redis Streams/Kafka as Phase 2 durability options. The benchmark evidence says the current in-process bus is correct and materially faster for the single-process walking skeleton, while the replay-capable transports remain available when persistence or multi-process recovery becomes a real requirement.

## Tradeoffs

- In-process gives the best speed and simplest operations, but it cannot replay after a process failure because nothing is persisted.
- Redis Streams and Kafka provide replay semantics and queue visibility, but they cost roughly 4x the end-to-end latency in the fake-backend benchmark and add infrastructure/consumer-group complexity.
- The new producer-crash measurement clarifies an important boundary: transports can recover already-published events, but they cannot recover events the producer never emitted. Recovery requires the producer to resume from the deterministic tail.

## Data/Evidence

- Comparison output: `agents/.venv/bin/python -m agents.common.message_bus.run_comparison --count 1000 --seed 42 --crash-at 500 --format markdown --output agents/docs/exp004_transport_results.md`
- Checked-in comparison table: [agents/docs/exp004_transport_results.md](exp004_transport_results.md)
- Checked-in HTML report: [agents/docs/exp004_transport_report.html](exp004_transport_report.html)
- Checklist test file: [agents/common/events/tests/test_event_bus.py](../common/events/tests/test_event_bus.py)
- Targeted verification: `agents/.venv/bin/python -m pytest agents/tests/test_transport_comparison.py agents/tests/test_transport_comparison_cli.py agents/common/events/tests/test_event_bus.py -q` -> 11 tests passed
- Representative benchmark snapshot from the checked-in markdown results:
  - `in_process`: publish `198243.92/s`, e2e `197980.60/s`, p95 `0.00 ms`, producer loss `500`, recovered `500`, final loss `0`
  - `redis_streams`: publish `188341.65/s`, e2e `46215.61/s`, p95 `13.14 ms`, replay `100%`, producer loss `500`, recovered `500`, final loss `0`
  - `kafka`: publish `173075.24/s`, e2e `45828.73/s`, p95 `13.25 ms`, replay `100%`, producer loss `500`, recovered `500`, final loss `0`
