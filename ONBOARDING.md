# Environment Setup (First-Time Clone)

This guide walks through setting up the Tech Talent Showcase app after cloning the repository. It supports **Windows**, **Linux**, and **macOS**.

## Prerequisites

- **Node.js** 18.17 or later ([nodejs.org](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm))
- **Python** 3.11 or later — [python.org/downloads](https://www.python.org/downloads/); on Windows, enable **"Add python.exe to PATH"** during install
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

For the Python agent pipeline (PostgreSQL), also set:
- `POSTGRES_USER` — Default: `postgres`
- `POSTGRES_PASSWORD` — Strong password
- `POSTGRES_DB` — Default: `talent_finder`
- `POSTGRES_PORT` — Default: `5432`

## 3. Start PostgreSQL (Docker) — Primary Database

PostgreSQL is the **primary database** for all development. The Python agent pipeline uses it exclusively via SQLAlchemy + psycopg2, with pgvector for embedding similarity search.

After configuring `.env.docker` with PostgreSQL variables (see section 2.2):

**All platforms:**

```bash
docker compose --env-file .env.docker up postgres -d
```

Wait for the container to be healthy:

```bash
docker ps --filter "name=postgres-server"
```

The pgvector extension is automatically enabled on first container creation (via the init script in `scripts/postgres-init/`).

## 3.5 Start SQL Server (Docker) — Deprecated

> **MSSQL is deprecated.** It is only needed for the legacy Next.js/Prisma layer and is being phased out. New development should target PostgreSQL exclusively. You do **not** need MSSQL for the Python agent pipeline.

If you need the Next.js app running locally, start SQL Server:

**Windows:**

```powershell
.\scripts\start-sql-server.ps1
```

**Linux / macOS:**

```bash
docker compose --env-file .env.docker up mssql -d
```

Wait for the container to be healthy:

```bash
docker ps --filter "name=mssql-server"
```

If you also run a local SQL Server instance on your machine, set `MSSQL_PORT` in `.env.docker` to a non-default host port (for example `11433`) so Prisma targets Docker, not the local instance.

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

After SQL Server is running and the database is created, set `DATABASE_URL` in `.env` to match your `.env.docker` values:

```env
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YOUR_SA_PASSWORD;encrypt=false;trustServerCertificate=true"
```

Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` from `.env.docker`, and adjust `1433` if you changed `MSSQL_PORT`.
If Docker is mapped to `11433`, your URL must use `localhost:11433`.

> **Note:** This `sqlserver://` format is required by Prisma/Next.js. Python agents (SQLAlchemy) use a different format and a separate variable — see step 7.4.

## 6. Seed PostgreSQL (Primary)

The repo includes **JSON fixtures** in `scripts/pg-seed-data/fixtures/` with all reference data (~56,000 rows across 40 tables). Seed the database with one command:

```bash
# Activate venv first (see step 7.2 if not done yet)
agents\.venv\Scripts\Activate.ps1          # Windows PowerShell
# source agents/.venv/bin/activate         # macOS / Linux

# Install dependencies (if not done yet)
pip install -r agents/requirements.txt

# Seed PostgreSQL
python scripts/pg-seed-data/seed_pg_database.py
```

The seed script:
- Creates the `dbo` schema with all tables, indexes, and constraints
- Loads all reference data (skills, companies, job postings, taxonomies, etc.)
- Creates agent-managed tables (`raw_ingested_jobs`, `normalized_jobs`, `job_ingestion_runs`)
- Adds Phase 1 columns to `job_postings`
- Is **idempotent** — safe to run multiple times (drops and recreates schema each time)

See [scripts/pg-seed-data/README.md](scripts/pg-seed-data/README.md) for details and troubleshooting.

### 6.5 Seed MSSQL (Deprecated — only if running Next.js)

> **Skip this unless you need the Next.js app.** MSSQL is deprecated and being phased out.

If you need the Next.js/Prisma layer, seed MSSQL from the anonymized fixtures in `prisma/mock-data/`:

```bash
npx prisma db push
npx prisma generate
node prisma/seed-anonymized.mjs --idempotent
```

Tip: if `prisma db push` errors and your machine has local SQL Server installed, verify you are connected to Docker SQL first:

```sql
SELECT @@SERVERNAME, @@VERSION;
```

`@@SERVERNAME` should be the container hostname, not your Windows host name (for example `DESKTOP-PC`).

## 7. Python Agent Environment (Pipeline — Not Yet Implemented)

The **Job Intelligence Engine** is an eight-agent Python pipeline that will ingest, normalize, enrich, and analyze external job postings alongside the Next.js app. **It is not yet implemented.** The `agents/` directory is scaffolded (structure and `requirements.txt`); the pipeline will be built out over the **12-week curriculum** as specified in [CLAUDE.md](CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](docs/planning/ARCHITECTURE_DEEP.md).

Set up the Python environment now so you’re ready to develop agents as you follow the weekly deliverables.

### 7.1 Install Python 3.11 (if not already installed)

1. Download from [python.org/downloads](https://www.python.org/downloads/) (Python 3.11 or later).
2. Run the installer. **On Windows**, check **"Add python.exe to PATH"** at the bottom.
3. Verify installation:

   **Windows (PowerShell):**
   ```powershell
   py -3.11 --version
   ```

   **Linux / macOS:**
   ```bash
   python3 --version
   ```

   If you see a version number (e.g. `Python 3.11.5`), you're good.

### 7.2 Create and activate a virtual environment

Create a venv in `agents/.venv` so dependencies stay isolated. Always activate it from the **project root** before running any Python commands, so that tools like `streamlit run agents/...` and `python -m agents...` resolve correctly.

**Create the venv** (one time only):

**Windows (PowerShell):**
```powershell
cd agents
py -3.11 -m venv .venv
cd ..
```

**Linux / macOS:**
```bash
cd agents && python3 -m venv .venv && cd ..
```

**Activate from the project root** (every new terminal session):

**Windows (PowerShell):**
```powershell
agents\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source agents/.venv/bin/activate
```

After activation, your prompt will show `(.venv)` and `pip` will work directly.

### 7.3 Install dependencies

```bash
pip install -r agents/requirements.txt
```

### 7.4 Set PYTHON_DATABASE_URL in .env

Python agents use SQLAlchemy + psycopg2, which connects to **PostgreSQL** (not the MSSQL instance used by Next.js). Add this to your `.env` file:

```env
PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/talent_finder
```

- Replace `YOUR_POSTGRES_PASSWORD` with your `POSTGRES_PASSWORD` from `.env.docker`.
- Replace `5432` with your `POSTGRES_PORT` if you changed it.
- Replace `talent_finder` with your `POSTGRES_DB` if you changed it.

> **Why PostgreSQL?** PostgreSQL is the primary database for the agent pipeline, with pgvector for embedding similarity search. MSSQL is deprecated — it is only used by the legacy Next.js/Prisma layer and is being phased out. A future DB-unification effort will consolidate both layers on PostgreSQL.

**When the pipeline is implemented**, you will use commands like the following (included here for reference; they will not work until the corresponding agents exist):

- **Streamlit dashboard:** `streamlit run agents/dashboard/streamlit_app.py`
- **Full pipeline (Orchestration Agent scheduler):** `python -m agents.orchestration.scheduler`
- **Single agent (e.g. Ingestion):** `python -m agents.ingestion.agent --source jsearch --limit 50`
- **Agent tests:** `cd agents && pytest tests/`

See [CLAUDE.md](CLAUDE.md) for architecture, rules, and the 12-week build order; see [docs/planning/ARCHITECTURE_DEEP.md](docs/planning/ARCHITECTURE_DEEP.md) for per-agent implementation specs.

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
| `Cannot find data type vector` during `prisma db push` | Usually means Prisma connected to the wrong SQL instance. Verify `DATABASE_URL` port and check `SELECT @@SERVERNAME, @@VERSION` |
| Password complexity error | SQL Server requires: 8+ chars, upper, lower, number, special char |
| Port already in use | Change `MSSQL_PORT` in `.env.docker` (e.g. to 11433) |
| Prisma errors after schema change | Run `npx prisma generate` |
| Docker not found | Install Docker — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) |
| `pip` not recognized / Python not found | Install Python 3.11, enable "Add python.exe to PATH", then use a venv (section 7). On Windows, use `py -3.11 -m venv .venv` and activate it before running `pip` |
| `SQLAlchemy OperationalError` / Python DB connection fails | `DATABASE_URL` uses Prisma's `sqlserver://` format and does not work with SQLAlchemy. Set `PYTHON_DATABASE_URL` in `.env` using `postgresql+psycopg2://` format (see step 7.4) |
| `PYTHON_DATABASE_URL` connection fails (PostgreSQL) | Ensure PostgreSQL container is running (`docker ps --filter "name=postgres-server"`), port matches `.env.docker`, password is correct |

## Further Documentation

- [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) — Docker installation (Windows, macOS, Linux)
- [docs/DOCKER_POSTGRESQL_SETUP.md](docs/DOCKER_POSTGRESQL_SETUP.md) — Detailed PostgreSQL Docker setup
- [scripts/pg-seed-data/README.md](scripts/pg-seed-data/README.md) — PostgreSQL seed data guide
- [docs/setup-MSSQL.md](docs/setup-MSSQL.md) — Native MSSQL install (deprecated — Next.js only)
- [docs/prisma-workflow.md](docs/prisma-workflow.md) — DB schema workflow (Prisma/MSSQL — deprecated)
- [docs/API-routes.md](docs/API-routes.md) — API reference
