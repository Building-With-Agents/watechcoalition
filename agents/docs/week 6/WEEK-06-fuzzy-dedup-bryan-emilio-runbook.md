# WEEK-06 — Fuzzy Deduplication with Embedding Similarity

| | |
|---|---|
| **Owner(s)** | Bryan + Emilio |
| **Timing** | Early-to-Mid Week 6 |
| **Stakes** | High |
| **Output** | Fuzzy dedup pipeline with embedding similarity, configurable threshold, and cluster survivor selection |
| **Timebox** | 3–4 hours |

---

### Pre-Reading

Read before starting this runbook:

- **[IMP-018: Fuzzy Deduplication with Embedding Similarity](readings/IMP-018-fuzzy-dedup-embedding-similarity-bryan-emilio-reading.md)** — Embedding-based duplicate detection with configurable cosine threshold (0.92 default), cluster survivor selection by field completeness, and threshold calibration tracking.

### External References

- [Azure OpenAI Embeddings API](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/embeddings) — The pipeline already uses `text-embedding-3-small` for taxonomy resolution (Step 4 in `taxonomy.py`). Reuse this same model and deployment for dedup embeddings — do not introduce a new dependency.
- [NumPy: Linear Algebra (np.linalg.norm)](https://numpy.org/doc/stable/reference/routines.linalg.html) — Cosine similarity is computed using normalized dot products with numpy, matching the existing pattern in `taxonomy.py` (lines 448, 503-504).
- [HDBSCAN Documentation](https://hdbscan.readthedocs.io/en/latest/) — Hierarchical density-based clustering. Understand `min_cluster_size` and `min_samples` parameters for grouping near-duplicate clusters.
- [Record Linkage (Wikipedia)](https://en.wikipedia.org/wiki/Record_linkage) — Background on deduplication and entity resolution approaches in data processing pipelines.

---

## The Question

How do you detect near-duplicate job postings using embedding similarity when exact matching is insufficient, and how do you select a cluster survivor when multiple versions of the same posting exist?

Job boards frequently have the same role reposted by the same company days apart with minor wording changes. Exact title matching misses these. Embedding similarity catches near-duplicates, but the threshold matters: too low and you merge different roles, too high and duplicates slip through. The 0.92 cosine threshold is the starting default (Decision #39 — EBS), but you need to track false positive and false negative rates to propose calibration later. And when you find a cluster of duplicates, you need a principled way to pick the survivor — not random, but by completeness.

## What You Have (Scaffolding on `development`)

- **`agents/enrichment/enrichment_agent.py`** — Enrichment Agent from Week 5 ("lite" phase). You are expanding this to full Phase 1.
- **`agents/common/types/job_profile.py`** — `JobProfile` Pydantic model with `title`, `company_name`, `requirements`, and other fields.
- **`job_postings` table** — Existing postings with title, company, and requirements data from normalization.
- **`agents/common/events/`** — Event definitions including `SkillsExtracted` (consumed) and `RecordEnriched` (emitted).
- **`agents/skills_extraction/extractors/taxonomy.py`** — **Reference implementation** for Azure OpenAI embeddings + numpy cosine similarity. Reuse the same `_embed_texts_azure()` pattern (lines 340-410) and `np.linalg.norm` + dot product cosine computation (lines 448, 503-504). Do not introduce sentence-transformers or scikit-learn — the pipeline already uses `text-embedding-3-small`.
- **`agents/common/llm_adapter.py`** — Contains `log_extraction_event()` (line 86) for writing to `dbo.llm_audit_log`. Your dedup embedding calls must log through this function for cost tracking. Issue [#108](https://github.com/Building-With-Agents/watechcoalition/issues/108) (closed) delivered the shared pattern: mirror taxonomy Step 4 embedding audit rows (`agents/skills_extraction/extractors/taxonomy.py`, `agents/skills_extraction/tests/test_taxonomy_embedding_audit.py`).

## What You Must Build

- Embedding computation for each posting using title + company name + key requirements
- Pairwise cosine similarity comparison against existing postings (same company, last 30 days)
- Duplicate marking when similarity > 0.92 with cluster assignment
- Cluster survivor selection based on field completeness count
- `job_postings` columns populated: `is_duplicate BOOLEAN DEFAULT FALSE`, `duplicate_cluster_id TEXT` (UUID string)
- Configurable threshold via environment variable (default 0.92)

## Task Checklist

- [ ] Implement embedding computation for each posting: title + company name + key requirements concatenated
- [ ] For each new posting, query existing postings from the same company within the last 30 days
- [ ] Compute pairwise cosine similarity between embeddings
- [ ] If similarity > 0.92 → mark `is_duplicate = TRUE`, assign `duplicate_cluster_id`
- [ ] Make the 0.92 threshold configurable via environment variable (e.g., `DEDUP_COSINE_THRESHOLD`)
- [ ] Implement cluster survivor selection: keep the posting with the highest field completeness count
- [ ] Store `is_duplicate` and `duplicate_cluster_id` on `job_postings` table
- [ ] Test: identical repost (same company, same title, 2 days apart) → should deduplicate
- [ ] Test: similar but different roles (same company, different title) → should NOT deduplicate
- [ ] Test: same role at different companies → should NOT deduplicate
- [ ] Test: posting at day 29 vs day 31 → boundary test for 30-day window
- [ ] Track false positive and false negative rates for threshold calibration proposal
- [ ] Log every embedding API call to `dbo.llm_audit_log` via `log_extraction_event()` from `agents/common/llm_adapter.py`, consistent with taxonomy Step 4 (closed [#108](https://github.com/Building-With-Agents/watechcoalition/issues/108); use a distinct `agent_name` such as `enrichment-dedup`)
- [ ] Write one-page findings doc with: What I Tested, What I Found, Recommendation, Tradeoffs, Data/Evidence

## Current Status — April 1, 2026

- [x] Dedup text composition is implemented in `agents/enrichment/dedup/text.py` as `title | company_name | requirements/job_description`.
- [x] Matching is constrained to same `company_id` and a half-open rolling 30-day window in `agents/enrichment/dedup/fuzzy_dedup.py`.
- [x] The cosine threshold is configurable through `DEDUP_COSINE_THRESHOLD` with a default of `0.92`.
- [x] Survivor arbitration is implemented with weighted completeness plus publish-date tiebreak in `agents/enrichment/dedup/completeness.py`.
- [x] Persistence for `is_duplicate`, `duplicate_cluster_id`, `dedup_text_hash`, and `dedup_embedding` is wired through `agents/enrichment/job_postings_promotion.py` and `agents/common/data_store/migrations.py`.
- [x] Unit coverage is green today:
  `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_fuzzy_dedup.py -q` and `./agents/.venv/bin/python -m pytest agents/enrichment/tests/test_job_postings_promotion.py -q`.
- [x] Real-DB E2E coverage exists for boundary matching, repost merges, cross-company isolation, promotion persistence, and live `llm_audit_log` insertion.
- [x] A live run completed on **April 1, 2026** outside the sandbox using the repo-root `.env` Azure database target.
- [x] `run_migrations(get_engine())` was applied successfully to the real DB before rerunning matching E2E tests.
- [x] `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -q` passed `6/6` outside the sandbox.
- [x] `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py -q` passed `1/1` outside the sandbox.

## Real DB + Docker Note

All Week 6 agent tests and dedup tooling should now read the **repo-root `.env` only**. They no longer fall back to a different `.env` discovered from the current working directory or a parent folder.

In this workspace, the repo-root `.env` currently targets the Azure PostgreSQL development host, and that target was used for the successful live validation run on **April 1, 2026**.

If you want the Week 6 E2E suite to hit the Dockerized Postgres instead of Azure, keep the same root-`.env` rule and simply point that root `.env` at the Docker URL:

1. Set `PYTHON_DATABASE_URL` in the **root `.env`** to the local Docker connection string that matches `.env.docker`.
2. Start Postgres with `docker compose --env-file .env.docker up postgres -d`.
3. Run migrations against that same root-`.env` database target.
4. Run:
   `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_matching_e2e.py -m fuzzy_dedup_e2e -v`
5. Run:
   `./agents/.venv/bin/python -m pytest agents/tests/test_fuzzy_dedup_promotion_e2e.py -v`

As of **April 1, 2026**, the root `.env` has the required Azure embedding variables set and has already been validated successfully against the real Azure DB outside the sandbox. Docker remains a supported alternate target, but the key rule is unchanged: the **root `.env`** is the source of truth.

## Evaluation Criteria

| Criterion | Target |
|---|---|
| Embedding composition | Includes title + company + requirements (not just title) |
| Company constraint | Only compares postings from the same company |
| 30-day window | Correctly computed as rolling 30 days (not calendar month) |
| Threshold configurability | Reads from env var, defaults to 0.92 |
| Survivor selection | Picks most complete posting (highest field count), not random |
| Boundary test (30-day) | Posting at day 29 deduplicates, posting at day 31 does not |
| False positive/negative tracking | Rates measured and documented for Sprint 4 calibration |
| Embedding cost tracking | Every embedding API call logged to `llm_audit_log` via `log_extraction_event()` |

**Decision rule:** The 0.92 threshold is the starting default (Decision #39 — EBS). Teams track FP/FN rates and propose calibration in Sprint 4 retrospective. The 30-day window is a rolling window from posting date, not a calendar month. Survivor selection is by field completeness — the most complete posting is kept.

## Questions to Ask Yourself

- The pipeline already uses Azure OpenAI `text-embedding-3-small` for taxonomy resolution. Why reuse it instead of introducing sentence-transformers? What are the tradeoffs?
- How do you compute "field completeness count"? Is it just non-null field count, or do you weight some fields higher?
- What happens when a cluster has 3+ duplicates? Does survivor selection still work correctly?
- Is the 30-day window computed from the new posting's date backwards, or from the existing posting's date forwards? Does it matter?
- At 1,000 postings, how many pairwise comparisons are you making? Is this O(n^2) within each company, and is that acceptable?
- What if a posting's title changes slightly between reposts but the requirements are identical? Does your embedding catch that?

## Cursor Prompts for Research

- "Compare sentence embedding models for near-duplicate detection — what model gives the best tradeoff between speed and accuracy for job posting similarity?"
- "Explain cosine similarity thresholds for near-duplicate detection — how do you calibrate a threshold and what are typical values for text deduplication?"
- "How do production deduplication systems handle cluster management — what happens when a new posting matches an existing cluster vs creating a new one?"

## Findings Doc Template

### What I Tested
### What I Found
### Recommendation
### Tradeoffs Acknowledged
### Data / Evidence

## Reference Files

- [`docs/planning/ARCHITECTURE_DEEP.md`](https://github.com/Building-With-Agents/watechcoalition/blob/development/docs/planning/ARCHITECTURE_DEEP.md) (Enrichment Agent specification, fuzzy dedup)
- [`docs/planning/ARCHITECTURAL_DECISIONS.md`](https://github.com/Building-With-Agents/watechcoalition/blob/development/docs/planning/ARCHITECTURAL_DECISIONS.md) (Decision #39 — Dedup threshold calibration)
- [`agents/enrichment/enrichment_agent.py`](https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/enrichment_agent.py)
- [`agents/common/types/job_profile.py`](https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/common/types/job_profile.py)
- [`agents/common/events/`](https://github.com/Building-With-Agents/watechcoalition/tree/development/agents/common/events) (SkillsExtracted, RecordEnriched)
- [`agents/skills_extraction/extractors/taxonomy.py`](https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/skills_extraction/extractors/taxonomy.py) — Reference implementation for Azure OpenAI embeddings + numpy cosine similarity
- [`agents/common/llm_adapter.py`](https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/common/llm_adapter.py) — `log_extraction_event()` for cost audit logging
- [Issue #108](https://github.com/Building-With-Agents/watechcoalition/issues/108) — Closed; Step 4 embedding costs in `llm_audit_log` (dedup should follow the same logging contract)
