# ADR-008 — Fuzzy near-duplicate detection (enrichment) — Bryan & Emilio (Pair C)


|            |                                                 |
| ---------- | ----------------------------------------------- |
| **Owner**  | Pair C                                           |
| **Spec**   | IMP-018                                         |
| **Status** | Accepted (implemented)                          |
| **Scope**  | Enrichment → `dbo.job_postings` after promotion |

## Decision

Detect **near-duplicate job postings** after enrichment promotion using **embedding cosine similarity**, constrained to **same `company_id`** and a **rolling 30-day window** on `publish_date`. Ingestion fingerprint dedup (exact / storage hash) remains separate and earlier in the pipeline.

## Design Summary


| Topic                  | Choice                                                                                                | Rationale                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| **Signal**             | `text-embedding-3-small` (1536-d) via Azure OpenAI                                                    | Same family as skills taxonomy embeddings; recalibrate threshold if deployment changes.   |
| **Similarity**         | Cosine > **0.92** (env `DEDUP_COSINE_THRESHOLD`)                                                      | Balances false merges vs misses; tune with FP/FN eval.                                    |
| **Scope**              | Same company + half-open window `[anchor − 30d, anchor)`                                              | Avoids cross-employer merges; time box limits “repost” style dupes.                       |
| **Candidates**         | Survivors only (`is_duplicate IS NOT TRUE`); reuse cached embeddings and lazily backfill missing ones | Star-shaped clustering; no transitive closure through dup rows; avoids cold-start misses. |
| **Survivor**           | Field **completeness** score, then **newer `publish_date`**                                           | Keeps richer / fresher row as canonical.                                                  |
| **Failure / no match** | Treat as **unique**; persist `is_duplicate = false`, `duplicate_cluster_id = null` for **that** row   | Safe default when embed fails or similarity is low; if that row was the prior survivor, clear only that old cluster to avoid orphaned duplicate-only state. |
| **Promotion**          | Dedup runs **after** successful enrichment `UPDATE`; errors **logged**, promotion **not** rolled back | Availability over strict dedup consistency.                                               |
| **Embedding audit**    | Reuse shared Azure embedding helper with `audit_agent_name="enrichment-dedup"`                        | Keeps every dedup embedding HTTP attempt on the same `llm_audit_log` contract as taxonomy Step 4, including `cost_usd` estimates when token usage is available. |


## Persistence (`dbo.job_postings`)


| Column                 | Type           | Role                                                          |
| ---------------------- | -------------- | ------------------------------------------------------------- |
| `dedup_text_hash`      | `TEXT`         | SHA-256 of normalized dedup string; cache hit skips re-embed. |
| `dedup_embedding`      | `vector(1536)` | Stored embedding for comparisons.                             |
| `is_duplicate`         | `BOOLEAN`      | Non-survivor in a cluster when true.                          |
| `duplicate_cluster_id` | `UUID`         | Shared cluster id (UUID string).                              |


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


## Issue completion matrix

| GitHub issue requirement | Status | Delivered behavior / evidence |
| ------------------------ | ------ | ----------------------------- |
| Embedding text uses title + company name + key requirements | **Done** | `text.py` builds dedup text from `job_title`, `company_name`, and normalized `requirements` with `job_description` fallback. |
| Query same-company postings from last 30 days | **Done** | `fuzzy_dedup.py` constrains candidates to `company_id` plus half-open window `[anchor - 30d, anchor)`. |
| Compute pairwise cosine similarity between embeddings | **Done** | `vectors.py` normalizes vectors and computes cosine similarity in Python. |
| If similarity > 0.92, mark duplicate and assign cluster id | **Done** | `fuzzy_dedup.py` now applies strict `similarity > threshold` semantics. |
| Threshold configurable via `DEDUP_COSINE_THRESHOLD` | **Done** | `config.py` exposes the env-backed threshold with default `0.92`. |
| Survivor selection uses highest field completeness count | **Done** | `completeness.py` now counts populated dedup-relevant fields and uses recency only as the tie-breaker. |
| Store `is_duplicate` and `duplicate_cluster_id` on `job_postings` | **Done** | `job_postings_promotion.py` persists both flags; `duplicate_cluster_id` is stored as `UUID`. |
| Identical repost test deduplicates | **Done** | Covered in unit/E2E suites and replay cases. |
| Similar but different roles do not deduplicate | **Done** | Covered in unit/E2E suites and replay cases. |
| Same role at different companies does not deduplicate | **Done** | Covered in unit/E2E suites and replay cases. |
| Day 29 vs day 31 boundary behaves correctly | **Done** | Covered in env-gated matching E2E and replay cases. |
| Track false-positive and false-negative rates | **Done** | `dedup_threshold_calibration.py` + labeled cases + committed JSON report + findings doc. |
| Log every embedding API call to `dbo.llm_audit_log` | **Done** | Shared `_embed_texts_azure(..., audit_agent_name="enrichment-dedup")` path writes one audit row per HTTP attempt. |
| Write one-page findings doc | **Done** | Supporting artifact at `agents/docs/week 6/FINDINGS-fuzzy-dedup-bryan-emilio.md`. |
| Run `pytest agents/tests/ -v` with no regressions | **Done** | Final out-of-sandbox repo sweep: `237 passed, 2 warnings`. |

