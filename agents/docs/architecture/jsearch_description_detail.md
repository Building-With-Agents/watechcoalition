# JSearch description detail — API spike, cost model, stage-2 design

## T1 — API spike (verified vs hypothesis)

**Verified (public RapidAPI product page):** The JSearch product on RapidAPI Hub lists multiple endpoints including **Job Search** and **Job Details** (see [JSearch on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)). **Go:** proceed with Phase 1a using a configurable detail URL so the exact path and query parameter names can be aligned with the live playground without code changes.

**Verified (this repo — list/search only):** Ingestion uses `GET https://jsearch.p.rapidapi.com/search` with query params `query`, `page`, `num_pages` ([`jsearch_adapter.py`](../../ingestion/sources/jsearch_adapter.py)).

**Hypothesis (confirm in RapidAPI playground before production):**

- Detail endpoint path is commonly documented as **`/job-details`** under host `jsearch.p.rapidapi.com`.
- Required identifier is typically **`job_id`** (string), matching `external_id` / `job_id` from `/search` payloads.

**Default implementation:** [`jsearch_detail_client.py`](../../ingestion/sources/jsearch_detail_client.py) uses:

- `JSEARCH_JOB_DETAIL_URL` (default `https://jsearch.p.rapidapi.com/job-details`)
- `JSEARCH_DETAIL_JOB_ID_PARAM` (default `job_id`)

Override these if the playground shows different names.

**Redacted response shape (expected):** Top-level JSON with a `data` array or single job object containing `job_description` and/or `description` (same field names as search mapping). Errors: HTTP 4xx/5xx; RapidAPI may return 429 when rate-limited.

**Pricing / credits:** **Unknown — operator must verify** in RapidAPI dashboard and JSearch plan docs. Treat each detail `GET` as **one billable request** until proven otherwise.

---

## T2 — Cost model (formulas)

Let:

- `P = jsearch_num_pages_from_env()` (from `BATCH_SIZE` and `JSEARCH_MAX_PAGES`, capped at 50).
- **Search requests per adapter run:** `S = P` (one request per page in the current implementation).
- `N` = JSearch rows staged in a run (after dedup).
- `θ` = fraction of those rows with **non-substantive** description after `/search` (staged as `awaiting_description` when `ALLOW_EMPTY_DESCRIPTION_PENDING` is off).
- `D` = number of **detail** HTTP calls the backfill worker issues for a batch (with gating: only rows in `awaiting_description`; with dedup: duplicate `external_id` in the same worker batch counts once).

**Conservative upper bound (no dedup):** `D_max = θ × N`.

**With per-batch dedup by `external_id`:** `D ≤ θ × N`.

**Total RapidAPI HTTP calls (search + detail backfill):** `S + D` (detail calls are additional to search; **verify** whether your plan bills search and detail identically).

**Example:** `BATCH_SIZE=100`, `JSEARCH_MAX_PAGES=10` → `P=10` → `S=10`. If `N=80` and `θ=0.45`, then up to `36` detail calls per full backfill pass over that cohort (fewer if capped by `JSEARCH_DETAIL_MAX_ROWS_PER_RUN`).

---

## T6 — Stage-2 design (script vs agent vs queue)

**Phase 1a (implemented):** DB-polled script [`run_jsearch_description_backfill.py`](../../scripts/run_jsearch_description_backfill.py) uses ingestion-owned HTTP client + `FOR UPDATE SKIP LOCKED` for concurrency. No new `EventEnvelope` types; normalization continues to read `processing_status = 'pending'`.

**Future:** If volume or isolation requirements exceed DB polling, optionally promote to a scheduled orchestration job or a dedicated worker process—**still no Celery by default** per project constraints. External message bus remains Phase 2.

---

## Legal / compliance (high level)

Respect site **robots.txt** and **terms of service**; **logged-out** fetching only; do **not** bypass CAPTCHA or login walls. Origin scraping (Phase 1b) requires explicit allowlists and review—not legal advice.
