# Week 6 — Fabian: Streamlit observability foundations (findings)

## What I Tested

- `streamlit run agents/dashboard/app.py` with PostgreSQL populated from prior ingestion/normalization runs (when available).
- Empty database: no rows in `raw_ingested_jobs`, `job_ingestion_runs`, `normalized_jobs` — confirmed pages show metrics as N/A or zero, info callouts, and no uncaught exceptions.
- JSON-only mode (no `PYTHON_DATABASE_URL`): **Ingestion Overview** and **Normalization Quality** show a clear warning; journey pages still use `pipeline_run.json`.
- Unit tests: `agents/tests/test_dashboard_observability.py` (metric helpers), `agents/tests/test_streamlit_app.py` (including `_db_available` / read-only URL cases).
- **Regression:** Full suite `pytest agents/tests/` — counts vary with environment (**193+** when DB available; **~235** in a fully green local run). **Caveat:** tests that run **Crawl4AI / Playwright** fail if browsers are not installed (`playwright install`); those failures are environmental, not Streamlit regressions.

## What I Found

- **Runbook / regression:** With Postgres running and `PYTHON_DATABASE_URL` set, dashboard-focused tests stay green; full suite depends on optional browser/LLM setup.
- A dedicated dashboard engine (`get_dashboard_engine`) with PostgreSQL `default_transaction_read_only=on` satisfies the “separate read-only engine” requirement without requiring a second DB user for local dev.
- TTL `300` on `@st.cache_data` plus `st.session_state` last-good snapshots covers “never blank” after at least one successful load in the session; first visit during an outage still shows structured empty state + error text.
- Ingestion run **status** in `job_ingestion_runs` uses values such as `completed` / `failed` from the Ingestion agent; the **Recent runs** table surfaces `status` as stored (the older Pipeline Run Summary page still treats `success` as a special case for messaging).

## Recommendation

- Use `PYTHON_DATABASE_URL_READONLY` in production with a read-only DB role; keep `PYTHON_DATABASE_URL` for agents. For local dev, a single URL is acceptable with the session read-only flag.
- Keep `pytest agents/tests/ -v` green on CI; merge only after the full suite passes in your pipeline configuration (or explicitly skip/mock Crawl4AI where appropriate).

## Tradeoffs Acknowledged

- **Cached fetch functions raise on DB errors** so Streamlit does not cache a failed return for the full TTL (“cache poisoning”). Resolvers catch exceptions and use `st.session_state` last-good snapshots instead.
- **Last-good data** is per browser session only (no disk cache).
- **Normalization metrics** use SQL aggregates for scale; detailed row-level drill-down is not on these two pages (by design — observability, not analytics).
- **Staleness banner** after five minutes may appear even when Streamlit has refreshed the cache on rerun; it reflects `fetched_at` embedded in the served payload.
- **Dashboard DB check logging:** first connection failure per process logs at warning; repeat failures while Postgres is down log at debug to avoid Streamlit rerun spam.
- **Streamlit reruns** when the tab reconnects; widget selections (e.g. which ingestion run) are **not** persisted in `session_state` on all pages — the UI can “reset” while **Postgres data is unchanged**. Recover runs via **Pipeline Run Summary** (newest run usually first), **`agents/data/output/pipeline_run.json`**, or SQL on `job_ingestion_runs`.

## Data / Evidence

- Code: `agents/dashboard/app.py` (repo-root `sys.path` bootstrap), `readonly_engine.py`, `observability_queries.py`, `observability_metrics.py`, `pages_observability.py`, updates to `streamlit_app.py` (e.g. `width="stretch"` for Streamlit API deprecation).
- Tests: `agents/tests/test_dashboard_observability.py` (9 tests), `agents/tests/test_streamlit_app.py`; full `agents/tests/` as run in your environment.
- Dependency: `plotly>=5.18` in `agents/requirements.txt`.

## Final verification performed (2026-04-01)

- **Automated:** `pytest agents/tests/test_dashboard_observability.py agents/tests/test_streamlit_app.py` → **30 passed**; full `pytest agents/tests/` → **193 passed** (5 unrelated SQLAlchemy deprecation warnings). `ruff check agents/dashboard/` → clean. Listed dashboard modules present on disk; `python -c "from agents.dashboard.app import main"` succeeds (Streamlit “no runtime” cache warnings on import are expected outside `streamlit run`).
- **Manual UI:** `streamlit run agents/dashboard/app.py` — **Ingestion Overview** and **Normalization Quality** render without errors; empty ingestion tables show the intended info callouts; normalization/quarantine metrics reflect whatever rows exist in `normalized_jobs` / `normalization_quarantine` (pages can differ if staging vs downstream tables are out of sync in dev — not a wiring bug).
- **Sidebar “Connected to PostgreSQL (read-only)”:** Expected with **only** `PYTHON_DATABASE_URL` set. The dashboard uses a **separate engine** from the pipeline writer, with PostgreSQL `default_transaction_read_only=on` on that connection. `PYTHON_DATABASE_URL_READONLY` is **optional** (e.g. dedicated RO user in production); local dev does not require it for this message to appear.