## Testing


| Layer             | What                                                                              | Command / note                                                            |
| ----------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Unit (dedup)**  | Mocked SQL + `_embed_texts_azure`; threshold, window, completeness, embed failure, dedup audit-agent propagation | `pytest agents/enrichment/tests/test_fuzzy_dedup.py`                      |
| **Unit (calibration)** | Labeled replay math, FP/FN accounting, scope gating, findings rendering | `pytest agents/enrichment/tests/test_dedup_calibration.py` |
| **Unit (promotion)** | `FuzzyDedupResult` persistence, dedup-after-promotion wiring; after merge with `development`, also temporal/Borderplex params on promotion `UPDATE` | `pytest agents/enrichment/tests/test_job_postings_promotion.py`           |
| **E2E matching**  | Real Postgres + Azure embeddings; 29d vs 31d window, near-dup vs different text, and live `llm_audit_log` insertion for `agent_name='enrichment-dedup'` | `pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e` |
| **E2E promotion** | Real DB + `EnrichmentAgent`; `run_fuzzy_dedup` mocked; asserts flag persistence   | `pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py`                   |

## Validation Findings

### What We Tested

- Promotion persistence/unit path with fabricated `FuzzyDedupResult` inputs, dedup-after-promotion wiring, and temporal/Borderplex column binding checks in `agents/enrichment/tests/test_job_postings_promotion.py` (the latter shared with the merged `development` enrichment promotion surface).
- Matching/unit path in `agents/enrichment/tests/test_fuzzy_dedup.py`, including threshold checks, half-open 30-day window params, survivor completeness arbitration, cached-vector reuse, and cold-start survivor backfill.
- Audit contract at the dedup call site: `_embed_texts_azure(..., audit_agent_name="enrichment-dedup")` for both current-row embedding and lazy survivor backfill.
- The shared helper now records one `llm_audit_log` row per embedding HTTP attempt, not only successful responses. Failed/rate-limited attempts are logged with `success = false`; `cost_usd` is computed from embedding token usage when the provider returns it.
- Live-path E2E coverage in `agents/tests/test_fuzzy_dedup_matching_e2e.py` now includes a real `llm_audit_log` assertion, not just dedup state assertions.
- Scenario coverage already checked into env-gated E2E tests:
  `agents/tests/test_fuzzy_dedup_matching_e2e.py` covers 29 vs 31 days, same-company different content, different companies, and repost merges.

### What We Found

- The write path is cleanly centralized: only `apply_fuzzy_dedup_result(...)` updates `is_duplicate` and `duplicate_cluster_id`.
- The matching path avoids the historical-cache blind spot by embedding in-window survivor candidates that do not yet have `dedup_embedding`.
- The current default threshold and survivor rules line up with the intended behavior in unit coverage: same-company reposts merge, different-company rows stay isolated, and richer/newer rows win survivor arbitration.
- The root `.env` source-of-truth issue was real. Before the fix, agent tests could silently inherit a different `.env` via `find_dotenv()`; after the fix, Week 6 tooling consistently uses the repo-root `.env`.
- A full live Week 6 validation now exists on the real Azure-backed database outside the sandbox: migrations completed, the matching E2E suite passed, and the promotion E2E suite passed.
- Repo-level regression is now green in the current local environment, not just the targeted Week 6 tests.
- Threshold calibration is now implemented as a labeled replay instead of a manual TODO. The current replay measures FP/FN directly from the same dedup text composition and shared Azure embedding helper used in production.
- The labeled replay currently favors `0.88` as the strongest next staging candidate (`TP=5`, `FP=0`, `TN=7`, `FN=0`) while the published default `0.92` remains the conservative production setting (`TP=3`, `FP=0`, `TN=7`, `FN=2`) until a broader staging replay validates the lower threshold against harder negatives.

### Exactly what changed to close the issue

- **Threshold semantics:** equality no longer merges; the live comparison is now strict `similarity > threshold`.
- **Survivor arbitration:** the old weighted heuristic was replaced with a literal populated-field count over dedup-relevant fields.
- **Cluster persistence:** `duplicate_cluster_id` moved from text semantics to a real `UUID` column with safe migration handling and stable string reads at the Python boundary.
- **Audit robustness:** dedup embedding calls use the shared Step 4 audit path and the migration layer now repairs agent-managed serial sequence drift, which fixed a real `llm_audit_log` primary-key collision seen during live E2E validation.
- **Calibration tracking:** FP/FN replay is now implemented in code, checked into the repo, and produces both machine-readable evidence and a one-page findings artifact.

