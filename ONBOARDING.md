# Environment Setup (First-Time Clone)

This guide walks through setting up the Tech Talent Showcase app after cloning the repository. It supports **Windows**, **Linux**, and **macOS**.

## Prerequisites

- **Node.js** 18.17 or later ([nodejs.org](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm))
- **Python** 3.11 or later ([python.org](https://www.python.org/downloads/))
- **Docker** (for local SQL Server) — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) for installation instructions
- **Git**

## 1. Clone and Install Dependencies

```bash
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
npm ci
```

## 2. Environment Configuration

### 2.1 Application environment (.env)

Copy the example file and fill in required values:

```bash
# All platforms
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `AUTH_SECRET` | Generate with `openssl rand -base64 32` |
| `DATABASE_URL` | See step 4 — you'll set this after starting SQL |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | e.g. `2025-01-01-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Chat deployment name |
| `AZURE_OPENAI_EMBEDDING_ENDPOINT` | Same or separate Azure OpenAI endpoint |
| `AZURE_OPENAI_EMBEDDING_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_EMBEDDING_API_VERSION` | e.g. `2024-02-01` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` | Embeddings deployment name |

### 2.2 Docker SQL environment (.env.docker)

**Windows:** Run the interactive setup script (recommended):

```powershell
.\scripts\setup-env-docker.ps1
```

**Linux / macOS:** Copy the example and edit manually:

```bash
cp .env.docker.example .env.docker
```

Edit `.env.docker` and set:

- `MSSQL_SA_PASSWORD` — Strong password (min 8 chars, uppercase, lowercase, number, special char)
- `MSSQL_DATABASE` — Default: `talent_finder`
- `MSSQL_PORT` — Default: `1433`

## 3. Start SQL Server (Docker)

This project uses SQL Server `mcr.microsoft.com/mssql/server:2025-latest` in [docker-compose.yml](docker-compose.yml).
If you also run a local SQL Server instance on your machine, set `MSSQL_PORT` in `.env.docker` to a non-default host port (for example `11433`) so Prisma targets Docker, not the local instance.

**Windows:**

```powershell
.\scripts\start-sql-server.ps1
```

**Linux / macOS:**

```bash
docker compose --env-file .env.docker up -d
```

Wait for the container to be healthy. To verify:

```bash
docker ps --filter "name=mssql-server"
```

## 4. Create the database (all platforms)

**You must create the database before pushing the Prisma schema (step 5).**  
Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` and `talent_finder` with your `MSSQL_DATABASE` if different.

**Windows (PowerShell):**
```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

**Linux / macOS:**
```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

If the database already exists, you can skip this step.

## 5. Set DATABASE_URL in .env

After SQL Server is running and the database is created, set `DATABASE_URL` in `.env` to match your `.env.docker` values. **This format is for Prisma/Next.js only.**

```env
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YOUR_SA_PASSWORD;encrypt=false;trustServerCertificate=true"
```

Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` from `.env.docker`, and adjust `1433` if you changed `MSSQL_PORT`.
If Docker is mapped to `11433`, your URL must use `localhost:11433`.

### 5.1 Python / agents (SQLAlchemy + pyodbc)

The **agents pipeline** uses `agents/.env` and **SQLAlchemy + pyodbc**. The `sqlserver://` format above does **not** work with Python. Use `mssql+pyodbc://` in `agents/.env`:

```env
# In agents/.env (copy from agents/.env.example first)
DATABASE_URL="mssql+pyodbc://SA:YOUR_SA_PASSWORD@127.0.0.1:1433/talent_finder?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
```

Replace `YOUR_SA_PASSWORD` and `talent_finder` to match your setup. Use `127.0.0.1` instead of `localhost` if you see connection errors. Verify with:

```bash
python -m agents.connectivity_test
```

Expected output: `job_postings row count: <N>`.

## 6. Database Schema and Seed (Anonymized Fixtures)

The repo includes **pre-anonymized JSON fixtures** in `prisma/mock-data/`. Populate the database from these:

```bash
npx prisma db push
npx prisma generate
npm run db:seed:anonymized
```

Seeding behavior notes:

- Seed runs in dependency-safe order (parents before children) to satisfy FK constraints.
- If fixture references are orphaned, the seed script auto-repairs those FK fields to deterministic fallback parent IDs before insert.
- FK violations are not skipped at insert time; unresolved references after repair fail fast with a clear error.

Tip: if `prisma db push` errors and your machine has local SQL Server installed, verify you are connected to Docker SQL first:

```sql
SELECT @@SERVERNAME, @@VERSION;
```

`@@SERVERNAME` should be the container hostname, not your Windows host name (for example `DESKTOP-PC`).

## 7. Python Agent Environment (Pipeline — Not Yet Implemented)

The **Job Intelligence Engine** is an eight-agent Python pipeline that will ingest, normalize, enrich, and analyze external job postings alongside the Next.js app. **It is not yet implemented.** The `agents/` directory is scaffolded (structure and `requirements.txt`); the pipeline will be built out over the **12-week curriculum** as specified in [CLAUDE.md](CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](docs/planning/ARCHITECTURE_DEEP.md).

Set up the Python environment now so you’re ready to develop agents as you follow the weekly deliverables:

```bash
# From project root (watechcoalition/)
cd agents
python3 -m venv .venv
cd ..
# Linux / macOS: activate from project root
source agents/.venv/bin/activate
# Windows (PowerShell): .\agents\.venv\Scripts\Activate.ps1
pip install -r agents/requirements.txt
```

If `python3` resolves to the wrong interpreter (e.g. Homebrew), run `deactivate`, remove `agents/.venv`, recreate it, and run `source agents/.venv/bin/activate` again from the project root.

**When the pipeline is implemented**, use these commands (activate the venv first):

- **Connectivity test:** `python -m agents.connectivity_test` (expect: `job_postings row count: <N>`)
- **Streamlit dashboard:** `streamlit run agents/dashboard/streamlit_app.py`
- **Full pipeline:** `python -m agents.orchestration.scheduler`
- **Single agent:** `python -m agents.ingestion.agent --source jsearch --limit 50`
- **Agent tests:** `cd agents && pytest tests/`

See [CLAUDE.md](CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](docs/planning/ARCHITECTURE_DEEP.md). See [agents/README.md](agents/README.md) for Python DATABASE_URL format.

## 8. Run the App

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## 9. Optional: Generate Skill Embeddings

If you need vector search (skill autocomplete), visit `/admin/dashboard/generate-embeddings` as an admin and click **Generate**.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `DATABASE_URL` connection fails | Ensure SQL container is running (`docker ps`), port matches `.env.docker`, password is correct |
| **Python `agents/`: DATABASE_URL fails** | Use `mssql+pyodbc://` in `agents/.env`, not `sqlserver://`. See [agents/README.md](agents/README.md) and section 5.1 above. Try `127.0.0.1` instead of `localhost`. |
| `Cannot find data type vector` during `prisma db push` | Usually means Prisma connected to the wrong SQL instance. Verify `DATABASE_URL` port and check `SELECT @@SERVERNAME, @@VERSION` |
| Password complexity error | SQL Server requires: 8+ chars, upper, lower, number, special char |
| Port already in use | Change `MSSQL_PORT` in `.env.docker` (e.g. to 11433) |
| Prisma errors after schema change | Run `npx prisma generate` |
| **Python resolves to wrong interpreter** | Run `deactivate`, remove `agents/.venv`, recreate with `python3 -m venv agents/.venv`, then `source agents/.venv/bin/activate` from project root |
| Docker not found | Install Docker — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) |

## Further Documentation

- [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) — Docker installation (Windows, macOS, Linux)
- [docs/DOCKER_SQL_SERVER_SETUP.md](docs/DOCKER_SQL_SERVER_SETUP.md) — Detailed SQL Server Docker setup
- [setup-MSSQL.md](setup-MSSQL.md) — Native MSSQL install (alternative to Docker)
- [prisma-workflow.md](prisma-workflow.md) — DB schema workflow
- [API-routes.md](API-routes.md) — API reference
