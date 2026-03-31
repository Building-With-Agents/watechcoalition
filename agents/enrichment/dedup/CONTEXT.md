# Fuzzy dedup — teammate handoff (Phase 0 → Week 6)

This package implements **IMP-018**: near-duplicate job postings via embedding cosine similarity, same-company constraint, rolling 30-day window, survivor by field completeness.

## What exists now (Phase 0)

- **`run_fuzzy_dedup(session, job_posting_id, *, threshold=None)`** in `fuzzy_dedup.py` — **stub**: logs `fuzzy_dedup_stub` and returns `FuzzyDedupResult(is_duplicate=False, stub=True)` with **no** reads/writes.
- **`FuzzyDedupResult`** in `types.py` — stable contract for the real implementation, including `matched_job_posting_id` so persistence can flip a prior survivor without changing the API later.
- **`config.py`** — env `DEDUP_COSINE_THRESHOLD` (default **0.92**), window length **30** days, anchor column name **`publish_date`**.

## What you implement next

1. **Dedup text:** `title | company_name | first 500 chars of requirements` (requirements may come from normalized_jobs / description — follow ARCHITECTURE_DEEP).
2. **Candidates:** same `company_id`, `is_duplicate = false`, `publish_date` in `[anchor - 30d, anchor)`; this keeps the 29-day case in-window, the 31-day case out-of-window, and prevents self-match on the anchor timestamp.
3. **Embeddings:** reuse `agents/skills_extraction/extractors/taxonomy.py` → `_embed_texts_azure`; add **`log_extraction_event`** with `agent_name` like `enrichment-dedup` (coordinate Issue #108 pattern).
4. **Persistence:** `dbo.job_postings.is_duplicate`, `duplicate_cluster_id` (already migrated in `agents/common/data_store/migrations.py`) are written only through `job_postings_promotion.apply_fuzzy_dedup_result`.
5. **Survivor:** highest field completeness; if a new row beats the survivor, flip flags and keep one cluster id.

## Integration point (not wired yet)

Call **`run_fuzzy_dedup`** from `job_postings_promotion.py` immediately after a successful enrichment promotion update. At that point:

- `EnrichmentAgent.process()` already opened the `Session`.
- `resolve_job_posting_row()` has both `job_posting_id` and `company_id`.
- rejected spam tiers have already exited, so dedup only runs for rows that remain on `job_postings`.

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEDUP_COSINE_THRESHOLD` | `0.92` | Cosine similarity above → near-duplicate |

## Tests

- Stub: `tests/test_fuzzy_dedup_stub.py` — import + safe return + log smoke.
- Add boundary tests (29 vs 31 days) and merge cases when live.

## References (repo)

- `agents/skills_extraction/extractors/taxonomy.py` — `_embed_texts_azure`, cosine pattern.
- `agents/common/llm_adapter.py` — `log_extraction_event`.
- `docs/planning/ARCHITECTURE_DEEP.md` — enrichment / fuzzy dedup spec.
