# Changelog — agents/

All notable changes to the `agents/` directory and agent-related documentation are documented here. Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Summary

- Implemented the full agents directory scaffold, connectivity test (SQLAlchemy + pyodbc), and Python/Node coexistence docs.
- Documented Python DATABASE_URL format (`mssql+pyodbc://`), venv location (`agents/.venv`), and Windows-specific setup.
- Resolved environment, dependency, and database connection issues (see **Problems and fixes** below).

---

### Added

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

---

### Changed

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

---

### Removed

- None.

---

### Problems encountered and fixes

| Problem | Cause | Fix |
|--------|--------|-----|
| **`source` not recognized (PowerShell)** | `source` is Bash; PowerShell uses a different command. | Use `.\agents\.venv\Scripts\Activate.ps1` (from project root) or `.\.venv\Scripts\Activate.ps1` from inside `agents/`. |
| **`python3` not found (Windows)** | On Windows the command is usually `python` or `py`, not `python3`. | Use `python -m venv .venv` or `py -3.12 -m venv .venv`. |
| **lxml build failed (Python 3.14)** | No pre-built lxml wheel for Python 3.14 on Windows; build requires libxml2/C++ and fails. | Use **Python 3.11 or 3.12** for the agents venv: `py -3.12 -m venv agents/.venv`. Then `pip install -r agents/requirements.txt` uses pre-built wheels. |
| **ODBC IM002: Data source name not found** | Microsoft ODBC Driver for SQL Server not installed. | Install [ODBC Driver 18 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server). Ensure `agents/.env` uses `driver=ODBC+Driver+18+for+SQL+Server` (or 17 if that’s what you install). |
| **Connection refused (10061) to localhost:1433** | SQL Server not running or Docker exposes a different port. | Start SQL Server (e.g. `docker compose up -d sqlserver`). In `agents/.env`, set `DATABASE_URL` to the **host port** Docker uses (e.g. `127.0.0.1:11433` or `localhost:11433`), not the container’s internal port. |
| **DATABASE_URL not set when running connectivity test** | Script could not find `agents/.env` when run as a module from repo root. | Copy `agents/.env.example` to `agents/.env` and fill in values. Connectivity script also has a fallback to load `Path.cwd() / "agents" / ".env"`. |
| **SAWarning: Unrecognized server version** | SQLAlchemy doesn’t recognize some SQL Server version strings. | Harmless for simple queries (e.g. `COUNT(*)`). Can be ignored; connectivity test still succeeds (`job_postings row count: 25`). |

---

### Verification

- **Connectivity test (Python):** From project root with `agents/.venv` activated: `python -m agents.connectivity_test`. Expected: `job_postings row count: <N>` (e.g. 25). Exit code 0.
- **Next.js:** From project root (venv not required): `npm run dev`. App should run at http://localhost:3000. Confirms Python scaffold did not affect the Node.js app.
- **Exit venv:** Run `deactivate` in the same terminal to leave the agents venv.

---

*Scaffold details: [agents/docs/architecture/AGENTS_SCAFFOLD.md](architecture/AGENTS_SCAFFOLD.md). Python env and DATABASE_URL: [agents/README.md](../README.md).*
