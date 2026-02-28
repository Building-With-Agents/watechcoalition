# Computing for All — WaTech Coalition

This repository contains the source code for the **Washington Tech Workforce Coalition** platform: a Next.js and Prisma application that supports employers and job seekers in the tech industry (job listings, employer flows, and jobseeker experience). The stack includes TailwindCSS for styling. A key goal is to add the **Job Intelligence Engine** — an eight-agent Python pipeline to ingest, normalize, enrich, and analyze external job postings — which is planned and scaffolded in `agents/` but not yet implemented.

For a visual overview of the platform architecture (current and planned), see [docs/PROJECT_OVERVIEW.md](docs/PROJECT_OVERVIEW.md).

## Prerequisites

- Node.js >= 18.17.0

- Python >= 3.11 (for the agent pipeline)
- npm
- Docker (for local SQL Server)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
```

**First-time setup?** Follow the full environment setup guide:

- **[ONBOARDING.md](ONBOARDING.md)** — Clone, env config, Docker SQL, database seed, and run (Windows, Linux, macOS)

---

## Tutorials and Documentation

- [Environment setup (onboarding)](ONBOARDING.md)
- [Install Docker](docs/INSTALL_DOCKER.md)
- [Branching Strategy](docs/branch-strategy.md)
- [Set up local MSSQL Server](docs/setup-MSSQL.md)
- [Changing the DB schema](docs/prisma-workflow.md)
- [API Routes](docs/API-routes.md)
- [CSS Utilities & Styling Guide](docs/styling-guide.md)

## Available `npm run` Scripts

- `build`: Builds the application for production.
- `dev`: Runs the application in development mode.
- `prettier`: Formats the code using Prettier.
- `prettier:check`: Checks if the code is formatted according to Prettier.
- `start`: Starts the application in production mode.
- `db:seed:anonymized`: Seeds the database with anonymized JSON fixtures from `prisma/mock-data/` (recommended for local dev).
- `seed`: Seeds the database with synthetic/faker-generated data (does not use `prisma/mock-data/`).
- `lint`: Runs ESLint to check for code issues.

## Agent Pipeline (Walking Skeleton)

The **Job Intelligence Engine** is an eight-agent Python pipeline that ingests, normalizes, enriches, and analyzes external job postings. The walking skeleton (Week 2) is functional — all eight agent stubs process 10 demo job postings end-to-end with fixture data. Real agent logic is built out over the 12-week curriculum.

See [CLAUDE.md](CLAUDE.md) for full architecture details, agent specs, and build order.

```bash
# Setup (one time — from repo root)
py -3.11 -m venv agents/.venv
agents\.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r agents/requirements.txt

# Run the pipeline (produces agents/data/output/pipeline_run.json)
python agents/pipeline_runner.py

# Run the Streamlit dashboard (http://localhost:8501)
streamlit run agents/dashboard/streamlit_app.py

# Run agent tests
python -m pytest agents/tests/ -v
```

## Technologies Used

### Next.js App
- **Next.js**: React framework for server-side rendering. [Next.js Documentation](https://nextjs.org/docs)
- **Prisma**: Database ORM for TypeScript and Node.js. [Prisma Documentation](https://www.prisma.io/docs)
- **TailwindCSS**: Utility-first CSS framework. [TailwindCSS Documentation](https://tailwindcss.com/docs)
- **Auth.js**: Authentication library for Next.js. [Auth.js Documentation](https://authjs.dev/docs)
- **MSSQL**: Microsoft SQL Server database. [MSSQL Documentation](https://docs.microsoft.com/en-us/sql/sql-server)

### Agent Pipeline (Python)
- **LangGraph**: Multi-agent framework for StateGraph routing. [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- **LangChain**: LLM adapter layer. [LangChain Documentation](https://python.langchain.com/)
- **SQLAlchemy**: Python database access (MSSQL via pyodbc). [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- **Streamlit**: Read-only analytics dashboards. [Streamlit Documentation](https://docs.streamlit.io/)
- **LangSmith**: Agent tracing and evaluation. [LangSmith Documentation](https://docs.smith.langchain.com/)

## License

Copyright (c) 2026 Computing For All. All rights reserved.

This software is proprietary and not licensed for use, distribution, or modification without explicit permission. The source is available for transparency and collaboration within the project only. Commercial licensing may be available; contact Computing For All for inquiries. See [LICENSE](LICENSE) for details.
