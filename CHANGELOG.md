# Changelog

All notable changes, additions, and removals to the codebase are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

- **agents/ directory scaffold (Job Intelligence Engine)**
  - Full directory tree under `agents/` per canonical structure in CLAUDE.md and docs/planning/ARCHITECTURE_DEEP.md.
  - Empty `__init__.py` in every Python package directory (ingestion, normalization, skills_extraction, enrichment, analytics, visualization, orchestration, demand_analysis, common, dashboard, platform, and all subpackages including tests). No `__init__.py` under `data/`, `eval/`, or `docs/`.
  - Stub modules: `ingestion/agent.py`, `ingestion/sources/jsearch_adapter.py`, `ingestion/sources/scraper_adapter.py`, `ingestion/deduplicator.py`; `normalization/agent.py`; `skills_extraction/agent.py`; `enrichment/agent.py`; `analytics/agent.py`; `visualization/agent.py`; `orchestration/agent.py`; `demand_analysis/agent.py`; `common/llm_adapter.py`; `dashboard/streamlit_app.py`. Each agent stub exposes a `health_check()`-style contract.
  - Phase 2 directories left as empty scaffolds (only `__init__.py` and, for demand_analysis, stub `agent.py`): `orchestration/circuit_breaker/`, `orchestration/saga/`, `orchestration/admin_api/`, `enrichment/resolvers/`, `demand_analysis/time_series/`, `demand_analysis/forecasting/`, `platform/*`, `data/demand_signals/`.
  - `.gitkeep` in leaf dirs under `data/`, `eval/`, and `docs/` so the structure is tracked by git.
- **agents/requirements.txt**
  - Package list: sqlalchemy, pyodbc, streamlit, httpx, python-dotenv, langchain, langchain-openai, langchain-community, langgraph, langsmith, crawl4ai, apscheduler, pydantic, structlog.
- **agents/.env.example**
  - Template for pipeline env vars: Azure OpenAI (API key, endpoint, deployment, LLM_PROVIDER), DATABASE_URL, LangSmith (LANGSMITH_API_KEY, LANGCHAIN_TRACING_V2), ingestion (JSEARCH_API_KEY, SCRAPING_TARGETS, INGESTION_SCHEDULE), and thresholds (SPAM_FLAG_THRESHOLD, SPAM_REJECT_THRESHOLD, SKILL_CONFIDENCE_THRESHOLD, BATCH_SIZE).
- **agents/docs/architecture/AGENTS_SCAFFOLD.md**
  - Documentation of the scaffold: what was created, Phase 1 vs Phase 2, conformance to canonical structure, and verification commands.
- **CHANGELOG.md** (this file)
  - Repo-wide changelog for implemented changes, additions, and removals.

### Changed

- **agents/requirements.txt**
  - Replaced previous version-pinned list (and optional dev deps pytest, ruff) with the unified list above per project request. Pytest and ruff can be re-added for development if needed.

### Removed

- None in this release.

---

*For detailed scaffold layout and conformance, see [agents/docs/architecture/AGENTS_SCAFFOLD.md](agents/docs/architecture/AGENTS_SCAFFOLD.md).*
