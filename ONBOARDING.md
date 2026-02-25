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

After SQL Server is running and the database is created, set `DATABASE_URL` in `.env` to match your `.env.docker` values:

```env
DATABASE_URL="sqlserver://localhost:1433;database=talent_finder;user=SA;password=YOUR_SA_PASSWORD;encrypt=false;trustServerCertificate=true"
```

Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` from `.env.docker`, and adjust `1433` if you changed `MSSQL_PORT`.
If Docker is mapped to `11433`, your URL must use `localhost:11433`.

> **Note:** This `sqlserver://` format is required by Prisma/Next.js. Python agents (SQLAlchemy) use a different format and a separate variable — see step 7.4.

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

Python agents use SQLAlchemy + pyodbc, which requires a **different connection string format** than Prisma's `DATABASE_URL`. Add this to your `.env` file:

```env
PYTHON_DATABASE_URL=mssql+pyodbc://SA:YOUR_SA_PASSWORD@localhost:1433/talent_finder?driver=ODBC+Driver+17+for+SQL+Server
```

- Replace `YOUR_SA_PASSWORD` with your `MSSQL_SA_PASSWORD` from `.env.docker`.
- Replace `1433` with your `MSSQL_PORT` if you changed it (e.g. `11433`).
- Replace `talent_finder` with your `MSSQL_DATABASE` if you changed it.

> **Why a separate variable?** Prisma requires `sqlserver://host:port;key=value` syntax. SQLAlchemy requires `mssql+pyodbc://user:pass@host:port/db?driver=...` syntax. They are not interchangeable — using the wrong format causes a silent connection failure.

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
| `SQLAlchemy OperationalError` / Python DB connection fails | `DATABASE_URL` uses Prisma's `sqlserver://` format and does not work with SQLAlchemy. Set `PYTHON_DATABASE_URL` in `.env` using `mssql+pyodbc://` format (see step 7.4) |

## Further Documentation

- [docs/INSTALL_DOCKER.md](docs/INSTALL_DOCKER.md) — Docker installation (Windows, macOS, Linux)
- [docs/DOCKER_SQL_SERVER_SETUP.md](docs/DOCKER_SQL_SERVER_SETUP.md) — Detailed SQL Server Docker setup
- [setup-MSSQL.md](setup-MSSQL.md) — Native MSSQL install (alternative to Docker)
- [prisma-workflow.md](prisma-workflow.md) — DB schema workflow
- [API-routes.md](API-routes.md) — API reference
