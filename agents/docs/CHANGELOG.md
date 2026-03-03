# Changelog — agents/

All notable changes to the `agents/` directory and agent-related documentation are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Exercise 1.1 — Environment and scaffold

#### Summary

- Implemented the full agents directory scaffold, connectivity test (SQLAlchemy + pyodbc), and Python/Node coexistence docs.
- Documented Python DATABASE_URL format (`mssql+pyodbc://`), venv location (`agents/.venv`), and Windows-specific setup.
- Resolved environment, dependency, and database connection issues (see **Problems and fixes** below).

#### Added

- **agents/ directory scaffold (Job Intelligence Engine)**
  - Full directory tree under `agents/` per canonical structure in CLAUDE.md and docs/planning/ARCHITECTURE_DEEP.md.
  - Empty `__init__.py` in every Python package (ingestion, normalization, skills_extraction, enrichment, analytics, visualization, orchestration, demand_analysis, common, dashboard, platform, and all subpackages including tests). No `__init__.py` under `data/`, `eval/`, or `docs/`.
  - Stub modules: `ingestion/agent.py`, `ingestion/sources/jsearch_adapter.py`, `ingestion/sources/scraper_adapter.py`, `ingestion/deduplicator.py`; all other agent `agent.py` stubs; `common/llm_adapter.py`; `dashboard/streamlit_app.py`. Each agent stub exposes a `health_check()`-style contract.
  - Phase 2 empty scaffolds (only `__init__.py` and `demand_analysis/agent.py` stub): `orchestration/circuit_breaker/`, `orchestration/saga/`, `orchestration/admin_api/`, `enrichment/resolvers/`, `demand_analysis/time_series/`, `demand_analysis/forecasting/`, `platform/*`, `data/demand_signals/`.
  - `.gitkeep` in leaf dirs under `data/`, `eval/`, and `docs/` so the structure is tracked by git.

- **agents/requirements.txt**
  - Package list: sqlalchemy, pyodbc, streamlit, httpx, python-dotenv, langchain, langchain-openai, langchain-community, langgraph, langsmith, crawl4ai, apscheduler, pydantic, structlog.

- **agents/.env.example**
  - Template for pipeline env vars: Azure OpenAI, DATABASE_URL, LangSmith, ingestion (JSEARCH_API_KEY, SCRAPING_TARGETS, INGESTION_SCHEDULE), and thresholds. Empty/placeholder values for secrets.
  - Comment and example for **Python DATABASE_URL**: must use `mssql+pyodbc://` (not `sqlserver://`); example with `127.0.0.1`, ODBC Driver 18, and TrustServerCertificate=yes. Use the same host/port as your app (e.g. Docker port 11433).

- **agents/connectivity_test.py**
  - Connectivity test: SQLAlchemy + pyodbc, no Prisma, no hardcoded credentials. Loads `agents/.env` via python-dotenv, reads `DATABASE_URL`, converts `sqlserver://` to `mssql+pyodbc://` (Driver 18) when needed, runs `SELECT COUNT(*) FROM job_postings`, prints count and exits 0/non-zero. Run from repo root: `python -m agents.connectivity_test`. Success: `job_postings row count: <N>`.

- **agents/README.md**
  - Python environment: venv inside `agents/`, activate from project root. DATABASE_URL must be `mssql+pyodbc://` in `agents/.env`; example with Driver 18. Commands: connectivity test, Streamlit, pytest. Coexistence note: agents use `agents/.env` + SQLAlchemy; Next.js uses root `.env` + Prisma.

- **agents/docs/architecture/AGENTS_SCAFFOLD.md**
  - Documentation of the scaffold: directory tree, `__init__.py` placement, stub modules, Phase 1 vs Phase 2, conformance. Python venv in `agents/`, DATABASE_URL format, connectivity test, coexistence with Node.js.

- **agents/docs/CHANGELOG.md** (this file)
  - Changelog for all agent-layer changes and setup lessons learned.

#### Changed

- **agents/requirements.txt**
  - Replaced previous version-pinned list (and optional pytest, ruff) with the unified package list. Pytest and ruff can be re-added for development if needed.

- **agents/.env.example**
  - Sanitized: removed real credentials; Azure keys and DATABASE_URL empty or commented example only. Documented `mssql+pyodbc://` and ODBC Driver 18.

