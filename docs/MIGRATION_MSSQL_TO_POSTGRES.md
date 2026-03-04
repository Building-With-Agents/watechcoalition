# Migrating the Agent Pipeline from MSSQL to PostgreSQL

This document covers the migration of the **Python agent pipeline** database from
MSSQL (SQL Server) to PostgreSQL. The Next.js app continues to use MSSQL via
Prisma in this phase. A future Phase 2 migration will unify both layers on
PostgreSQL.

**Why PostgreSQL?** See `docs/planning/ARCHITECTURAL_DECISIONS.md`, Decision #19
for the full rationale (pgvector for embedding similarity search, Python ecosystem
fit, simpler type system, no ODBC driver friction).

---

## Prerequisites

- Docker installed and running
- Existing `.env` and `.env.docker` files (from [ONBOARDING.md](../ONBOARDING.md) setup)
- MSSQL container running with seeded data (`docker ps --filter "name=mssql-server"`)
- Python 3.11+ with virtual environment activated

---

## Step 1: Update `.env.docker`

Add PostgreSQL variables to your existing `.env.docker` file. **Keep the MSSQL
variables** (they are still needed for Next.js):

```env
# PostgreSQL Docker Configuration (Python agent pipeline)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YourPostgresP4ssw0rd
POSTGRES_DB=talent_finder
POSTGRES_PORT=5432
```

Or re-run the setup script (Windows):

```powershell
.\scripts\setup-env-docker.ps1
```

---

## Step 2: Start PostgreSQL container

```bash
docker compose --env-file .env.docker up postgres -d
```

Verify it is healthy:

```bash
docker ps --filter "name=postgres-server"
```

You should see `(healthy)` in the STATUS column within ~30 seconds. The pgvector
extension is automatically enabled on first container creation via the init script
in `scripts/postgres-init/`.

To verify pgvector:

```bash
docker exec -it postgres-server psql -U postgres -d talent_finder -c "\dx"
```

You should see `vector` in the list of installed extensions.

---

## Step 3: Migrate data from MSSQL to PostgreSQL (pgloader)

pgloader copies the entire schema and data from MSSQL to PostgreSQL in one step.
It handles type conversions automatically.

### 3a. Edit the pgloader config

Open `scripts/pgloader/migrate-all-tables.load` and update the connection strings
to match your `.env.docker` credentials:

```
FROM mssql://SA:<your-MSSQL_SA_PASSWORD>@localhost:<MSSQL_PORT>/talent_finder
INTO postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@localhost:<POSTGRES_PORT>/talent_finder
```

### 3b. Run pgloader via Docker

pgloader is available as a Docker image — no host installation needed:

**Linux / macOS:**

```bash
docker run --rm --network host \
  -v "$(pwd)/scripts/pgloader:/pgloader" \
  dimitri/pgloader:latest \
  pgloader /pgloader/migrate-all-tables.load
```

**Windows (PowerShell):**

```powershell
docker run --rm --network host `
  -v "${PWD}/scripts/pgloader:/pgloader" `
  dimitri/pgloader:latest `
  pgloader /pgloader/migrate-all-tables.load
```

> **Note:** `--network host` allows pgloader to reach both `localhost:1433` (MSSQL)
> and `localhost:5432` (PostgreSQL). On Docker Desktop for Windows/macOS, if
> `--network host` does not work, use `host.docker.internal` instead of `localhost`
> in the connection strings.

### 3c. Verify migration

```bash
# Count tables
docker exec -it postgres-server psql -U postgres -d talent_finder -c "\dt"

