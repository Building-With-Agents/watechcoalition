# ADR-008 — Fuzzy near-duplicate detection (enrichment) — Bryan & Emilio (Pair C)


|            |                                                 |
| ---------- | ----------------------------------------------- |
| **Owner**  | Bryan                                           |
| **Spec**   | IMP-018                                         |
| **Status** | Accepted (implemented)                          |
| **Scope**  | Enrichment → `dbo.job_postings` after promotion |


> **Note:** `agents/docs/adr/ADR-006` is observability. Root `docs/adr/ADR-007` is the multi-agent framework; **ingestion** cross-source dedup is **ADR-003**. This ADR records **embedding fuzzy** dedup only.

## Decision

Detect **near-duplicate job postings** after enrichment promotion using **embedding cosine similarity**, constrained to **same `company_id`** and a **rolling 30-day window** on `publish_date`. Ingestion fingerprint dedup (exact / storage hash) remains separate and earlier in the pipeline.

## Key findings


| Topic                  | Choice                                                                                                | Rationale                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Signal**             | `text-embedding-3-small` (1536-d) via Azure OpenAI                                                    | Same family as skills taxonomy embeddings; recalibrate threshold if deployment changes.   |
| **Similarity**         | Cosine ≥ **0.92** (env `DEDUP_COSINE_THRESHOLD`)                                                      | Balances false merges vs misses; tune with FP/FN eval.                                    |
| **Scope**              | Same company + half-open window `[anchor − 30d, anchor)`                                              | Avoids cross-employer merges; time box limits “repost” style dupes.                       |
| **Candidates**         | Survivors only (`is_duplicate IS NOT TRUE`); reuse cached embeddings and lazily backfill missing ones | Star-shaped clustering; no transitive closure through dup rows; avoids cold-start misses. |
| **Survivor**           | Field **completeness** score, then **newer `publish_date`**                                           | Keeps richer / fresher row as canonical.                                                  |
| **Failure / no match** | Treat as **unique**; persist `is_duplicate = false`, `duplicate_cluster_id = null` for **that** row   | Safe default when embed fails or similarity is low; if that row was the prior survivor, clear only that old cluster to avoid orphaned duplicate-only state. |
| **Promotion**          | Dedup runs **after** successful enrichment `UPDATE`; errors **logged**, promotion **not** rolled back | Availability over strict dedup consistency.                                               |


## Persistence (`dbo.job_postings`)


| Column                 | Type           | Role                                                          |
| ---------------------- | -------------- | ------------------------------------------------------------- |
| `dedup_text_hash`      | `TEXT`         | SHA-256 of normalized dedup string; cache hit skips re-embed. |
| `dedup_embedding`      | `vector(1536)` | Stored embedding for comparisons.                             |
| `is_duplicate`         | `BOOLEAN`      | Non-survivor in a cluster when true.                          |
| `duplicate_cluster_id` | `TEXT`         | Shared cluster id (UUID string).                              |


**Dedup text:** `title \| company_name \|` first **500** chars of `normalized_jobs.requirements`, else `job_description` (normalized in `text.py`).

## Implementation map


| Piece               | Location                                                                   |
| ------------------- | -------------------------------------------------------------------------- |
| Algorithm           | `agents/enrichment/dedup/fuzzy_dedup.py` — `run_fuzzy_dedup`               |
| Result type         | `agents/enrichment/dedup/types.py` — `FuzzyDedupResult`                    |
| DB writes for flags | `agents/enrichment/job_postings_promotion.py` — `apply_fuzzy_dedup_result` |
| Migrations          | `agents/common/data_store/migrations.py`                                   |
| Detail              | `agents/enrichment/dedup/CONTEXT.md`                                       |


## Testing


| Layer             | What                                                                              | Command / note                                                            |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Unit**          | Mocked SQL + `_embed_texts_azure`; threshold, window, completeness, embed failure | `pytest agents/enrichment/tests/test_fuzzy_dedup.py`                      |
| **E2E matching**  | Real Postgres + Azure embeddings; 29d vs 31d window, near-dup vs different text   | `pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e` |
| **E2E promotion** | Real DB + `EnrichmentAgent`; `run_fuzzy_dedup` mocked; asserts flag persistence   | `pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py`                   |


## Tradeoffs

- **Cost & latency:** One embed per posting on cache miss; cached when `dedup_text_hash` unchanged.
- **Operational:** Requires `AZURE_OPENAI_EMBEDDING_`*; embedding outages leave rows as non-duplicates for that run (no global reset).
- **Not a substitute** for ingestion dedup: fingerprint dedup still drops exact repeats at `raw_ingested_jobs`.

## References

- `docs/planning/ARCHITECTURE_DEEP.md` — enrichment / dedup
- `agents/scripts/dedup_metrics_report.py` — optional HTML metrics from DB
