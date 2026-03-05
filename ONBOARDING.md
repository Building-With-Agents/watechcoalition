# Environment Setup (First-Time Clone)

This guide walks through setting up the watechcoalition platform after cloning the repository. It supports **Windows**, **Linux**, and **macOS**.

## Prerequisites

- **Node.js** 18.17 or later ([nodejs.org](https://nodejs.org/) or use [nvm](https://github.com/nvm-sh/nvm))
- **Python** 3.11 or later — [python.org/downloads](https://www.python.org/downloads/); on Windows, enable **"Add python.exe to PATH"** during install
- **Docker** (for local PostgreSQL) — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md)
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
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Description |
|----------|-------------|
| `AUTH_SECRET` | Generate with `openssl rand -base64 32` |
| `PYTHON_DATABASE_URL` | PostgreSQL connection string (see step 5) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource URL |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | e.g. `2025-01-01-preview` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Chat deployment name |
| `AZURE_OPENAI_EMBEDDING_ENDPOINT` | Same or separate Azure OpenAI endpoint |
| `AZURE_OPENAI_EMBEDDING_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_EMBEDDING_API_VERSION` | e.g. `2024-02-01` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME` | Embeddings deployment name |

### 2.2 Docker environment (.env.docker)

**Linux / macOS:** Copy the example and edit manually:

```bash
cp .env.docker.example .env.docker
```

**Windows:** You can also use the interactive setup script:

```powershell
.\scripts\setup-env-docker.ps1
```

Edit `.env.docker` and set the PostgreSQL variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | PostgreSQL superuser name |
| `POSTGRES_PASSWORD` | — | Strong password |
| `POSTGRES_DB` | `talent_finder` | Database name |
| `POSTGRES_PORT` | `5432` | Host port mapping |

> **MSSQL variables** (`MSSQL_SA_PASSWORD`, `MSSQL_DATABASE`, `MSSQL_PORT`) are only needed if you run the legacy Next.js app — see [section 8](#8-optional-mssql--nextjs-setup).

## 3. Start PostgreSQL (Docker)

PostgreSQL with pgvector is the primary database. The agent pipeline uses it exclusively via SQLAlchemy + psycopg2.

```bash
docker compose --env-file .env.docker up postgres -d
```

Wait for the container to be healthy:

```bash
docker ps --filter "name=postgres-server"
```

You should see `(healthy)` in the STATUS column. The pgvector extension is automatically enabled on first container creation (via `scripts/postgres-init/01-enable-pgvector.sql`).

See [docs/DOCKER_POSTGRESQL_SETUP.md](docs/DOCKER_POSTGRESQL_SETUP.md) for detailed setup, troubleshooting, and connection info.

## 4. Python Environment Setup

### 4.1 Install Python 3.11 (if not already installed)

1. Download from [python.org/downloads](https://www.python.org/downloads/) (Python 3.11 or later).
2. Run the installer. **On Windows**, check **"Add python.exe to PATH"**.
3. Verify:

   **Windows (PowerShell):**
   ```powershell
   py -3.11 --version
   ```

   **Linux / macOS:**
   ```bash
   python3 --version
   ```

### 4.2 Create and activate a virtual environment

Create a venv in `agents/.venv`. Always activate from the **project root** so tools like `streamlit` and `python -m agents...` resolve correctly.

**Create (one time):**

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

**Activate (every new terminal):**

**Windows (PowerShell):**
```powershell
agents\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source agents/.venv/bin/activate
```

After activation, your prompt shows `(.venv)` and `pip` works directly.

### 4.3 Install dependencies

```bash
pip install -r agents/requirements.txt
```

## 5. Set PYTHON_DATABASE_URL in .env

Add this to your `.env` file:

```env
PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YOUR_POSTGRES_PASSWORD@localhost:5432/talent_finder
```

- Replace `YOUR_POSTGRES_PASSWORD` with `POSTGRES_PASSWORD` from `.env.docker`
- Replace `5432` with `POSTGRES_PORT` if changed
- Replace `talent_finder` with `POSTGRES_DB` if changed

## 6. Seed PostgreSQL

The repo includes **JSON fixtures** in `scripts/pg-seed-data/fixtures/` with all reference data (~56,000 rows across 40 tables):

```bash
# With venv activated (see step 4.2)
python scripts/pg-seed-data/seed_pg_database.py
```

Or via npm:

```bash
npm run db:seed
```

The seed script:
- Creates the `dbo` schema with all tables, indexes, and constraints
- Loads all reference data (skills, companies, job postings, taxonomies, etc.)
- Creates agent-managed tables (`raw_ingested_jobs`, `normalized_jobs`, `job_ingestion_runs`)
- Adds Phase 1 columns to `job_postings`
- Is **idempotent** — safe to run multiple times (drops and recreates schema each time)

See [scripts/pg-seed-data/README.md](scripts/pg-seed-data/README.md) for details and troubleshooting.

## 7. Run the App

### Agent Pipeline

The **Job Intelligence Engine** is an eight-agent Python pipeline that will ingest, normalize, enrich, and analyze external job postings alongside the Next.js app. The `agents/` directory is scaffolded; the pipeline is built out over the **12-week curriculum** as specified in [CLAUDE.md](CLAUDE.md).

**Walking skeleton (Week 2+):**

```bash
python agents/pipeline_runner.py
```

**Streamlit dashboard:**

```bash
streamlit run agents/dashboard/streamlit_app.py
```

**Agent tests:**

```bash
cd agents && pytest tests/
```

**When the pipeline is implemented**, use these commands (activate the venv first):

- **Connectivity test:** `python -m agents.connectivity_test` (expect: `job_postings row count: <N>`)
- **Full pipeline:** `python -m agents.orchestration.scheduler`
- **Single agent:** `python -m agents.ingestion.agent --source jsearch --limit 50`

See [CLAUDE.md](CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](docs/planning/ARCHITECTURE_DEEP.md). See [agents/README.md](agents/README.md) for Python DATABASE_URL format.

### Next.js App

> Requires MSSQL setup — see [section 8](#8-optional-mssql--nextjs-setup) first.

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## 8. (Optional) MSSQL + Next.js Setup

> **MSSQL is being phased out.** It is only needed for the legacy Next.js/Prisma layer. You do **not** need MSSQL for the Python agent pipeline.

### 8.1 Start SQL Server (Docker)

Ensure `MSSQL_SA_PASSWORD`, `MSSQL_DATABASE`, and `MSSQL_PORT` are set in `.env.docker`.

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

If you also run a local SQL Server instance, set `MSSQL_PORT` to a non-default port (e.g. `11433`) so Prisma targets Docker.

### 8.2 Create the MSSQL Database

Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` and `talent_finder` with your `MSSQL_DATABASE` if different.

**Windows (PowerShell):**

```powershell
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

**Linux / macOS:**

```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "CREATE DATABASE talent_finder"
```

### 8.3 Set DATABASE_URL in .env

```env
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YOUR_SA_PASSWORD;encrypt=false;trustServerCertificate=true"
```

Replace `YOUR_SA_PASSWORD` and adjust port if needed. This `sqlserver://` format is required by Prisma/Next.js only.

### 8.4 Push Prisma Schema + Seed MSSQL

```bash
npx prisma db push
npx prisma generate
node prisma/seed-anonymized.mjs --idempotent
```

Tip: if `prisma db push` errors and your machine has a local SQL Server, verify `SELECT @@SERVERNAME, @@VERSION;` shows the container hostname, not your Windows machine name.

## 9. Optional: Generate Skill Embeddings

If you need vector search (skill autocomplete), visit `/admin/dashboard/generate-embeddings` as an admin and click **Generate**.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `PYTHON_DATABASE_URL` / PostgreSQL connection fails | Ensure PostgreSQL container is running (`docker ps`), port matches `.env.docker` (5432), password is correct. Try `127.0.0.1` instead of `localhost` if needed. |
| **Python `agents/`: DB connection fails** | Use `postgresql+psycopg2://` in `.env` for `PYTHON_DATABASE_URL`, not `sqlserver://`. See [agents/README.md](agents/README.md) and step 5. |
| `DATABASE_URL` connection fails (Next.js) | For MSSQL only — ensure SQL Server container is running, port matches `.env.docker`, password is correct |
| `Cannot find data type vector` during `prisma db push` | Usually means Prisma connected to the wrong SQL instance. Verify `DATABASE_URL` port and check `SELECT @@SERVERNAME, @@VERSION` |
| Password complexity error (MSSQL) | SQL Server requires: 8+ chars, upper, lower, number, special char |
| Port already in use | Change `POSTGRES_PORT` or `MSSQL_PORT` in `.env.docker` (e.g. 5433 or 11433) |
| Prisma errors after schema change | Run `npx prisma generate` |
| **Python resolves to wrong interpreter** | Run `deactivate`, remove `agents/.venv`, recreate with `python3 -m venv agents/.venv`, then `source agents/.venv/bin/activate` from project root |
| Docker not found | Install Docker — see [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) |
| `pip` not recognized / Python not found | Install Python 3.11, enable "Add python.exe to PATH", then use a venv (section 4). On Windows, use `py -3.11 -m venv .venv` and activate it before running `pip` |
| `SQLAlchemy OperationalError` / Python DB connection fails | Set `PYTHON_DATABASE_URL` in `.env` using `postgresql+psycopg2://` format (see step 5). Do not use Prisma's `sqlserver://` format. |

## Further Documentation

- [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) — Docker installation (Windows, macOS, Linux)
- [docs/DOCKER_POSTGRESQL_SETUP.md](docs/DOCKER_POSTGRESQL_SETUP.md) — PostgreSQL Docker setup (primary)
- [scripts/pg-seed-data/README.md](scripts/pg-seed-data/README.md) — PostgreSQL seed and fixtures
- [setup-MSSQL.md](setup-MSSQL.md) — Native MSSQL install (optional, for Next.js)
- [prisma-workflow.md](prisma-workflow.md) — DB schema workflow
- [API-routes.md](API-routes.md) — API reference