- **agents/connectivity_test.py**
  - Use ODBC Driver 18 when converting `sqlserver://` to `mssql+pyodbc://`. Fallback: load `agents/.env` from `Path.cwd() / "agents" / ".env"` when run as `python -m agents.connectivity_test` from repo root.

- **ONBOARDING.md** (repo root)
  - Section 5: Root `DATABASE_URL` is for Prisma/Next.js only. Added **5.1 Python / agents**: use `agents/.env` with `mssql+pyodbc://`, example with Driver 18 and `127.0.0.1`, verify with `python -m agents.connectivity_test`.
  - Section 7: Venv inside `agents/`, activate from project root; create with `python -m venv .venv` (use `python` or `py -3.12` on Windows). Windows: `.\agents\.venv\Scripts\Activate.ps1`. Added connectivity test as first command; link to agents/README.md.
  - Troubleshooting: Python DATABASE_URL (use `mssql+pyodbc://`; try `127.0.0.1`; use Docker host port e.g. 11433). Wrong Python interpreter (deactivate, remove `agents/.venv`, recreate with 3.11/3.12, activate again). ODBC driver missing (install ODBC Driver 18 for SQL Server). Connection refused (start Docker SQL Server; use correct host/port in `agents/.env`).

- **docs/setup-MSSQL.md**
  - Root `.env`: DATABASE_URL labeled Prisma/Next.js. Added Python (agents): use `agents/.env` with `mssql+pyodbc://`; link to agents/README and ONBOARDING §5.1; commented example with Driver 18 and `127.0.0.1`.

#### Removed

- None.

#### Problems encountered and fixes

