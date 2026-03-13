# EXP-004 Transport Comparison

Scenario: `ingest_batch_to_normalization_complete` | Input events: `1000` | Seed: `42` | Replay: `enabled`
Best publish throughput: `in_process` / `in_memory` at `163145.44` events/sec
Best end-to-end throughput: `in_process` / `in_memory` at `163041.71` events/sec
Lowest p95 latency: `in_process` / `in_memory` at `0.01` ms

| transport | backend | throughput_publish_events_per_sec | throughput_e2e_events_per_sec | latency_p50_ms | latency_p95_ms | latency_p99_ms | crash_replay_complete | replay_completeness_pct | published_events | delivered_events | handler_failures | queue_depth | in_flight | correctness_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in_process | in_memory | 163145.44 | 163041.71 | 0.01 | 0.01 | 0.01 | N/A | N/A | 2000 | 2000 | 0 | N/A | N/A | true |
| redis_streams | fake_redis | 131137.22 | 33753.68 | 12.30 | 17.27 | 17.60 | true | 100.00 | 2000 | 2000 | 0 | 0 | 0 | true |
| kafka | fake_kafka | 133788.21 | 35223.79 | 12.45 | 16.50 | 16.97 | true | 100.00 | 2000 | 2000 | 0 | 0 | 0 | true |
