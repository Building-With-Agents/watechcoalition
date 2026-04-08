# JSearch pipeline — changelog and findings (Emilio track)

Engineering notes: how raw staging, `pending` vs `awaiting_description`, and optional **description backfill** fit together. Use this as a quick onboarding doc; authoritative specs live in runbooks and [`jsearch_description_detail.md`](../architecture/jsearch_description_detail.md).

---

## TL;DR

| Topic | Takeaway |
|--------|-----------|
| **Low job count from a run** | Usually **discovery** (query, location, pagination stopping early) — not the same as “half the descriptions are empty.” |
| **Thin or empty descriptions** | **Completeness** — JSearch `/search` often returns listings with empty or short `job_description`; we stage those separately from the normalize queue. |
| **Normalize queue** | Only `processing_status = 'pending'` rows are picked up by Normalization. |
| **Second-hop text** | Optional script calls RapidAPI **job detail** (configurable URL), then promotes to `pending` only if text passes a **length gate** (`DESCRIPTION_MIN_CHARS`). |

---

## Changelog (what changed, in order)

### 1. Everything used to be `pending`

- Raw rows were staged as `pending` even when `description` was empty.
- Downstream (normalization → skills) then saw empty text, which masked upstream API issues and wasted work.

### 2. Staging split: `pending` vs `awaiting_description`

- **Rule:** After ingest, if mapped description is **empty or whitespace-only** → `awaiting_description`. If there is any non-whitespace text → `pending`.
- **Implementation:** `raw_processing_status_for_record()` in [`agents/ingestion/agent.py`](../../ingestion/agent.py).
- **Downstream:** [`fetch_pending_records`](../../normalization/agent.py) only loads `processing_status == 'pending'`, so metadata-only rows **wait** until description is filled or policy changes.

### 3. Legacy escape hatch

- **`ALLOW_EMPTY_DESCRIPTION_PENDING=1`** — forces **all** new ingests to `pending` even with empty description (old behavior). Use only if you explicitly accept empty-text rows in normalization.

### 4. Provenance on the row (`description_source`)

- JSearch rows get `description_source = 'jsearch_search'` at insert when staged ([`stage_records`](../../ingestion/agent.py)).
- After a successful detail backfill that passes the gate, `description_source = 'jsearch_detail'` and `processing_status = 'pending'`.

### 5. DB columns for detail attempts (Phase 1a)

