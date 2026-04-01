# Week 6 — Fabian: Streamlit observability foundations (findings)

## What I Tested

- `streamlit run agents/dashboard/app.py` with PostgreSQL populated from prior ingestion/normalization runs (when available).
- Empty database: no rows in `raw_ingested_jobs`, `job_ingestion_runs`, `normalized_jobs` — confirmed pages show metrics as N/A or zero, info callouts, and no uncaught exceptions.
- JSON-only mode (no `PYTHON_DATABASE_URL`): **Ingestion Overview** and **Normalization Quality** show a clear warning; journey pages still use `pipeline_run.json`.
- Unit tests: `agents/tests/test_dashboard_observability.py` (metric helpers), `agents/tests/test_streamlit_app.py` (including `_db_available` / read-only URL cases).
- **Regression:** Full suite `cd agents && pytest tests/ -v` — **193 passed** (confirmed **2026-04-01** with PostgreSQL available; earlier **2026-03-30** run also green). CI should match when `PYTHON_DATABASE_URL` is set and Postgres is reachable; without DB, `test_database` / `test_models` are typically skipped or fail depending on fixtures.

## What I Found

- **Runbook / regression:** With Postgres running and `PYTHON_DATABASE_URL` set, the full `agents/tests/` suite completes with **193 passed** (no failures); Week 6 dashboard tests are included in that run.
- A dedicated dashboard engine (`get_dashboard_engine`) with PostgreSQL `default_transaction_read_only=on` satisfies the “separate read-only engine” requirement without requiring a second DB user for local dev.
- TTL `300` on `@st.cache_data` plus `st.session_state` last-good snapshots covers “never blank” after at least one successful load in the session; first visit during an outage still shows structured empty state + error text.
- Ingestion run **status** in `job_ingestion_runs` uses values such as `completed` / `failed` from the Ingestion agent; the **Recent runs** table surfaces `status` as stored (the older Pipeline Run Summary page still treats `success` as a special case for messaging).

## Recommendation

- Use `PYTHON_DATABASE_URL_READONLY` in production with a read-only DB role; keep `PYTHON_DATABASE_URL` for agents. For local dev, a single URL is acceptable with the session read-only flag.
- Keep `pytest tests/ -v` (from `agents/`) green on CI; merge only after the full suite passes in your pipeline configuration.

## Tradeoffs Acknowledged

- **Cached fetch functions raise on DB errors** so Streamlit does not cache a failed return for the full TTL (“cache poisoning”). Resolvers catch exceptions and use `st.session_state` last-good snapshots instead.
- **Last-good data** is per browser session only (no disk cache).
- **Normalization metrics** use SQL aggregates for scale; detailed row-level drill-down is not on these two pages (by design — observability, not analytics).
- **Staleness banner** after five minutes may appear even when Streamlit has refreshed the cache on rerun; it reflects `fetched_at` embedded in the served payload.
- **Dashboard DB check logging:** first connection failure per process logs at warning; repeat failures while Postgres is down log at debug to avoid Streamlit rerun spam.

## Data / Evidence

- Code: `agents/dashboard/app.py` (repo-root `sys.path` bootstrap), `readonly_engine.py`, `observability_queries.py`, `observability_metrics.py`, `pages_observability.py`, updates to `streamlit_app.py` (e.g. `width="stretch"` for Streamlit API deprecation).
- Tests: `agents/tests/test_dashboard_observability.py` (9 tests), `agents/tests/test_streamlit_app.py`; **full `agents/tests/` suite: 193 passed** (recorded run).
- Dependency: `plotly>=5.18` in `agents/requirements.txt`.

## Final verification performed (2026-04-01)

- **Automated:** `pytest agents/tests/test_dashboard_observability.py agents/tests/test_streamlit_app.py` → **30 passed**; full `pytest agents/tests/` → **193 passed** (5 unrelated SQLAlchemy deprecation warnings). `ruff check agents/dashboard/` → clean. Listed dashboard modules present on disk; `python -c "from agents.dashboard.app import main"` succeeds (Streamlit “no runtime” cache warnings on import are expected outside `streamlit run`).
- **Manual UI:** `streamlit run agents/dashboard/app.py` — **Ingestion Overview** and **Normalization Quality** render without errors; empty ingestion tables show the intended info callouts; normalization/quarantine metrics reflect whatever rows exist in `normalized_jobs` / `normalization_quarantine` (pages can differ if staging vs downstream tables are out of sync in dev — not a wiring bug).
- **Sidebar “Connected to PostgreSQL (read-only)”:** Expected with **only** `PYTHON_DATABASE_URL` set. The dashboard uses a **separate engine** from the pipeline writer, with PostgreSQL `default_transaction_read_only=on` on that connection. `PYTHON_DATABASE_URL_READONLY` is **optional** (e.g. dedicated RO user in production); local dev does not require it for this message to appear.

**Conclusion:** Week 6 Streamlit observability wiring is verified end-to-end.
