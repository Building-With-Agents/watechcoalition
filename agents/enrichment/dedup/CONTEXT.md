# Fuzzy dedup — IMP-018 (live implementation)

Near-duplicate job postings via embedding cosine similarity, same-`company_id` constraint, rolling 30-day window, survivor by field completeness.

## Public API

- **`run_fuzzy_dedup(session, job_posting_id, *, threshold=None)`** in [`fuzzy_dedup.py`](fuzzy_dedup.py) — loads the row, builds dedup text, ensures an embedding (Azure via `_embed_texts_azure` with `audit_agent_name="enrichment-dedup"`), compares to **survivors** in the window, returns **`FuzzyDedupResult` with `stub=False`** on all paths (including soft failures that yield “unique”).
- **`FuzzyDedupResult`** in [`types.py`](types.py) — `matched_job_posting_id` supports persistence flipping a prior survivor via [`apply_fuzzy_dedup_result`](../../enrichment/job_postings_promotion.py).
- **`config.py`** — env `DEDUP_COSINE_THRESHOLD` (default **0.92**), window **30** days, anchor **`publish_date`**.

## Database columns (`dbo.job_postings`)

| Column | Purpose |
|--------|---------|
| `dedup_text_hash` | SHA-256 of normalized dedup string; skip re-embed when unchanged |
| `dedup_embedding` | `vector(1536)` — cached embedding for comparisons (see `migrations.py`) |
| `is_duplicate` / `duplicate_cluster_id` | Cluster membership; written **only** by `job_postings_promotion.apply_fuzzy_dedup_result` |

**Threshold note:** `0.92` is calibrated for the same embedding family as taxonomy audit (`text-embedding-3-small` in audit logs). If the embedding deployment changes, recalibrate `DEDUP_COSINE_THRESHOLD`.

## Algorithm (summary)

1. **Dedup text:** `title | company_name | first 500 chars` of `normalized_jobs.requirements` if present, else `job_description` (see [`text.py`](text.py)).
2. **Window:** half-open **`[anchor - 30d, anchor)`** on `publish_date` (UTC-aware).
3. **Candidates:** same `company_id`, **`is_duplicate IS NOT TRUE`**, `dedup_embedding IS NOT NULL`, excluding self.
4. **Similarity:** cosine in Python (`vectors.py`); compare current vector to each survivor; take **best** match (star clustering — no transitive chaining through duplicates).
5. **Survivor arbitration:** [`completeness.py`](completeness.py) (salary, location, description length); **recency** tie-break. Reuse matched survivor’s `duplicate_cluster_id` if set; else new **UUID4** cluster id.

## Idempotency / re-runs

- Same dedup text → same hash → **reuse** stored embedding (no second Azure call).
- Edited description/requirements → new hash → re-embed → cluster membership may change.
- If a prior **survivor** reruns as unique, persistence clears that row's prior cluster membership to avoid leaving orphaned duplicate-only clusters.

## Integration (wired)

After a successful enrichment promotion update, [`apply_enrichment_to_job_postings`](../../enrichment/job_postings_promotion.py) calls `_apply_fuzzy_dedup_after_promotion`, which runs `run_fuzzy_dedup` then `apply_fuzzy_dedup_result` inside a nested transaction/savepoint. Dedup failures are logged; promotion is **not** rolled back.

## Env vars

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEDUP_COSINE_THRESHOLD` | `0.92` | Cosine similarity ≥ threshold → near-duplicate candidate |

## Tests

- [`enrichment/tests/test_fuzzy_dedup.py`](../../enrichment/tests/test_fuzzy_dedup.py) — mocked session + `_embed_texts_azure`: threshold, window params, company filter, completeness, hash skip, embedding failure.
- [`enrichment/tests/test_fuzzy_dedup_stub.py`](../../enrichment/tests/test_fuzzy_dedup_stub.py) — missing row smoke; threshold default smoke.
- Promotion + persistence: [`enrichment/tests/test_job_postings_promotion.py`](../../enrichment/tests/test_job_postings_promotion.py).

## References

- [`agents/skills_extraction/extractors/taxonomy.py`](../../../skills_extraction/extractors/taxonomy.py) — `_embed_texts_azure(..., audit_agent_name=...)`
- [`agents/common/llm_adapter.py`](../../../common/llm_adapter.py) — `log_extraction_event`
- `docs/planning/ARCHITECTURE_DEEP.md` — enrichment / fuzzy dedup spec
