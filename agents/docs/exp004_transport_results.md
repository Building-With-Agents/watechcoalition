# EXP-004 Transport Comparison

Scenario: `ingest_batch_to_normalization_complete` | Input events: `1000` | Seed: `42` | Replay: `enabled`
Best publish throughput: `in_process` / `in_memory` at `198243.92` events/sec
Best end-to-end throughput: `in_process` / `in_memory` at `197980.60` events/sec
Lowest p95 latency: `in_process` / `in_memory` at `0.00` ms
Producer crash at `500`: immediate loss `500` events; resumed recovery `500` events; complete after resume: `True`

| transport | backend | throughput_publish_events_per_sec | throughput_e2e_events_per_sec | latency_p50_ms | latency_p95_ms | latency_p99_ms | crash_replay_complete | replay_completeness_pct | producer_crash_published_before_crash | producer_crash_delivered_before_crash | producer_crash_loss_count | producer_resume_recovered_count | producer_resume_final_loss_count | producer_resume_complete | published_events | delivered_events | handler_failures | queue_depth | in_flight | correctness_passed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in_process | in_memory | 198243.92 | 197980.60 | 0.00 | 0.00 | 0.01 | N/A | N/A | 500 | 500 | 500 | 500 | 0 | true | 2000 | 2000 | 0 | N/A | N/A | true |
| redis_streams | fake_redis | 188341.65 | 46215.61 | 9.47 | 13.14 | 13.43 | true | 100.00 | 500 | 500 | 500 | 500 | 0 | true | 2000 | 2000 | 0 | 0 | 0 | true |
| kafka | fake_kafka | 173075.24 | 45828.73 | 9.66 | 13.25 | 13.54 | true | 100.00 | 500 | 500 | 500 | 500 | 0 | true | 2000 | 2000 | 0 | 0 | 0 | true |
