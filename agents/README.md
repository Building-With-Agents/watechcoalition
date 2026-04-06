# Job Intelligence Engine — Agents

Python agent pipeline for the watechcoalition Job Intelligence Engine: ingestion, normalization, skills extraction, enrichment, analytics, visualization, and orchestration. See [CLAUDE.md](../CLAUDE.md) in the repo root for architecture, event contracts, and build order.

## Quick start

**Requires Python 3.11** (do not use 3.12+ — a dependency requires 3.11). See [ONBOARDING.md](../ONBOARDING.md) for full setup.

Create and activate the venv (one time):

**Windows (PowerShell):**
```powershell
cd agents
py -3.11 -m venv .venv
cd ..
agents\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
cd agents && python3.11 -m venv .venv && cd ..
source agents/.venv/bin/activate
```

Install and run:

```bash
pip install -r agents/requirements.txt

# Seed local DB with enriched data (first time)
python scripts/pg-seed-data/seed_agent_data.py

# Flywheel pipeline (production)
python agents/scripts/batch_ingest.py                          # Loop 1: ingest
python agents/scripts/run_processing_loop.py --batch-size 50   # Loop 2: process

# Demo run (fixture data only, Week 2 demo)
# python agents/pipeline_runner.py

# Streamlit dashboard
streamlit run agents/dashboard/app.py
# (alias) streamlit run agents/dashboard/streamlit_app.py
```

## Azure PostgreSQL (shared DB)

To provision an Azure Database for PostgreSQL Flexible Server and mirror schema/data from local Docker (or sync via fixtures), use the runbook:

- **[Azure PostgreSQL Runbook](../docs/runbooks/AZURE_POSTGRES_JOB_INTELLIGENCE_ENGINE.md)** — Create resource group `rg-job-inteligence-engine`, create Flexible Server, enable pgvector, mirror from Docker (pg_dump/restore), and use the fixtures workflow so devs can share reference data and load it into the Azure DB.

## Tests

```bash
python -m pytest agents/tests/ -v
```

## Layout

- `ingestion/`, `normalization/`, `skills_extraction/`, `enrichment/`, `analytics/`, `visualization/`, `orchestration/` — agent modules
- `common/` — events, message bus, LLM adapter, data store, config
- `dashboard/` — Streamlit app
- `data/` — staging, fixtures, output (see `.gitkeep` and `.gitignore`)