**Conclusion:** Week 6 Streamlit observability wiring is verified end-to-end.

---

## Updates after the initial findings commit

### Pipeline Run Summary — ingestion “Pass” bug fix

- **Issue:** **Record Completion** marked **Ingestion** as **Fail** for almost all rows because the UI required `processing_status == "success"`. Ingestion stores **`pending`**, then normalization sets **`normalized`** or **`quarantined`** — **`success` is never written** on `raw_ingested_jobs`.
- **Fix:** `_raw_row_ingestion_succeeded()` in `streamlit_app.py` treats `pending`, `normalized`, `quarantined` (and `success` if it ever appears) as successful staging.
- **Tests:** `TestRawRowIngestionSucceeded` in `agents/tests/test_streamlit_app.py`.

### Batch Insights — full-table SQL aggregates

- **Issue:** Charts previously used pandas `value_counts()` on at most **500** rows loaded into memory — wrong at scale and **misleading** once more than 500 rows existed.
- **Add:** `agents/dashboard/batch_insights_queries.py` — `fetch_batch_insights_bundle()` (cached `ttl=300`): `GROUP BY` distributions, remote CASE, top state/city, salary medians via `percentile_cont`, histogram via `WIDTH_BUCKET` + **`bin_start`**, global raw **`processing_status`** breakdown, **50-row** recent sample; helpers `series_from_category_count`, `series_from_salary_histogram` (x-axis **USD range labels**, not bucket integers 1–10).
- **Wire:** `_page_batch_insights_db()` consumes the bundle instead of aggregating large frames in Python.

### Record Journey — paging and correct Stage 2 lookups

- **Unscoped** `_load_raw_jobs` / `_load_normalized_jobs` support **`limit`** / **`offset`** (clamped via `_clamp_list_window`, max 5000) for a **newest-first** window.
- **UI:** expander **List window** — max rows + skip (offset); caption shows which slice is loaded.
- **Fix:** Normalization and quarantine for the selected raw id use **per-row SQL** — `_load_normalized_for_raw_job`, `_load_quarantine_for_raw_job` — so a paged raw list still resolves Stage 2 even when that id is not in the last 500 normalized rows.
- **Tests:** `agents/tests/test_batch_insights_queries.py`, `agents/tests/test_dashboard_list_window.py`.

### Team demo / integration notes (behavior, not new code)

- **Normalization Quality — conformance vs quarantine:** Conformance is **only** over **`normalized_jobs`** with `normalization_status = 'success'`. Quarantined rows live in **`normalization_quarantine`** and are **not** in `normalized_jobs`, so **100% conformance** can coexist with a **non-zero quarantine count**.
- **Ingestion Overview:** Dedup rate is **aggregated across runs** in the loaded `job_ingestion_runs` set; per-run dedup is on **Pipeline Run Summary**.
- **Normalization agent batch scope:** Each pipeline pass passes **`batch_id`** (= ingestion `run_id`); pending rows from **other** runs are not normalized in that pass unless you run a backlog path.
- **`raw_ingested_jobs.id`:** Table-wide surrogate key; **not** “row 1 of this run.” Gaps and starting above 1 are normal after prior inserts or deletes (sequence does not reset).
- **`web_scrape` in `source`:** Legacy rows or old paths; current Crawl4AI fixture mapping uses **`crawl4ai`**. Stale labels persist until data is removed or re-ingested.
- **`pipeline_runner` duration:** Default **`sources`: `jsearch` + `crawl4ai`** plus long **`SCRAPING_TARGETS`** and downstream **LLM** agents (skills, enrichment) make full runs **minutes**, not seconds.

### Local Docker / Compose

- **`docker-compose.yml`:** Dropped obsolete top-level **`version`**. **`POSTGRES_PASSWORD`** and **`MSSQL_SA_PASSWORD`** use **compose defaults** when unset so Postgres can start without an empty password; **root `.env` still overrides** (e.g. align **`POSTGRES_PASSWORD`** with **`PYTHON_DATABASE_URL`**).
- **Fresh DB workflow (documented in RUNBOOK / team):** `docker compose down -v` → `up -d postgres` → **`scripts/pg-seed-data/seed_pg_database.py`** (drops/rebuilds `dbo` + fixtures) → **`agents/scripts/db_check.py migrate`** (agent tables) — **order: seed then migrate** because seed **`DROP SCHEMA dbo CASCADE`** would remove migration-only tables if migrate ran first.

### Commands (quick reference)

```bash
# Dashboard
streamlit run agents/dashboard/app.py

# Full agent tests (from repo root)
agents/.venv/bin/python -m pytest agents/tests/ -v

# DB migrate
agents/.venv/bin/python agents/scripts/db_check.py migrate
```

---

**Conclusion (updated):** Week 6 observability pages plus journey/dashboard improvements above are in place; treat full `pytest` green as environment-dependent where Crawl4AI/Playwright is required.