| Problem | Cause | Fix |
|--------|--------|-----|
| **`source` not recognized (PowerShell)** | `source` is Bash; PowerShell uses a different command. | Use `.\agents\.venv\Scripts\Activate.ps1` (from project root) or `.\.venv\Scripts\Activate.ps1` from inside `agents/`. |
| **`python3` not found (Windows)** | On Windows the command is usually `python` or `py`, not `python3`. | Use `python -m venv .venv` or `py -3.12 -m venv .venv`. |
| **lxml build failed (Python 3.14)** | No pre-built lxml wheel for Python 3.14 on Windows; build requires libxml2/C++ and fails. | Use **Python 3.11 or 3.12** for the agents venv: `py -3.12 -m venv agents/.venv`. Then `pip install -r agents/requirements.txt` uses pre-built wheels. |
| **ODBC IM002: Data source name not found** | Microsoft ODBC Driver for SQL Server not installed. | Install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server). Ensure `agents/.env` uses `driver=ODBC+Driver+18+for+SQL+Server` (or 17 if that's what you install). |
| **Connection refused (10061) to localhost:1433** | SQL Server not running or Docker exposes a different port. | Start SQL Server (e.g. `docker compose up -d sqlserver`). In `agents/.env`, set `DATABASE_URL` to the **host port** Docker uses (e.g. `127.0.0.1:11433` or `localhost:11433`), not the container's internal port. |
| **DATABASE_URL not set when running connectivity test** | Script could not find `agents/.env` when run as a module from repo root. | Copy `agents/.env.example` to `agents/.env` and fill in values. Connectivity script also has a fallback to load `Path.cwd() / "agents" / ".env"`. |
| **SAWarning: Unrecognized server version** | SQLAlchemy doesn't recognize some SQL Server version strings. | Harmless for simple queries (e.g. `COUNT(*)`). Can be ignored; connectivity test still succeeds (`job_postings row count: 25`). |

#### Verification

- **Connectivity test (Python):** From project root with `agents/.venv` activated: `python -m agents.connectivity_test`. Expected: `job_postings row count: <N>` (e.g. 25). Exit code 0.
- **Next.js:** From project root (venv not required): `npm run dev`. App should run at http://localhost:3000. Confirms Python scaffold did not affect the Node.js app.
- **Exit venv:** Run `deactivate` in the same terminal to leave the agents venv.

---

### Exercise 1.2 — Crawl4AI scraper adapter

#### Summary

- Implemented Crawl4AI-based scraper that fetches a job-board URL, chunks page content into 5–10 job-like sections, and writes raw JSON to staging. URL from env; structlog only; no PII or hardcoded credentials. Pre-scrape URL reachability check (failsafe); output includes source, URL, timestamp, and raw text for downstream agents.

#### Added

- **agents/ingestion/sources/scraper_adapter.py**
  - **Scraping:** Uses Crawl4AI only: top-level `from crawl4ai import AsyncWebCrawler`; `async with AsyncWebCrawler() as crawler:` and `result = await crawler.arun(url=url)`. Reads markdown from `result.markdown` (raw_markdown / fit_markdown / string).
  - **Logging:** structlog only — `log = structlog.get_logger()`; `log.info("raw_scrape_result", url=target, record_count=n)` on success; `log.warning` for `scrape_skipped`, `url_unreachable`, `scrape_failed`, `scrape_aborted_url_unreachable`. No `print()` or stdlib `logging`.
  - **Configuration:** Target URL from environment only: `os.getenv("SCRAPING_TARGETS", "").strip()`; first URL used when comma-separated. No hardcoded URLs or credentials.
  - **Output path:** Raw output saved to `agents/data/staging/raw_scrape_sample.json` (path derived from `__file__` under `agents/`).
  - **Output JSON structure (metadata for downstream):** Top-level: `source` (e.g. `"crawl4ai"`), `url`, `fetch_started_at` (ISO 8601 UTC, when fetch began), `scraped_at` (ISO 8601 UTC, when fetch completed / write time), `record_count`, `jobs`. Each job: `index`, `source`, `url`, `raw_text`, `scraped_at` (timestamp for that posting). Ensures source identifier, scraped URL, timestamps for fetch and per posting, and raw text body on every record.
  - **Failsafe:** Before running Crawl4AI, `_check_url_reachable(url)` uses httpx (HEAD, or GET if 405) with 10s timeout. If unreachable, logs `scrape_aborted_url_unreachable` and returns without scraping.
  - **Chunking:** `_chunk_markdown_into_jobs()` splits markdown by `##`/`###` and double newlines; produces 5–10 unique chunks (min 5, max 10).
  - **Run:** `python -m agents.ingestion.sources.scraper_adapter` from repo root (or `run_scrape(url)` with optional URL override).

- **Recommended job-board URLs (documented in scraper docstring and agents/.env.example)**
  - USAJobs (federal): `https://www.usajobs.gov/`
  - We Work Remotely: `https://weworkremotely.com/categories/remote-programming-jobs`
  - Remote.co: `https://remote.co/remote-jobs/developer/`
  - Wellfound: `https://wellfound.com/jobs`

#### Changed

- **agents/ingestion/sources/scraper_adapter.py**
  - **Timestamps:** Added `fetch_started_at` (ISO 8601 UTC) at top level when the crawl starts; kept `scraped_at` for when the fetch completes. Each job/posting in `jobs` now includes `scraped_at` (same run-completion time per record).
  - **Job-posting filter:** Only chunks that look like job postings are included in the JSON. A chunk is kept only if it contains at least one employment-type keyword (e.g. full-time, part-time, permanent, internship, contract, temporary, remote, hybrid) or pay/salary keyword (e.g. salary, compensation, pay, wage, hourly, annual, per year, per hour, USD, $). Main page, nav, and other content without these signals are excluded. Up to 10 such chunks are written per run (may be fewer if the page has fewer matching sections).
  - **USAJobs two-phase scraping:** When the target URL is USAJobs (`usajobs.gov`), the scraper uses a two-phase flow: (1) Scrape the search-results page (or `https://www.usajobs.gov/Search/Results?p=1` if the user provided the homepage) to discover job announcement links from `result.links` or markdown fallback; (2) Scrape each job detail URL (`/job/{id}`); one record per job page. Only job announcement pages are scraped; no chunking or keyword filter on detail pages. Other sites still use single-page scrape + chunk + filter. Logs: `usajobs_discovery` (discovery_url, job_links_found), `usajobs_job_scrape_failed` per failed detail page.
  - **USAJobs search keyword:** Discovery URL is built with `?k={keyword}&p=1`. Keyword from env `USAJOBS_SEARCH_KEYWORD` (default `job`). Set to `internship`, `part time`, `software`, etc. so the search returns results; without a keyword USAJobs often returns no results.

- **agents/.env.example**
  - Added commented recommended job-board URLs above `SCRAPING_TARGETS` (USAJobs, We Work Remotely, Remote.co, Wellfound).
  - USAJobs: recommend Search/Results URL with keyword `https://www.usajobs.gov/Search/Results?k=job&p=1`; set `USAJOBS_SEARCH_KEYWORD` to `internship`, `part time`, etc. for other searches.

#### Verification

- **Scraper:** Set `SCRAPING_TARGETS` in env (e.g. `$env:SCRAPING_TARGETS = "https://www.usajobs.gov/Search/Results?p=1"` for USAJobs) or pass URL to `run_scrape(url)`. For USAJobs set `USAJOBS_SEARCH_KEYWORD=job` (or `internship`, `part time`, `software`) so the search returns results. From repo root with agents venv activated: `python -m agents.ingestion.sources.scraper_adapter`. **USAJobs:** Two-phase (discover job links from Search/Results?k=..., then scrape each job announcement page). Expected: `usajobs_discovery` log with `job_links_found`, then `raw_scrape_result` with `record_count` and `agents/data/staging/raw_scrape_sample.json` with `jobs[].url` (job detail URL) and `jobs[].raw_text`. **Other sites:** Single-page scrape + chunk + keyword filter; only sections with employment type or pay are included.
- **Playwright (first run):** If Crawl4AI fails with “Executable doesn’t exist” for Chromium, run `playwright install` (or `python -m playwright install`) with the same venv activated to download browser binaries.

---

### Scraper: USAJobs removed, env-only URL, reachability GET fallback

#### Summary

- USAJobs-specific code was removed from the scraper; the target URL is read from `SCRAPING_TARGETS` only (no hardcoded default). When `SCRAPING_TARGETS` is unset, the scraper logs `scrape_skipped` with reason `no_target_url` and returns 0. The reachability check now tries GET when HEAD returns any non-2xx/3xx status, so sites that block or mishandle HEAD (e.g. 403) can still pass when GET succeeds.

#### Added

- **agents/ingestion/sources/scraper_adapter.py**
  - Reachability GET fallback: `_check_url_reachable()` tries GET when HEAD returns any status outside 200–399 (not only 405), so more sites pass the pre-scrape check.

#### Changed

- **agents/ingestion/sources/scraper_adapter.py**
  - Removed USAJobs constants (`_USAJOBS_BASE`, `_USAJOBS_SEARCH_BASE`, `_USAJOBS_JOB_PATH_RE`), functions `_get_usajobs_search_keyword`, `_is_usajobs`, `_usajobs_discovery_url`, `_extract_job_detail_urls`, and async function `scrape_usajobs`; removed the `run_scrape` branch that called `scrape_usajobs` when the target was USAJobs.
  - `_get_target_url()` returns the first URL from `SCRAPING_TARGETS` when set, and `None` when unset (no default URL).
  - Module docstring updated to describe only We Work Remotely / Remote.co (two-phase) and other sites (single-page); configuration from environment variables only; no USAJobs references.
  - `_check_url_reachable()` tries GET when HEAD response status is not 2xx/3xx.

#### Removed

- **agents/ingestion/sources/scraper_adapter.py**
  - USAJobs-related code: constants, discovery URL builder, job-detail URL extractor, `scrape_usajobs`, and the USAJobs branch in `run_scrape`. Unused `quote_plus` import removed.
  - Hardcoded default URL: when `SCRAPING_TARGETS` is unset, the scraper no longer falls back to We Work Remotely or any other URL; it returns `None` and skips with `no_target_url`.

#### Verification

- Set `SCRAPING_TARGETS` in `agents/.env` to a list URL (e.g. `https://weworkremotely.com/categories/remote-programming-jobs`). From repo root with agents venv activated: `python -m agents.ingestion.sources.scraper_adapter`. Expected: `raw_scrape_result` log with `record_count`, and `agents/data/staging/raw_scrape_sample.json` with top-level `source`, `url`, `scraped_at`, `record_count`, `jobs` and each job having `source`, `url`, `scraped_at`, `raw_text`.
- With `SCRAPING_TARGETS` unset: expected `scrape_skipped` log with `reason=no_target_url` and scraper returns 0.

---

*Scaffold details: [agents/docs/architecture/AGENTS_SCAFFOLD.md](architecture/AGENTS_SCAFFOLD.md). Python env and DATABASE_URL: [agents/README.md](../README.md).*