# Spot-check key tables
docker exec -it postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM skills;"
docker exec -it postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM companies;"
docker exec -it postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM job_postings;"
```

Compare counts with MSSQL:

```bash
docker exec -it mssql-server /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -Q "SELECT count(*) FROM skills"
```

---

## Step 4: Update Python dependencies

Activate your virtual environment and install:

**Windows (PowerShell):**

```powershell
agents\.venv\Scripts\Activate.ps1
pip install -r agents/requirements.txt
```

**Linux / macOS:**

```bash
source agents/.venv/bin/activate
pip install -r agents/requirements.txt
```

This installs `psycopg2-binary` (which replaced `pyodbc`). If you previously had
`pyodbc` installed, it remains but is no longer used by the agent pipeline.

---

## Step 5: Update `PYTHON_DATABASE_URL` in `.env`

Change the `PYTHON_DATABASE_URL` line in your `.env` file from:

```env
PYTHON_DATABASE_URL=mssql+pyodbc://SA:password@localhost:1433/talent_finder?driver=ODBC+Driver+17+for+SQL+Server
```

To:

```env
PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YourPostgresP4ssw0rd@localhost:5432/talent_finder
```

Replace the user, password, and port to match your `.env.docker` values.

---

## Step 6: Verify connection

**Windows (PowerShell):**

```powershell
agents\.venv\Scripts\Activate.ps1
python -c "from sqlalchemy import create_engine, text; import os; e = create_engine(os.getenv('PYTHON_DATABASE_URL')); conn = e.connect(); print(conn.execute(text('SELECT 1')).scalar()); conn.close()"
```

**Linux / macOS:**

```bash
source agents/.venv/bin/activate
python -c "from sqlalchemy import create_engine, text; import os; e = create_engine(os.getenv('PYTHON_DATABASE_URL')); conn = e.connect(); print(conn.execute(text('SELECT 1')).scalar()); conn.close()"
```

If this prints `1`, the connection is working.

---

## SQL Type Mapping Reference

pgloader handles these conversions automatically. This table is for reference if
you write manual SQL or SQLAlchemy models:

| MSSQL Type | PostgreSQL Type |
|------------|-----------------|
| NVARCHAR(n) | VARCHAR(n) or TEXT |
| NVARCHAR(MAX) | TEXT |
| NTEXT | TEXT |
| UNIQUEIDENTIFIER | UUID |
| BIT | BOOLEAN |
| FLOAT | DOUBLE PRECISION |
| DATETIME / DATETIME2 | TIMESTAMPTZ |
| VARBINARY | BYTEA |
| vector(1536) | vector(1536) (pgvector) |

For agent-specific columns added via SQLAlchemy migrations, use PostgreSQL types
directly (see `CLAUDE.md` Database Schema section):

| Column | Type |
|--------|------|
| source | TEXT |
| external_id | TEXT |
| ingestion_run_id | TEXT |
| ai_relevance_score | DOUBLE PRECISION |
| quality_score | DOUBLE PRECISION |
| is_spam | BOOLEAN |
| spam_score | DOUBLE PRECISION |
| overall_confidence | DOUBLE PRECISION |
| field_confidence | JSONB |

---

## What Stays on MSSQL (Phase 1)

These are **not affected** by this migration:

- The Next.js app (`DATABASE_URL` in `.env` — `sqlserver://` format)
- Prisma schema and migrations (`prisma/schema.prisma` — `provider = "sqlserver"`)
- All existing Next.js API routes
- The `scripts/start-sql-server.ps1` and related MSSQL scripts

These will migrate to PostgreSQL in a future Phase 2 effort.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `psycopg2` import error | Run `pip install psycopg2-binary>=2.9` in your activated venv |
| Connection refused on port 5432 | Ensure PostgreSQL container is running: `docker ps --filter "name=postgres-server"` |
| `FATAL: password authentication failed` | Verify `POSTGRES_PASSWORD` in `.env.docker` matches the password in `PYTHON_DATABASE_URL` |
| pgvector extension not found | Check init script ran: `docker exec -it postgres-server psql -U postgres -d talent_finder -c "\dx"` |
| Port conflict (5432 in use) | Change `POSTGRES_PORT` in `.env.docker` to another port (e.g., `15432`) and update `PYTHON_DATABASE_URL` to match |
| pgloader `--network host` fails on macOS/Windows | Replace `localhost` with `host.docker.internal` in the pgloader config connection strings |
| pgloader reports type conversion errors | Check for custom SQL Server types (e.g., `vector`). The pgvector extension must be enabled before migration (the `BEFORE LOAD DO` clause in the config handles this) |
| Tables missing after pgloader | Verify MSSQL container has seeded data. Run `npm run db:seed:anonymized` first if needed |
