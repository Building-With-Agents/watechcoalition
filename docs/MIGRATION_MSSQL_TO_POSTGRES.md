# Migrating the Agent Pipeline from MSSQL to PostgreSQL

This document covers the migration of the **Python agent pipeline** database from
MSSQL (SQL Server) to PostgreSQL. The Next.js app continues to use MSSQL via
Prisma in this phase. A future DB-unification effort will consolidate both
layers on PostgreSQL.

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

## Step 3: Migrate schema and data from MSSQL to PostgreSQL

Migration uses a two-phase approach:

1. **pgloader** creates the schema (tables, indexes, foreign keys, constraints)
2. **Python script** copies all data with proper type conversion

This two-phase approach is necessary because pgloader cannot correctly convert
MSSQL's `uniqueidentifier` type (it emits raw bytes instead of UUID strings)
or `vector` embeddings (scientific notation is incompatible with pgvector).
pgloader excels at schema creation, so we use it for that and handle data
separately.

### 3a. Edit the pgloader config

Open `scripts/pgloader/migrate-all-tables.load` and update the connection strings
to match your `.env.docker` credentials:

```
FROM mssql://SA:<your-MSSQL_SA_PASSWORD>@host.docker.internal:<MSSQL_PORT>/talent_finder
INTO postgresql://<POSTGRES_USER>:<POSTGRES_PASSWORD>@host.docker.internal:<POSTGRES_PORT>/talent_finder
```

> **Important:** Use `host.docker.internal` (not `localhost`) in the connection
> strings. pgloader runs inside a Docker container and needs to reach the host's
> mapped ports. This works on Windows, macOS, and modern Linux Docker.

### 3b. Run pgloader to create the schema

pgloader is available as a Docker image — no host installation needed.

**Windows (Git Bash):**

```bash
MSYS_NO_PATHCONV=1 docker run --rm \
  -v "${PWD}/scripts/pgloader:/pgloader" \
  dimitri/pgloader:latest \
  pgloader /pgloader/migrate-all-tables.load
```

> **Git Bash note:** The `MSYS_NO_PATHCONV=1` prefix is required to prevent
> Git Bash from mangling the `/pgloader` container path.

**Windows (PowerShell):**

```powershell
docker run --rm `
  -v "${PWD}/scripts/pgloader:/pgloader" `
  dimitri/pgloader:latest `
  pgloader /pgloader/migrate-all-tables.load
```

**Linux / macOS:**

```bash
docker run --rm \
  -v "$(pwd)/scripts/pgloader:/pgloader" \
  dimitri/pgloader:latest \
  pgloader /pgloader/migrate-all-tables.load
```

pgloader will report errors for data rows (UUIDs and embeddings) — this is
expected. The important output is that **tables and indexes were created**:

```
Create tables          0        128
Create Indexes         0        136
Primary Keys           0         62
Create Foreign Keys    ...       ...
```

### 3c. Copy data with the Python migration script

The Python script reads from MSSQL (via `pyodbc`) and writes to PostgreSQL
(via `psycopg2`), handling UUID and vector embedding conversions correctly.

> **Prerequisite:** You need both `pyodbc` and `psycopg2-binary` installed.
> If you haven't done Step 4 yet, run `pip install psycopg2-binary pyodbc`
> in your activated venv first.

**Windows (Git Bash or PowerShell):**

```bash
agents/.venv/Scripts/python.exe scripts/migrate_all_data.py
```

**Linux / macOS:**

```bash
source agents/.venv/bin/activate
python scripts/migrate_all_data.py
```

The script:
- Disables FK constraints temporarily
- Truncates all tables (safe to re-run)
- Copies every row from MSSQL, converting UUIDs and embeddings
- Re-enables FK constraints
- Reports per-table row counts and any errors

Expected output:

```
Migration complete: 1185 total rows across 64 tables
No errors!
```

### 3d. Verify migration

```bash
# Count tables in PostgreSQL
docker exec postgres-server psql -U postgres -d talent_finder -c "\dt dbo.*"

# Spot-check key tables
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM dbo.skills;"
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM dbo.companies;"
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT count(*) FROM dbo.job_postings;"

# Verify UUID format is correct (should show standard UUID like 88FEF40B-464B-...)
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT skill_id FROM dbo.skills LIMIT 1;"

# Verify pgvector embeddings loaded correctly
docker exec postgres-server psql -U postgres -d talent_finder -c "SELECT embedding FROM dbo.skills WHERE embedding IS NOT NULL LIMIT 1;"
```

> **Note:** On Windows with Git Bash, omit the `-it` flags from `docker exec`
> commands (use `docker exec postgres-server ...` not `docker exec -it ...`)
> to avoid TTY errors.

Compare counts with MSSQL (Windows Git Bash):

```bash
MSYS_NO_PATHCONV=1 docker exec mssql-server /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P 'YOUR_SA_PASSWORD' -C -No \
  -Q "SELECT count(*) FROM skills"
```

> **MSSQL sqlcmd note:** Use the `-No` flag for optional encryption. Without
> it, login may fail on newer MSSQL images that default to mandatory encryption.

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

These will migrate to PostgreSQL in a future DB-unification effort.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `psycopg2` import error | Run `pip install psycopg2-binary>=2.9` in your activated venv |
| Connection refused on port 5432 | Ensure PostgreSQL container is running: `docker ps --filter "name=postgres-server"` |
| `FATAL: password authentication failed` | Verify `POSTGRES_PASSWORD` in `.env.docker` matches the password in `PYTHON_DATABASE_URL` |
| pgvector extension not found | Check init script ran: `docker exec postgres-server psql -U postgres -d talent_finder -c "\dx"` |
| Port conflict (5432 in use) | Change `POSTGRES_PORT` in `.env.docker` to another port (e.g., `15432`) and update `PYTHON_DATABASE_URL` to match |
| Git Bash mangles Docker paths | Prefix commands with `MSYS_NO_PATHCONV=1` (e.g., `MSYS_NO_PATHCONV=1 docker run ...`) |
| `the input device is not a TTY` | Remove `-it` flags from `docker exec` commands when running in Git Bash |
| pgloader UUID errors (`invalid input syntax for type uuid`) | Expected — pgloader cannot convert MSSQL `uniqueidentifier` correctly. Use the Python migration script (`scripts/migrate_all_data.py`) for data |
| pgloader vector/embedding errors | Expected — MSSQL stores embeddings in scientific notation which pgvector rejects. The Python script handles the format conversion |
| pgloader `text(255)` type modifier error | The pgloader config casts `nvarchar` to `varchar` (not `text`) to preserve length modifiers. If you see this error, check the CAST rules in the `.load` file |
| MSSQL sqlcmd `Login failed` | Use the `-No` flag for optional encryption: `sqlcmd -S localhost -U sa -P 'pass' -C -No -Q "..."` |
| Tables missing after migration | Verify MSSQL container has seeded data. Run `npm run db:seed:anonymized` first if needed |
| Python migration script column errors | pgloader lowercases all PostgreSQL identifiers. The migration script handles this automatically. If you see `column "createdAt" does not exist`, ensure you're using the latest version of `scripts/migrate_all_data.py` |
