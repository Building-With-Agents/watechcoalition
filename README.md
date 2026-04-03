# Computing for All — WaTech Coalition

This repository contains the source code for the **Washington Tech Workforce Coalition** platform: a Next.js and Prisma application that supports employers and job seekers in the tech industry (job listings, employer flows, and jobseeker experience). The stack includes TailwindCSS for styling. A key goal is to add the **Job Intelligence Engine** — an eight-agent Python pipeline to ingest, normalize, enrich, and analyze external job postings — which is planned and scaffolded in `agents/` but not yet implemented.

For a visual overview of the platform architecture (current and planned), see [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md).

## Prerequisites

- Node.js >= 18.17.0

- Python 3.11 (pinned — for the agent pipeline)
- npm
- Docker (for local PostgreSQL and Redis)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
```

**First-time setup?** Follow the full environment setup guide:

- **[ONBOARDING.md](ONBOARDING.md)** — Clone, env config, Docker PostgreSQL, database seed, and run (Windows, Linux, macOS)

---

## Tutorials and Documentation

- [Environment setup (onboarding)](ONBOARDING.md)
- [Install Docker](docs/INSTALL_DOCKER.md)
- [Branching Strategy](docs/branch-strategy.md)
- [PostgreSQL Docker Setup](docs/DOCKER_POSTGRESQL_SETUP.md)
- [Redis Setup](#redis-message-bus) — Redis Streams for inter-agent events
- [Changing the DB schema](docs/prisma-workflow.md) (legacy — new schema changes go through SQLAlchemy)
- [API Routes](docs/API-routes.md)
- [CSS Utilities & Styling Guide](docs/styling-guide.md)

## Available `npm run` Scripts

- `build`: Builds the application for production.
- `dev`: Runs the application in development mode.
- `prettier`: Formats the code using Prettier.
- `prettier:check`: Checks if the code is formatted according to Prettier.
- `start`: Starts the application in production mode.
- `db:seed`: Seeds the PostgreSQL database with anonymized fixtures via `scripts/pg-seed-data/seed_pg_database.py` (recommended for local dev).
- `seed`: Seeds the MSSQL database with synthetic/faker-generated data via Prisma (deprecated).
- `lint`: Runs ESLint to check for code issues.

## Agent Pipeline (Flywheel Architecture)

The **Job Intelligence Engine** is an eight-agent Python pipeline that ingests, normalizes, enriches, and analyzes external job postings. The pipeline uses a **flywheel pattern**: ingestion (cheap HTTP) is decoupled from processing (LLM-based extraction and enrichment) so each loop runs independently at its own pace.

See [CLAUDE.md](CLAUDE.md) for full architecture details, agent specs, and build order.

### Setup (one time)

```bash
py -3.11 -m venv agents/.venv
agents\.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r agents/requirements.txt
```

### Seed Local Database with Enriched Data

New devs should seed their local database with pre-processed job postings so analytics and visualization have data to work with:

```bash
python scripts/pg-seed-data/seed_agent_data.py
```

This imports enriched records from `scripts/pg-seed-data/agent-fixtures/` using UPSERT (safe to run multiple times).

### Run the Pipeline

```bash
# Loop 1: Bulk ingest from JSearch API (budget-aware, key rotation)
python agents/scripts/batch_ingest.py              # run all queries from config
python agents/scripts/batch_ingest.py --dry-run    # preview without API calls

# Loop 2: Paced processing (normalize → extract → enrich)
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2

# Streamlit dashboard (http://localhost:8501)
streamlit run agents/dashboard/streamlit_app.py

# Agent tests
python -m pytest agents/tests/ -v
```

### Environment Variables (Pipeline)

| Variable | Required | Description |
|----------|----------|-------------|
| `PYTHON_DATABASE_URL` | Yes | PostgreSQL connection string |
| `JSEARCH_API_KEY` | For ingestion | RapidAPI JSearch key (primary) |
| `JSEARCH_API_KEY_2` | Optional | Second JSearch key for budget rotation |
| `NORM_BATCH_SIZE` | Optional | Records per processing batch (default: 50) |
| `PROCESSING_DELAY` | Optional | Seconds between processing batches (default: 10) |
| `AZURE_OPENAI_*` | For extraction/enrichment | Azure OpenAI credentials |

### Scripts

| Script | Purpose |
|--------|---------|
| `agents/scripts/batch_ingest.py` | Loop 1 — budget-aware JSearch ingestion |
| `agents/scripts/run_processing_loop.py` | Loop 2 — paced normalize/extract/enrich |
| `scripts/pg-seed-data/seed_agent_data.py` | Import enriched data to local DB |
| `scripts/pg-seed-data/export_agent_data.py` | Export pipeline data to JSON fixtures (admin) |
| `scripts/pg-seed-data/clean_stale_postings.py` | Purge old pipeline data before re-seeding (admin) |
| `agents/config/ingestion_queries.yaml` | Editable query configuration for batch_ingest |

## Technologies Used

### Next.js App
- **Next.js**: React framework for server-side rendering. [Next.js Documentation](https://nextjs.org/docs)
- **Prisma**: Database ORM for TypeScript and Node.js (being phased out — SQLAlchemy is now the single DB authority). [Prisma Documentation](https://www.prisma.io/docs)
- **TailwindCSS**: Utility-first CSS framework. [TailwindCSS Documentation](https://tailwindcss.com/docs)
- **Auth.js**: Authentication library for Next.js. [Auth.js Documentation](https://authjs.dev/docs)
- **MSSQL**: Microsoft SQL Server database (deprecated — replaced by PostgreSQL via SQLAlchemy). [MSSQL Documentation](https://docs.microsoft.com/en-us/sql/sql-server)

### Agent Pipeline (Python)
- **LangGraph**: Multi-agent framework for StateGraph routing. [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- **LangChain**: LLM adapter layer. [LangChain Documentation](https://python.langchain.com/)
- **SQLAlchemy**: Python database access (PostgreSQL via psycopg2). [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- **Streamlit**: Read-only analytics dashboards. [Streamlit Documentation](https://docs.streamlit.io/)
- **Redis Streams**: Inter-agent event bus (`XADD`/`XREADGROUP`/`XACK`). [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- **Langfuse**: LLM observability and tracing. [Langfuse Documentation](https://langfuse.com/docs)

## License

Copyright (c) 2026 Computing For All. All rights reserved.

This software is proprietary and not licensed for use, distribution, or modification without explicit permission. The source is available for transparency and collaboration within the project only. Commercial licensing may be available; contact Computing For All for inquiries. See [LICENSE](LICENSE) for details.
