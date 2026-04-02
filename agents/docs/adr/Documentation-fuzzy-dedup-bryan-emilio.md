# ADR-008 — Fuzzy near-duplicate detection (enrichment) — Bryan & Emilio (Pair C)


|            |                                                 |
| ---------- | ----------------------------------------------- |
| **Owner**  | Pair C                                           |
| **Spec**   | IMP-018                                         |
| **Status** | Accepted (implemented)                          |
| **Scope**  | Enrichment → `dbo.job_postings` after promotion |


> **Note:** `agents/docs/adr/ADR-006` is observability. Root `docs/adr/ADR-007` is the multi-agent framework; **ingestion** cross-source dedup is **ADR-003**. This ADR records **embedding fuzzy** dedup only.

## Decision

Detect **near-duplicate job postings** after enrichment promotion using **embedding cosine similarity**, constrained to **same `company_id`** and a **rolling 30-day window** on `publish_date`. Ingestion fingerprint dedup (exact / storage hash) remains separate and earlier in the pipeline.

## Design Summary


| Topic                  | Choice                                                                                                | Rationale                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Signal**             | `text-embedding-3-small` (1536-d) via Azure OpenAI                                                    | Same family as skills taxonomy embeddings; recalibrate threshold if deployment changes.   |
| **Similarity**         | Cosine ≥ **0.92** (env `DEDUP_COSINE_THRESHOLD`)                                                      | Balances false merges vs misses; tune with FP/FN eval.                                    |
| **Scope**              | Same company + half-open window `[anchor − 30d, anchor)`                                              | Avoids cross-employer merges; time box limits “repost” style dupes.                       |
| **Candidates**         | Survivors only (`is_duplicate IS NOT TRUE`); reuse cached embeddings and lazily backfill missing ones | Star-shaped clustering; no transitive closure through dup rows; avoids cold-start misses. |
| **Survivor**           | Field **completeness** score, then **newer `publish_date`**                                           | Keeps richer / fresher row as canonical.                                                  |
| **Failure / no match** | Treat as **unique**; persist `is_duplicate = false`, `duplicate_cluster_id = null` for **that** row   | Safe default when embed fails or similarity is low; if that row was the prior survivor, clear only that old cluster to avoid orphaned duplicate-only state. |
| **Promotion**          | Dedup runs **after** successful enrichment `UPDATE`; errors **logged**, promotion **not** rolled back | Availability over strict dedup consistency.                                               |
| **Embedding audit**    | Reuse shared Azure embedding helper with `audit_agent_name="enrichment-dedup"`                        | Keeps every dedup embedding call on the same `llm_audit_log` contract as taxonomy Step 4. |


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
| Embeddings + audit  | `agents/skills_extraction/extractors/taxonomy.py` — `_embed_texts_azure`   |
| Result type         | `agents/enrichment/dedup/types.py` — `FuzzyDedupResult`                    |
| DB writes for flags | `agents/enrichment/job_postings_promotion.py` — `apply_fuzzy_dedup_result` |
| Migrations          | `agents/common/data_store/migrations.py`                                   |
| Detail              | `agents/enrichment/dedup/CONTEXT.md`                                       |


## Testing


| Layer             | What                                                                              | Command / note                                                            |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Unit (dedup)**  | Mocked SQL + `_embed_texts_azure`; threshold, window, completeness, embed failure, dedup audit-agent propagation | `pytest agents/enrichment/tests/test_fuzzy_dedup.py`                      |
| **Unit (promotion)** | `FuzzyDedupResult` persistence, dedup-after-promotion wiring; after merge with `development`, also temporal/Borderplex params on promotion `UPDATE` | `pytest agents/enrichment/tests/test_job_postings_promotion.py`           |
| **E2E matching**  | Real Postgres + Azure embeddings; 29d vs 31d window, near-dup vs different text, and live `llm_audit_log` insertion for `agent_name='enrichment-dedup'` | `pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e` |
| **E2E promotion** | Real DB + `EnrichmentAgent`; `run_fuzzy_dedup` mocked; asserts flag persistence   | `pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py`                   |


## Workspace status on April 1, 2026

- The implementation is materially complete in code: fuzzy matching, survivor arbitration, cached embeddings, DB persistence, and unit coverage are all present.
- Agent-side local bootstrapping now enforces the **repo root** `.env` as the only `.env` file loaded by the Week 6 test path and dedup tooling. In particular, `agents/conftest.py` no longer falls back to `find_dotenv()`, which previously allowed an unrelated parent or CWD `.env` to change E2E behavior.
- The repo-root `.env` in this workspace points `PYTHON_DATABASE_URL` at the Azure PostgreSQL development host `pg-jobintel-cfa-dev.postgres.database.azure.com`. That target was unreachable inside the sandbox, but it was reachable outside the sandbox on **April 1, 2026**, which allowed a full live Week 6 validation run against the real database.
- During that live validation, `run_migrations(get_engine())` added the missing dedup schema on the real DB, including `job_postings.dedup_embedding` and `job_postings.dedup_text_hash`, which had previously been the only blocker for the matching E2E suite.