- Added on `dbo.raw_ingested_jobs`: `description_fetched_at`, `detail_fetch_attempts`, `detail_last_error`, `detail_fetch_status` (e.g. terminal stop), plus `description_source` above.
- Applied via `run_migrations()` — see [Commands — database](#commands--database).

### 6. Substantive description gate (detail promotion only)

- **Initial staging** still uses only “non-empty after strip” for `pending` vs `awaiting_description` (unchanged).
- **Detail worker** uses `is_substantive_description()` — min length from **`DESCRIPTION_MIN_CHARS`** (default **200**) — before flipping to `pending`. Short API text stays `awaiting_description` until retries exhaust or status goes terminal.

### 7. Optional RapidAPI detail fetch (worker script)

- Separate from `/search` ingestion: [`run_jsearch_description_backfill.py`](../../scripts/run_jsearch_description_backfill.py).
- **Kill switch:** no live HTTP unless **`JSEARCH_DETAIL_FETCH_ENABLED=1`**.
- **Concurrency:** PostgreSQL `FOR UPDATE SKIP LOCKED`; dedupes duplicate `external_id` within one batch to avoid double API calls.

### 8. Observability

- **`jsearch_search_complete`** log after each `/search` fetch: `jsearch_search_requests_total`, `jsearch_search_pages_fetched`, `search_unique_records_staged` ([`jsearch_adapter.py`](../../ingestion/sources/jsearch_adapter.py)).
- **Detail / worker:** `jsearch_detail_*`, `jsearch_429_total`, `detail_dedup_skips_total`, `description_fill_rate`, etc. (structlog JSON).

### 9. Skills extraction

- Empty normalized text still short-circuits with log event **`skills_extraction_no_text`** (info). Fewer rows hit this after successful description backfill.

---

## Findings (things we learned)

1. **Do not conflate metrics.** “Only 18 jobs in this batch” is often pagination or a narrow query. “46% empty description” is a **cohort quality** metric on the jobs `/search` actually returned.
2. **JSearch `/search` is not guaranteed to include full job bodies.** A second endpoint (details in RapidAPI playground) may return richer text — URL and query param names are **configurable** via env vars so you can match current API docs without a code change.
3. **Billing** for search vs detail is **operator-verified** (dashboard / plan); treat each detail GET as potentially one billable call until proven otherwise.
4. **`ALLOW_EMPTY_DESCRIPTION_PENDING`** does not add rows to the detail worker queue (those rows are already `pending`). Prefer the detail worker + gate for “needs richer text” when using default staging.

---

## Commands — ingestion and samples

Run from **repo root** unless noted. Ensure **`PYTHON_DATABASE_URL`** and **`JSEARCH_API_KEY`** are set for live JSearch.

| Command | What it does |
|--------|----------------|
| `python -m agents.ingestion.agent --source jsearch --limit 50` | Runs ingestion for JSearch only, caps fetched records at 50. |
| `python -m agents.ingestion.agent --migrate --source jsearch --limit 50` | Runs **DB migrations** first, then same as above. |
| `python agents/scripts/batch_ingest.py` | Bulk ingest from configured regions (Loop 1 / flywheel). |
| `python agents/scripts/batch_ingest.py --dry-run` | Prints plan only; no API calls. |
| `python agents/scripts/ingest_description_sample.py --limit 50` | Small JSearch ingest + **prints description coverage** and counts of `pending` vs `awaiting_description` for that run. Syncs PostgreSQL sequences first (use `--no-sync-sequences` to skip). |
| `python agents/scripts/ingest_description_sample.py --limit 50 --query "data engineer" --location "Texas"` | Same, with custom query and region location. |
| `python agents/scripts/run_processing_loop.py` | Loop 2: normalize → extract → enrich for **pending** raw rows (paced batches). |
| `python agents/scripts/run_processing_loop.py --dry-run` | Shows pending counts without processing. |

### JSearch pagination env (affects `/search` volume)

| Variable | Role |
|----------|------|
| `BATCH_SIZE` | Desired volume; with `jsearch_num_pages_from_env()`, drives how many pages to request (≈ 10 jobs per page). |
| `JSEARCH_MAX_PAGES` | Hard cap on pages per adapter call (default 10, max 50). |

---

## Commands — description backfill (detail API)

| Command | What it does |
|--------|----------------|
| `python agents/scripts/run_jsearch_description_backfill.py --dry-run` | **No HTTP.** Counts eligible rows and estimates unique detail fetches for a read-only sample (no row locks). |
| `python agents/scripts/run_jsearch_description_backfill.py --batch-size 25` | Claims up to 25 eligible rows (PostgreSQL: `SKIP LOCKED`), calls detail API when enabled, updates DB. Requires **`JSEARCH_DETAIL_FETCH_ENABLED=1`** and **`JSEARCH_API_KEY`**. |

### Detail backfill env

| Variable | Role |
|----------|------|
| `JSEARCH_DETAIL_FETCH_ENABLED` | Must be `1` / `true` / `yes` for live detail HTTP. |
| `JSEARCH_JOB_DETAIL_URL` | Default `https://jsearch.p.rapidapi.com/job-details` — override if RapidAPI path differs. |
| `JSEARCH_DETAIL_JOB_ID_PARAM` | Query param name for job id (default `job_id`). |
| `DESCRIPTION_MIN_CHARS` | Min trimmed length to promote to `pending` after detail (default `200`). |
| `JSEARCH_DETAIL_MAX_ATTEMPTS` | Stop retrying a row after this many attempts (default `3`). |
| `JSEARCH_DETAIL_MAX_ROWS_PER_RUN` | Optional cap on rows processed per invocation. |
| `JSEARCH_DETAIL_TIMEOUT_SECONDS` | HTTP timeout for detail client. |
| `JSEARCH_DETAIL_MAX_429_RETRIES` / `JSEARCH_DETAIL_BACKOFF_BASE_SECONDS` | 429 backoff tuning. |

---

## Commands — database

| Command | What it does |
|--------|----------------|
| `python agents/scripts/db_check.py migrate` | Runs **`run_migrations(get_engine())`** — creates/updates agent tables and columns (including description-detail fields on `raw_ingested_jobs`). Idempotent. |
| `python agents/scripts/db_check.py counts` | Row counts for main pipeline tables. |
| `python agents/scripts/sync_agent_sequences.py` | Resyncs PostgreSQL SERIAL/IDENTITY sequences after restores / bulk inserts. Also invoked at end of `run_migrations` for agent tables. |

One-liner equivalent (from [`RUNBOOK.md`](../RUNBOOK.md)):

```bash
python -c "
from dotenv import load_dotenv; load_dotenv()
from agents.common.data_store.database import get_engine
from agents.common.data_store.migrations import run_migrations
run_migrations(get_engine())
print('Migrations complete')
"
```

---

## Related docs

- [WEEK06 testing runbook](../runbooks/WEEK06_TESTING_RUNBOOK.md) — staging status, `ingest_description_sample`, SQL snippets, skills note.
- [jsearch_description_detail.md](../architecture/jsearch_description_detail.md) — API spike notes, cost model, Phase 1b pointer.
- Issue **#165** (empty JSearch descriptions) — product context and historical discussion.

---

## Streamlit / dashboard

- `awaiting_description` is treated as a **normal** raw ingestion outcome alongside `pending` (see [`streamlit_app.py`](../../dashboard/streamlit_app.py) allowed status set). Operators should expect both when monitoring raw staging.
