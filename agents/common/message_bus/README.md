# Message Bus

Transport-agnostic event bus used by the agent pipeline. All implementations share the same contract: events are routed by `payload["event_type"]`, the transport unit is `EventEnvelope`, and control events (`*Failed`, `*Alert`, `SourceFailure`, `DemandAnomaly`) may only be consumed by `orchestration-agent`.

## Package layout

| Module | Purpose |
|--------|---------|
| `contracts.py` | Shared typing, validation, and subscription policy (event type, subscriber id, restricted control events) |
| `base.py` | `EventBusBase` abstract interface: `publish`, `subscribe`, `consume_available` (where applicable) |
| `in_process.py` | In-memory bus (Phase 1 default); counters: `published_events`, `delivered_events`, `handler_failures` |
| `redis_streams.py` | Redis Streams bus: `xadd` / `xreadgroup` / `xack`; optional `queue_depth`, `in_flight` |
| `kafka.py` | Kafka bus: `send` / `poll` / per-message `commit`; optional `queue_depth`, `in_flight` |
| `candidate_factories.py` | Builds transport candidates (in-process, fake/live Redis, fake/live Kafka) for comparison |
| `comparison.py` | Benchmark harness: run one or many buses, collect throughput/latency/replay metrics |
| `run_comparison.py` | CLI for comparison → Markdown, CSV, or JSON |
| `generate_report.py` | CLI for comparison → single HTML report with embedded Chart.js graphs |

## Using the buses

**In-process**  
No extra deps. `publish(event)` delivers synchronously to subscribed handlers. Use for Phase 1 pipeline.

**Redis Streams**  
`pip install redis`. `publish` appends to a stream; `subscribe(event_type, handler, subscriber_id=...)` registers a handler; `consume_available(replay_pending=..., stop_on_handler_error=...)` reads and dispatches. Failed entries can be left pending for replay.

**Kafka**  
`pip install kafka-python` for live brokers. Same `publish` / `subscribe` pattern. `consume_available` polls and commits on success; failed messages stay uncommitted for replay. Use `--redis-url` / `--kafka-bootstrap-servers` in the CLIs to use live backends instead of in-memory fakes.

## Transport comparison

The comparison harness runs a fixed scenario (synthetic `IngestBatch` → handler emits `NormalizationComplete`) and collects:

- **Throughput:** publish events/sec and end-to-end events/sec  
- **Latency:** p50, p95, p99 (ms)  
- **Parity:** `published_events`, `delivered_events`, `handler_failures`, `queue_depth`, `in_flight`  
- **Replay (optional):** crash mid-run then drain; reports `crash_replay_complete` and `replay_completeness_pct`

**Programmatic use**

- `run_transport_comparison(bus, transport=..., backend=..., scenario=..., replay_bus_factory=...)` → one `TransportComparisonResult`
- `compare_transport_candidates(candidates, scenario=...)` → list of results (one per transport/backend)
- `format_results_markdown_table(results)` and `results_to_rows(results)` for Markdown table or CSV/JSON-friendly dicts

**CLI (text output)**

```bash
python -m agents.common.message_bus.run_comparison [options]
```

From repo root. Useful options: `--count 1000`, `--seed 42`, `--skip-replay` to disable crash/replay, `--format markdown|csv|json`, `--output <path>`, `--redis-url <url>`, `--kafka-bootstrap-servers <host:port,...>`.

## HTML report

Generates a single HTML file with bar charts (throughput, latency, replay) and a full results table. No server required; open the file in a browser.

```bash
python -m agents.common.message_bus.generate_report [options]
```

From repo root. Options: `--count 1000`, `--seed 42`, `--crash-at 500`, `--skip-replay`, `--output <path>` (default `agents/docs/exp004_transport_report.html`), `--redis-url`, `--kafka-bootstrap-servers`.
