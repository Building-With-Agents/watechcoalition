# Job Intelligence Engine — Agents

Python agent pipeline for the watechcoalition Job Intelligence Engine: ingestion, normalization, skills extraction, enrichment, analytics, visualization, and orchestration. See [CLAUDE.md](../CLAUDE.md) in the repo root for architecture, event contracts, and build order.

## Quick start

From repo root with venv activated:

```bash
pip install -r agents/requirements.txt
python agents/pipeline_runner.py
streamlit run agents/dashboard/streamlit_app.py
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
