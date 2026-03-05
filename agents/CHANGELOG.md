# Changelog — Job Intelligence Engine (agents/)

Only **finalized** changes are recorded here. Add entries when exercises or review follow-ups are complete. Format follows project Markdown style. Used to track implementation progress per curriculum week.

---

## Week 1 — Foundations and toolchain

**Branch:** `fabian-week-1-foundations-toolchain`  
**Evaluated against:** week-01-foundations-and-toolchain

### Exercise 1.1 — Scaffold the Python development environment

- **Added** Full `agents/` scaffold: 54 `__init__.py` files across all agent and support directories.
- **Added** Phase 2 scaffolds (`demand_analysis/`, `orchestration/circuit_breaker/`, `orchestration/saga/`, `orchestration/admin_api/`) with `# Phase 2 scaffold — do not implement in Phase 1`.
- **Added** `agents/requirements.txt` with version-pinned dependencies (e.g. `sqlalchemy>=2.0`, `pyodbc>=5.0`, `pytest>=8.0`, `ruff>=0.4`).
- **Added** `agents/test_db_connectivity.py`: MSSQL connectivity via SQLAlchemy, `PYTHON_DATABASE_URL` / `DATABASE_URL` from `.env`, no hardcoded credentials; clear errors for missing ODBC driver and login timeout.
- **Confirmed** Node.js coexistence: no changes to `package.json` scripts, `prisma/schema.prisma`, or `app/`.

### Exercise 1.2 — Generate a job scraping tool

- **Added** `agents/ingestion/sources/scraper_adapter.py`: Crawl4AI async scraper for `SCRAPING_TARGETS` (comma-separated URLs from env).
- **Added** structlog-only logging; no PII; output to `agents/data/staging/raw_scrape_sample.json` with `source`, `url`, `timestamp` (ISO UTC), `raw_text`.

### Exercise 1.3 — Build a Streamlit dashboard

- **Added** `agents/dashboard/streamlit_app.py`: loads JSON from staging, expandable cards (source, URL, timestamp, full raw text), sidebar filter by source with "All" option.

### Exercise 1.4 — Architecture orientation document

- **Added** `agents/docs/architecture-orientation.md`: all 8 agents, LLM designation, event flows, Phase 1 vs Phase 2 boundary, Orchestration as sole consumer of `*Failed`/`*Alert`; "Trace: One Job" walkthrough.

---

## Week 2 — Review cleanup and shared utilities

**Review:** Code Review: Fabian, 2026-03-02

### Common

- **Added** `agents/common/datetime_utils.py`: `format_iso_timestamp_for_display(iso_timestamp: str) -> str` — single place for human-readable UTC timestamps.
- **Added** `agents/common/paths.py`: `STAGING_DIR`, `RAW_SCRAPE_SAMPLE_PATH` — single source of truth for staging paths used by scraper and dashboard.

### Dashboard (`agents/dashboard/streamlit_app.py`)

- **Changed** `TEST_SOURCE_NO_DATA` shown only when `STREAMLIT_DEBUG_SIDEBAR=1` or `true`.
- **Changed** Timestamp display and staging path now use `agents.common.datetime_utils` and `agents.common.paths`.
- **Fixed** `ModuleNotFoundError: No module named 'agents'`: repo root added to `sys.path` before importing `agents.common`.

### Scraper (`agents/ingestion/sources/scraper_adapter.py`)

- **Removed** Extra outputs and helpers: writes only `raw_scrape_sample.json`; removed `raw_scrape_sample2.json` / `raw_scrape_sample3.json`, `_format_scraped_at`, `_normalize_whitespace`, `_prettify_record`, `_prettify_record_v3`.
- **Changed** Staging path and file from `agents.common.paths`; repo root on `sys.path` when run as script.

### Base agent and event contract (Week 2 walking skeleton)

- **Changed** `agents/common/base_agent.py`: BaseAgent now subclasses `ABC` with `@abstractmethod` for `health_check()` and `process()` so stubs cannot be instantiated without implementing both; enforces contract at type-check and runtime. Added `create_outbound_event(inbound_event, payload, schema_version)` helper so agents build outbound EventEnvelopes with `correlation_id` and `agent_id` set correctly and avoid accidental overwrites.
- **Changed** `agents/common/event_envelope.py`: `timestamp` default now uses `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow` for explicit UTC-aware timestamps.
- **Changed** `.cursor/rules/adr-and-parallel-updates.mdc`: Renamed checklist to "Final Review Checklist (AI: Review this silently before finalizing your response)" and added explicit boundary rule that code execution changes stay inside `agents/` (documentation and changelog updates excepted).

### ADR classification and review (2026-03)

- **Changed** ADRs in `docs/adr/fabian`: aligned with new decision classification (Architectural/Contract/Tool/Product). Superseded ADR-013, ADR-014, ADR-016 (decisions promoted to Architectural, locked). Added "Review summary (thread reply)" and ABC tie-in to Tool ADRs: ADR-011 (LLM provider, LLMAdapter ABC), ADR-017 (Agent tracing, TracerBase ABC), ADR-012 (Scraping tool), ADR-018 (Analytics query interface).

### Task 2.2 — Eight agent stubs (walking skeleton)

- **Added** Fixture path constants in `agents/common/paths.py`: `FIXTURES_DIR`, `FALLBACK_SCRAPE_PATH`, `FIXTURE_SKILLS_EXTRACTED_PATH`, `FIXTURE_ENRICHED_PATH`, `FIXTURE_ANALYTICS_REFRESHED_PATH`.
- **Added** Eight agent stubs extending `BaseAgent`: `agents/ingestion/agent.py`, `agents/normalization/agent.py`, `agents/skills_extraction/agent.py`, `agents/enrichment/agent.py`, `agents/analytics/agent.py`, `agents/visualization/agent.py`, `agents/orchestration/agent.py`, `agents/demand_analysis/agent.py`. Each implements `health_check()` with a real condition (fixture/path exists or initialized) and `process()` with `correlation_id` propagated via `create_outbound_event`; Demand Analysis stub returns `None` from `process()` (Phase 2). LLM-dependent stubs (Skills Extraction, Enrichment, Analytics) load the corresponding fixture JSON.