### Recommendation

- Keep `DEDUP_COSINE_THRESHOLD=0.92` as the conservative production default for now, because it preserves the published Week 6 contract and avoids changing rollout behavior from a small replay alone.
- Use `0.88` as the next threshold candidate for a broader staging replay, because the current labeled set improves recall without increasing measured false positives.
- Keep the lazy backfill behavior. It materially improves cold-start recall without opening cross-company or out-of-window matches.
- Treat the implementation as issue-complete in code. The remaining work is operational follow-through: extend the labeled case file as new edge cases are discovered and rerun the calibration report when the embedding deployment changes.

### Data / Evidence

- 2026-04-01: `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_fuzzy_dedup.py -q` → `14 passed`
- 2026-04-01 (pre–`development` merge): `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_job_postings_promotion.py -q` → `11 passed` (fuzzy-dedup promotion tests only).
- After merge with `development`: the same module grows to **`17 passed`** — the original fuzzy-dedup/promotion cases plus six tests that assert `temporal_period` / `borderplex_subregion` are bound on promotion `UPDATE`s (dedup path mocked so `execute` counts stay stable).
- 2026-04-01 inside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py tables` → failed with `could not translate host name "pg-jobintel-cfa-dev.postgres.database.azure.com" to address`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py tables` → succeeded against the real Azure DB
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py migrate` → `Migrations complete`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -q` → `6 passed`
- 2026-04-01 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py -q` → `1 passed`
- 2026-04-02: `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_company_resolver.py -v` → `17 passed`
- 2026-04-02: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py -v` → `1 passed`
- 2026-04-02: `./agents/.venv/bin/python -m pytest agents/tests/ -v` → `217 passed, 5 skipped, 2 warnings`
- 2026-04-03 outside sandbox: `./agents/.venv/bin/python agents/scripts/db_check.py migrate` → `Migrations complete`
- 2026-04-03 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_database.py -q` → `5 passed, 1 warning`
- 2026-04-03 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_matching_e2e.py agents/tests/test_fuzzy_dedup_promotion_e2e.py -q` → `7 passed`
- 2026-04-03 outside sandbox: `./agents/.venv/bin/python -m pytest agents/tests/ -v` → `237 passed, 2 warnings`
- 2026-04-03 outside sandbox: `./agents/.venv/bin/python -m agents.scripts.dedup_threshold_calibration` → wrote `agents/data/reports/dedup_threshold_calibration.json` and `agents/docs/week 6/FINDINGS-fuzzy-dedup-bryan-emilio.md`
- 2026-04-03 calibration replay summary:
  - `0.88` → `TP=5`, `FP=0`, `TN=7`, `FN=0`, `FPR=0.000`, `FNR=0.000`
  - `0.92` → `TP=3`, `FP=0`, `TN=7`, `FN=2`, `FPR=0.000`, `FNR=0.400`

## Tradeoffs Acknowledged

- **Cost & latency:** One embed per posting on cache miss; cached when `dedup_text_hash` unchanged.
- **Operational:** Requires `AZURE_OPENAI_EMBEDDING_`*; embedding outages leave rows as non-duplicates for that run (no global reset).
- **Availability bias:** Best-effort dedup favors enrichment availability over strict dedup consistency on every run.
- **Lazy backfill cost:** Backfilling same-company, in-window survivors improves cold-start recall, but adds embedding cost during historical comparisons.
- **Tooling warning:** SQLAlchemy can emit `SAWarning: Did not recognize type 'vector'` when reflecting `job_postings` columns that include `dedup_embedding`. The enrichment E2E helpers (`agents/tests/db_seed_enrichment_e2e.py`, `agents/tests/fuzzy_dedup_e2e_helpers.py`) filter that warning around `inspect.get_columns` so pytest output stays clean; other ad-hoc reflection may still log the warning. It does not block migrations or live test execution.
- **Calibration scope:** The labeled replay is now part of the checked-in toolchain, but it is still a curated sample rather than a full production backfill.
- **Not a substitute** for ingestion dedup: fingerprint dedup still drops exact repeats at `raw_ingested_jobs`.

## References

- `docs/planning/ARCHITECTURE_DEEP.md` — enrichment / dedup
- `agents/scripts/dedup_metrics_report.py` — optional HTML metrics from DB
- `agents/scripts/dedup_threshold_calibration.py` — labeled FP/FN replay
- `agents/data/reports/dedup_threshold_calibration.json` — committed calibration evidence
