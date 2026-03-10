## EXP-002 — PostgreSQL Baseline Benchmarks

- **Experiment ID**: EXP-002  
- **Owner**: Fatima

### Objective

Establish baseline PostgreSQL performance characteristics for the Job Intelligence Engine, focusing on insert throughput, deduplication latency, Unicode handling, and concurrent write behavior against the `raw_ingested_jobs` table.

### Method

All tests used the EXP-002 benchmark script running against PostgreSQL via SQLAlchemy with the canonical `raw_ingested_jobs` schema. The script:
- Inserted batches of synthetic rows into `raw_ingested_jobs` and measured elapsed time with `time.perf_counter()`.
- Performed one `SELECT ... WHERE raw_payload_hash = :hash` per row to simulate dedup checks and recorded per-call latency.
- Inserted rows containing Japanese, Arabic, and emoji text into metadata fields, then read them back and compared values byte-for-byte.
- Spawned 5 threads, each inserting 100 rows concurrently, and checked for deadlocks, errors, or unexpected duplicate hashes.

All benchmark rows were deleted after each test to avoid polluting production tables.

### Results

| Metric                          | Value                     |
|---------------------------------|---------------------------|
| Insert throughput               | **28,805 rows/sec**       |
| Dedup median latency            | **0.24 ms**               |
| Dedup p99 latency               | **0.47 ms**               |
| Unicode roundtrip               | **pass** (Japanese, Arabic, emoji) |
| Concurrent access               | **pass** (5 threads, 500 rows, no deadlocks) |

### Interpretation

- **Insert throughput** of ~28.8k rows/sec is more than sufficient for the expected Phase 1 batch sizes (hundreds to low thousands of postings per run), leaving headroom for retries and additional indexing.
- **Dedup hash lookups** with median 0.24 ms and p99 0.47 ms mean per-record dedup in ingestion will not be a latency bottleneck, even when executed once per posting.
- **Unicode handling** is reliable: PostgreSQL preserved Japanese, Arabic, and emoji text without corruption, so the pipeline can safely ingest and process non-English job postings.
- **Concurrent inserts** at 5 threads and 500 total rows showed no deadlocks or duplicate key issues, which is adequate for the modest parallelism planned for Phase 1 agents.

### Recommendation for ADR-002

- **PostgreSQL is validated for Phase 1** as the database engine for agent-managed tables and the extended `job_postings` schema.
- **Dedup via `raw_payload_hash` lookup is fast enough at the projected scale**, so no additional caching or alternative dedup mechanism is required for Phase 1.
- **Concurrent access at 5 threads is stable**, indicating that the planned level of intra-agent parallelism will not require special locking strategies beyond standard SQLAlchemy usage.
- **Unicode handling is safe**, so the pipeline can treat text fields as UTF-8 by default without additional encoding workarounds.

