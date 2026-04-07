# Pair C (Week 7) — Work split & production checklist

**Owners:** Bryan + Emilio  
**Theme:** Step 4 — Canonical role clustering (HDBSCAN + embeddings) · Step 5 — `role_snapshot_weekly` + salary percentiles · `EmergenceAlert`  
**Branch:** `week-07/canonical-role-clustering` (or current Pair C branch)

This file is the **execution contract** for the pair: who does what, how it must be built for **production**, what to read, and how to **test**.

---

## How to use this doc

1. Read **References (both)** once.  
2. **Person 1** and **Person 2** work in parallel where possible; use the **integration boundary** so merges do not fight.  
3. **Person 2** owns **`models.py` / `migrations.py`** ordering: append migration steps; do not drop or reorder existing steps (repo rule).  
4. Land **`.cursor/rules/canonical-role-clustering.mdc` early** (Person 2) with **final** table and event shapes once schema is agreed (even if implementation is stubbed).

---

## References (read in this order)

| Order | Document | Why |
|------|----------|-----|
| 1 | [`reading-analytics-pipeline-architecture.md`](./reading-analytics-pipeline-architecture.md) | Where steps 4–5 sit in the 13-step analytics chain; ordering constraints. |
| 2 | [`IMP-023-unsupervised-clustering-canonical-roles-bryan-emilio-reading.md`](./IMP-023-unsupervised-clustering-canonical-roles-bryan-emilio-reading.md) | HDBSCAN intuition, embedding input, thresholds, emergence **filter** (not all noise). |
| 3 | [`WEEK-07-canonical-role-clustering-bryan-emilio-runbook.md`](./WEEK-07-canonical-role-clustering-bryan-emilio-runbook.md) | Checklist, evaluation criteria, findings template. |
| 4 | [`docs/planning/ARCHITECTURE_DEEP.md`](../../../docs/planning/ARCHITECTURE_DEEP.md) | Canonical table sketches (`canonical_roles`, `role_snapshot_weekly`), event catalog (`EmergenceAlert`). **Reconcile** with runbook column names before coding. |
| 5 | [`agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md`](../runbooks/WEEK07_TESTING_RUNBOOK.md) | DB verification commands; update queries if your final schema uses `canonical_role_id` / different column names than examples. |
| 6 | **Embedding precedent** | `agents/skills_extraction/extractors/taxonomy.py` — `_embed_texts_azure()`; dedup usage in `agents/enrichment/dedup/fuzzy_dedup.py` (audit agent name, batch embed, no PII in logs). |
| 7 | **Integration schema** | `.cursor/rules/integration-schema.mdc` — dedup columns on `job_postings`; clustering should run on **deduplicated / survivor** logic as required by curriculum (issue #135 gate). |
| 8 | **Pair B** | Coordinate **salary percentile helper** signature (p25, p50, p75, p95) for step 5; document the agreed import path in `.cursor/rules/canonical-role-clustering.mdc`. |

---

## Integration boundary (do not cross without syncing)

| Artifact | Owner | Contract |
|----------|--------|----------|
| `agents/analytics/clustering/*` (pure logic + optional small IO helpers) | **Person 1** | Exposes **testable functions** and **dataclasses** (e.g. inputs: list of posting feature rows + embeddings matrix; outputs: cluster labels per row, cluster summaries, emergence candidate list). |
| `agents/common/data_store/models.py`, `migrations.py` | **Person 2** | **Single source of truth** for table/column names; Person 1 imports ORM types only after they exist—until then, use shared **Pydantic/dataclasses** in `clustering/` that Person 2 maps in the analytics runner. |
| `agents/analytics/agent.py` (or submodules called from it) | **Person 2** orchestrates | Loads DB rows → calls Person 1 pipeline → persists → emits events. |
| `EmergenceAlert` payload + bus publish | **Person 2** | Defined in `agents/common/events/` per repo patterns; Person 1 returns **plain dicts** matching the agreed payload shape. |
| `.cursor/rules/canonical-role-clustering.mdc` | **Person 2** (draft) + **both** (review) | Final schemas, env vars, HDBSCAN defaults, event payload, embedding deployment name env. |

---

## Person 1 — Clustering & embeddings (“algorithm path”)

### Scope

- Create **`agents/analytics/clustering/`** as a **real package** (`__init__.py`), not a dump folder.
- **Embedding text builder:** deterministic string from title, skills, tools, responsibilities, seniority (and any fields Pair C agrees from enriched/`JobProfile` / DB joins). Document field order and separators so a small text change does not silently break clusters.
- **Embeddings:** call the **same Azure embedding path** as the rest of the pipeline (`_embed_texts_azure` or a thin wrapper), with a **dedicated `audit_agent_name`** (e.g. `analytics-clustering`) so `llm_audit_log` stays attributable. Batch sensibly; handle partial failure without crashing the whole run (log + skip or retry policy).
- **HDBSCAN:** default implementation, parameters from **environment variables** (e.g. `CLUSTER_MIN_CLUSTER_SIZE`, `CLUSTER_MIN_SAMPLES`, `CLUSTER_SELECTION_EPSILON`, metric). Use **`hdbscan`** (already in `agents/requirements.txt`).
- **Thresholds:** implement runbook + IMP-023 rules: **skip clustering** if total eligible postings is **fewer than 500**; **drop** clusters with **fewer than 10** members (treat as noise or “review” per agreed policy); log structured reasons (counts only—no PII).
- **Cluster labels:** most-common title with dominance rule; optional **LLM label** via `get_adapter` with **same failure behavior** as other agents (retries + audit log; do **not** block persisting clusters if LLM fails—fallback label).
- **Emergence candidates:** implement IMP-023 **filters** (quality, skills vs existing clusters, multi-employer) on top of HDBSCAN noise — return a **structured list** for Person 2 to persist/emit.
- **Unit tests** under `agents/analytics/clustering/tests/` (or `agents/analytics/tests/`) with **mocked** embeddings and **fixed** random seeds where needed.

### Production requirements (Person 1)

- **structlog** only; **no PII** (no raw descriptions in logs; log hashes, counts, cluster ids).
- **No secrets** in code; all from `os.getenv`.
- **Pure functions** where possible — easier tests and clearer failure modes.
- **Docstrings** on public functions: args, returns, and “what happens when embedding API fails.”

### Done when (Person 1)

- [ ] Package exists; `pytest` for clustering passes without live API keys when mocks are used.
- [ ] README or module docstring at top of package listing **env vars** and defaults.
- [ ] Handoff type: documented **Python structure** (dataclass/TypedDict) for “per posting: id, label, features” and “per cluster: id, member ids, label, top skills/tools.”

---

## Person 2 — Schema, snapshots, events, wiring (“data & pipeline path”)

### Scope

- **`canonical_roles`** and **`role_snapshot_weekly`** in **`agents/common/data_store/models.py`** + **`migrations.py`**.  
  - **Reconcile** runbook columns (`description`, `member_count`, `centroid_embedding`, `computed_at`, …) with **`ARCHITECTURE_DEEP.md`** (`cluster_centroid` JSONB vs vector, `representative_titles`, etc.). Pick **one** physical schema; document deviations from either doc in `.mdc`.
- **Posting → role mapping:** decide and migrate: e.g. **`job_postings.canonical_role_id`** (nullable TEXT/UUID-as-text consistent with repo) and/or a small mapping table if you need history per run. Downstream step 5 **must** group by **`canonical_role_id`**, not raw title.
- **Step 5 — `role_snapshot_weekly`:** for each `(week_start, canonical_role_id)`, compute posting counts, **p25/p50/p75/p95** salaries using **Pair B’s helper** once available; until then implement a **clear temporary** path (e.g. `percentile` from `agents/common/message_bus/comparison.py` on extracted numeric salaries) and **TODO** linked to Pair B.
- **`EmergenceAlert`:** add typed payload in `agents/common/events/` (follow existing patterns), publish via message bus where other analytics events go; **orchestrator-only** consumption of `*Alert` per architecture—verify routing in `contracts` / orchestration stubs.
- **Wire into `agents/analytics/agent.py`:** replace long-term stub behavior with a **batch path** that respects step ordering (shared reading: step 5 after step 4). Integrate **minimum data guard** (50 vs 500 — document: global guard vs clustering-only guard).
- **`.cursor/rules/canonical-role-clustering.mdc`:** integration contract for other pairs (schemas, events, env vars, HDBSCAN defaults).
- **Findings doc** (runbook template): one page for the team.

### Production requirements (Person 2)

- **Transactions:** persist canonical roles + posting updates + snapshots in a **consistent** order; define behavior on mid-run failure (idempotent re-run or run id).
- **Migrations:** idempotent `CREATE TABLE IF NOT EXISTS` / `ADD COLUMN IF NOT EXISTS` consistent with `migrations.py` style in repo.
- **SQL:** parameterize queries; no string-concatenated user content.
- **Health check:** extend `AnalyticsAgent.health_check()` to reflect real dependencies (DB reachable, fixture vs production mode if applicable).

### Done when (Person 2)

- [ ] `python agents/scripts/db_check.py tables` shows new tables after migrate.
- [ ] Step 5 rows verify with queries aligned to **your** column names (update WEEK07 testing runbook examples if needed).
- [ ] At least one **integration test** that runs migration + a small in-memory or test-DB flow (or documented manual runbook path if DB-only).

---

## Testing strategy (both own parts)

| Layer | What | Who |
|-------|------|-----|
| **Unit** | Text builder, label logic, HDBSCAN wrapper on numpy fixtures, emergence filter | Person 1 |
| **Unit** | SQLAlchemy model round-trip, snapshot math with fake rows | Person 2 |
| **Integration** | Load N real or seeded postings → cluster → write DB → query `role_snapshot_weekly` | Both (pair session) |
| **Manual / QA** | Top clusters: inspect titles for coherence; noise rate sanity | Both — runbook criteria |
| **Lint** | `cd agents && ruff check . && ruff format .` | Both before PR |
| **Regression** | `cd agents && pytest agents/tests/ -v` (and new tests paths) | Both |

### Commands (from repo root)

```bash
cd agents && pip install -r requirements.txt
cd agents && ruff check . && ruff format .
cd agents && pytest agents/analytics/clustering/tests/ -v   # after Person 1 adds tests
cd agents && pytest agents/tests/ -v
python agents/scripts/db_check.py query "SELECT COUNT(*) FROM dbo.canonical_roles"
python agents/scripts/db_check.py query "SELECT week_start, canonical_role_id, posting_count FROM dbo.role_snapshot_weekly LIMIT 10"
```

---

## Coordination cadence

- **Day 1:** Agree **physical schema** (draw 5-minute ERD); Person 2 lands **migrations + empty models**; Person 1 scaffolds **`clustering/`** with fake data tests.  
- **Mid-week:** Freeze **`EmergenceAlert`** payload keys; Person 1 returns matching dict keys.  
- **Before merge:** Pair B percentile **import path** confirmed or TODO explicitly in `.mdc` and code.

---

## Definition of done (Pair C)

- [ ] Steps **4** and **5** run in order as part of the analytics batch path (even if other analytics steps remain stubs).  
- [ ] `canonical_roles` populated from real clustering run on sufficiently large sample.  
- [ ] `role_snapshot_weekly` keyed by **`canonical_role_id`** + `week_start` with salary percentiles.  
- [ ] `EmergenceAlert` emitted when filtered emergence candidates exist (test or manual verification).  
- [ ] Production practices above satisfied; **ruff + pytest** green.  
- [ ] `.cursor/rules/canonical-role-clustering.mdc` merged.  
- [ ] Runbook **findings** section completed.

---

## Glossary (shared language)

| Term | Meaning |
|------|--------|
| **Embedding** | Numeric vector representing text; similar jobs → vectors close together. |
| **HDBSCAN** | Density clustering; finds variable-shaped groups and **noise** points without fixing “k clusters” upfront. |
| **Canonical role** | One stable cluster label + id representing many noisy titles. |
| **Emergence candidate** | Outliers/noise that pass **quality filters** — possible new role, not “all noise.” |