## Validation Findings

### What We Tested

- Promotion persistence/unit path with fabricated `FuzzyDedupResult` inputs, dedup-after-promotion wiring, and temporal/Borderplex column binding checks in `agents/enrichment/tests/test_job_postings_promotion.py` (the latter shared with the merged `development` enrichment promotion surface).
- Matching/unit path in `agents/enrichment/tests/test_fuzzy_dedup.py`, including threshold checks, half-open 30-day window params, survivor completeness arbitration, cached-vector reuse, and cold-start survivor backfill.
- Audit contract at the dedup call site: `_embed_texts_azure(..., audit_agent_name="enrichment-dedup")` for both current-row embedding and lazy survivor backfill.
- Live-path E2E coverage in `agents/tests/test_fuzzy_dedup_matching_e2e.py` now includes a real `llm_audit_log` assertion, not just dedup state assertions.
- Scenario coverage already checked into env-gated E2E tests:
  `agents/tests/test_fuzzy_dedup_matching_e2e.py` covers 29 vs 31 days, same-company different content, different companies, and repost merges.

### What We Found

- The write path is cleanly centralized: only `apply_fuzzy_dedup_result(...)` updates `is_duplicate` and `duplicate_cluster_id`.
- The matching path avoids the historical-cache blind spot by embedding in-window survivor candidates that do not yet have `dedup_embedding`.
- The current default threshold and survivor rules line up with the intended behavior in unit coverage: same-company reposts merge, different-company rows stay isolated, and richer/newer rows win survivor arbitration.
- The root `.env` source-of-truth issue was real. Before the fix, agent tests could silently inherit a different `.env` via `find_dotenv()`; after the fix, Week 6 tooling consistently uses the repo-root `.env`.
- A full live Week 6 validation now exists on the real Azure-backed database outside the sandbox: migrations completed, the matching E2E suite passed, and the promotion E2E suite passed.
- The largest remaining uncertainty is calibration rather than mechanics. The implementation is now live-validated, but false-positive and false-negative **rates** still need a broader replay or labeled sample beyond the six checked-in E2E scenarios.

### Recommendation

- Keep `DEDUP_COSINE_THRESHOLD=0.92` as the default until the env-gated E2E suite is run against a database with Azure embedding credentials.
- Treat the checked-in E2E scenarios as the source of truth for rollout validation, then capture real FP/FN counts from a staging or replay run before changing the threshold.
- Keep the lazy backfill behavior. It materially improves cold-start recall without opening cross-company or out-of-window matches.
- For **local Docker validation**, keep the repo-root `.env` authoritative:
  set `PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:<POSTGRES_PASSWORD>@localhost:<POSTGRES_PORT>/talent_finder` in the root `.env`, matching `.env.docker`, then start Docker and run migrations before the Week 6 E2E suite.

### Data / Evidence

- 2026-04-01: `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_fuzzy_dedup.py -q` → `14 passed`
- 2026-04-01 (pre–`development` merge): `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_job_postings_promotion.py -q` → `11 passed` (fuzzy-dedup promotion tests only).
- After merge with `development`: the same module grows to **`17 passed`** — the original fuzzy-dedup/promotion cases plus six tests that assert `temporal_period` / `borderplex_subregion` are bound on promotion `UPDATE`s (dedup path mocked so `execute` counts stay stable).
- 2026-04-01 inside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py tables` → failed with `could not translate host name "pg-jobintel-cfa-dev.postgres.database.azure.com" to address`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py tables` → succeeded against the real Azure DB
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py migrate` → `Migrations complete`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -q` → `6 passed`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py -q` → `1 passed`

## Tradeoffs Acknowledged

- **Cost & latency:** One embed per posting on cache miss; cached when `dedup_text_hash` unchanged.
- **Operational:** Requires `AZURE_OPENAI_EMBEDDING_`*; embedding outages leave rows as non-duplicates for that run (no global reset).
- **Availability bias:** Best-effort dedup favors enrichment availability over strict dedup consistency on every run.
- **Lazy backfill cost:** Backfilling same-company, in-window survivors improves cold-start recall, but adds embedding cost during historical comparisons.
- **Tooling warning:** SQLAlchemy can emit `SAWarning: Did not recognize type 'vector'` when reflecting `job_postings` columns that include `dedup_embedding`. The enrichment E2E helpers (`agents/tests/db_seed_enrichment_e2e.py`, `agents/tests/fuzzy_dedup_e2e_helpers.py`) filter that warning around `inspect.get_columns` so pytest output stays clean; other ad-hoc reflection may still log the warning. It does not block migrations or live test execution.
- **Calibration gap:** Unit coverage is strong for contract and control flow, but semantic threshold calibration still depends on live embeddings.
- **Not a substitute** for ingestion dedup: fingerprint dedup still drops exact repeats at `raw_ingested_jobs`.

## References

- `docs/planning/ARCHITECTURE_DEEP.md` — enrichment / dedup
- `agents/scripts/dedup_metrics_report.py` — optional HTML metrics from DB
