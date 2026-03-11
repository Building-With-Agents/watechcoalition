# Runbook: Azure PostgreSQL Flexible Server for Job Intelligence Engine

This runbook provisions an Azure resource group and an Azure Database for PostgreSQL Flexible Server for the Job Intelligence Engine, then mirrors schema and data from your local Docker Desktop PostgreSQL. It also explains how to create and share JSON fixtures so devs working in isolation can align their databases.

**When to use:** Setting up a shared Azure PostgreSQL instance for the agent pipeline, or syncing local Docker data and fixtures to Azure.

---

## Prerequisites

- **Azure CLI** installed and logged in: `az login`; set subscription if needed: `az account set -s <subscription-id>`
- **Docker Desktop** running with the local PostgreSQL container (`postgres-server`, database `talent_finder`)
- **`.env.docker`** in repo root with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` (see [DOCKER_POSTGRESQL_SETUP.md](../DOCKER_POSTGRESQL_SETUP.md))
- **`.env`** with `PYTHON_DATABASE_URL` pointing at local Docker (for export/seed steps)
- **psql** and **pg_restore** (e.g. from PostgreSQL client tools or WSL) for restore step

---

## Variables

Set these before running commands (or substitute in the examples):

| Variable | Example | Description |
|----------|---------|-------------|
| `RESOURCE_GROUP` | `rg-job-inteligence-engine` | Azure resource group name |
| `LOCATION` | `eastus` | Azure region |
| `SERVER_NAME` | `pg-jobintel-<unique>` | Globally unique server name (lowercase, hyphens only) |
| `ADMIN_USER` | `pgadmin` | Admin login (1–63 chars, no `pg_` prefix) |
| `ADMIN_PASSWORD` | *(from secret)* | Strong password (8–128 chars, mixed case, numbers, symbols) |
| `DATABASE_NAME` | `talent_finder` | Database name (must match local) |

---

## Step 1: Create resource group

```bash
az group create --name rg-job-inteligence-engine --location eastus
```

---

## Step 2: Create PostgreSQL Flexible Server

Use a **globally unique** server name (e.g. `pg-jobintel-dev-abc12`). PostgreSQL version **16** matches the local Docker image (`pgvector/pgvector:pg16`).

```bash
az postgres flexible-server create \
  --resource-group rg-job-inteligence-engine \
  --name <SERVER_NAME> \
  --location eastus \
  --admin-user <ADMIN_USER> \
  --admin-password '<ADMIN_PASSWORD>' \
  --database-name talent_finder \
  --version 16 \
  --tier Burstable \
  --sku-name Standard_B1ms \
  --storage-size 32 \
  --public-access 0.0.0.0
```

- **Security:** `--public-access 0.0.0.0` allows any IP. For production, use a specific IP or VNet; add a firewall rule instead (Step 3).
- **Production:** Use `--tier GeneralPurpose` and a larger SKU (e.g. `Standard_D2s_v3`).

---

## Step 3: Firewall (if not using 0.0.0.0)

To allow only your client IP:

```bash
az postgres flexible-server firewall-rule create \
  --resource-group rg-job-inteligence-engine \
  --name <SERVER_NAME> \
  --rule-name AllowMyIP \
  --start-ip-address <YOUR_PUBLIC_IP> \
  --end-ip-address <YOUR_PUBLIC_IP>
```

---

## Step 4: Enable pgvector

The Skills Extraction agent and taxonomy matching require the `vector` extension.

**4a. Add extension to allowed list**

```bash
az postgres flexible-server parameter set \
  --resource-group rg-job-inteligence-engine \
  --server-name <SERVER_NAME> \
  --name azure.extensions \
  --value vector
```

**4b. Create extension in the database**

Connect to the `talent_finder` database (see connection string in Step 6) and run:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

You can use Azure Cloud Shell, `psql`, or:

```bash
az postgres flexible-server execute \
  --resource-group rg-job-inteligence-engine \
  --name <SERVER_NAME> \
  --admin-user <ADMIN_USER> \
  --admin-password '<ADMIN_PASSWORD>' \
  --database-name talent_finder \
  --querytext "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Step 5: Mirror schema and data from Docker (Option A — full mirror)

This copies the **exact** state of your local Docker PostgreSQL into Azure. If you do not need an exact copy and prefer to load shared reference data only, use the **Fixtures workflow** below (seed script) instead.

**5a. Dump from local Docker**

From the **repository root**:

```bash
# Plain SQL dump (works everywhere)
docker exec postgres-server pg_dump -U postgres -d talent_finder --no-owner --no-acl -f /tmp/talent_finder.sql
docker cp postgres-server:/tmp/talent_finder.sql ./talent_finder_dump.sql
```

Alternative (custom format, for `pg_restore`):

```bash
docker exec postgres-server pg_dump -U postgres -d talent_finder -Fc --no-owner --no-acl -f /tmp/talent_finder.dump
docker cp postgres-server:/tmp/talent_finder.dump ./talent_finder.dump
```

**5b. Restore to Azure**

Build the Azure connection string (replace placeholders):

```
postgresql://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require
```

- **Using SQL dump:**

  ```bash
  psql "postgresql://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require" -f talent_finder_dump.sql
  ```

- **Using custom dump:**

  ```bash
  pg_restore -d "postgresql://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require" --no-owner --no-acl talent_finder.dump
  ```

If the database already has objects, you may need to drop and recreate it first, or use `pg_restore --clean` (can drop objects before restore). Prefer restoring into an empty `talent_finder` created by the `create` command in Step 2.

**5c. Re-enable pgvector after restore**

If the dump did not include `CREATE EXTENSION vector`, run it once (see Step 4b).

---

## Step 6: Configure the app

Set `PYTHON_DATABASE_URL` in `.env` to the Azure instance (SQLAlchemy format):

```
PYTHON_DATABASE_URL=postgresql+psycopg2://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require
```

**Verify:** Run the pipeline or Streamlit dashboard:

```bash
python agents/pipeline_runner.py
# or
streamlit run agents/dashboard/streamlit_app.py
```

---

## Fixtures workflow: bring dev workflows together

Devs working in isolation can share reference data via **JSON fixtures** and load them into the shared Azure DB (or each other’s environments). This keeps schema and reference tables (skills, companies, job_postings, etc.) in sync without full pg_dump/restore.

### Creating fixtures from current data (export)

Fixtures are JSON files under `scripts/pg-seed-data/fixtures/`. To **generate or update** them from your **current** database (local Docker or any PostgreSQL):

1. Point `PYTHON_DATABASE_URL` in `.env` at the database you want to export from (e.g. local Docker).
2. Run the export script from repo root (with venv activated):

   ```bash
   python scripts/pg-seed-data/export_pg_fixtures.py
   ```

3. The script writes one JSON file per table (e.g. `skills.json`, `companies.json`, `job_postings.json`) into `scripts/pg-seed-data/fixtures/` and updates `metadata.json` with row counts. PII and agent-managed tables are skipped; see the script for the full list.
4. Commit and push the updated `scripts/pg-seed-data/fixtures/` (and optionally `schema.sql` if you changed schema) so others can use them.

**Note:** The export excludes the `embedding` column in `skills` (large pgvector data). Regenerate embeddings via the admin tool if needed.

### Loading fixtures into the Azure database

To load the **shared fixture set** into the Azure DB (or any target DB):

1. Set `PYTHON_DATABASE_URL` in `.env` to the **Azure** (or target) connection string.
2. From repo root, with venv activated:

   ```bash
   python scripts/pg-seed-data/seed_pg_database.py
   ```

3. The seed script will:
   - Apply `scripts/pg-seed-data/schema.sql` (recreates `dbo` schema and tables).
   - Truncate all fixture-loaded tables, then insert in **FK-safe order** (tiers 0–4) so referential integrity is preserved.
   - Run agent migrations (agent-managed tables and Phase 1 columns on `job_postings`).

**Important:** The seed run is **full load**: it replaces the contents of all tables that have fixture files. Use it when you want the Azure DB to match the shared fixtures (e.g. after pulling the latest fixtures from git).

### Loading into specific tables only

The standard seed loads **all** tables that have fixture files and respects foreign-key order. To update only **specific** tables in Azure:

- **Option 1 — Full seed:** Run `seed_pg_database.py` against Azure with the full fixture set. This is the recommended way to “bring workflows together” so everyone has the same reference data.
- **Option 2 — Manual / one-off:** For a single table, you can:
  - Export only that table (e.g. by modifying the export script to a single table, or by querying the DB and saving JSON), then
  - Truncate that table in Azure and insert the rows (e.g. with a small script that reads the JSON and uses `COPY` or `INSERT`), **or**
  - Run the full seed but ensure only the fixture files you care about are present in `fixtures/` (and `metadata.json` lists only those tables); the seed script loads whatever fixtures exist and skips missing ones. Tables not in the fixture set are not truncated by the seed (they are only truncated if they appear in the seed’s table list derived from the schema).

For day-to-day alignment, prefer: **export from your DB → commit fixtures → others run full seed against Azure (or their local)** so everyone shares the same reference state.

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| Connection timeout | Check firewall rule and that `--public-access` or firewall allows your IP; use `sslmode=require`. |
| `extension "vector" is not available` | Set server parameter `azure.extensions` to `vector` (Step 4a), then `CREATE EXTENSION vector` in the DB (Step 4b). |
| pg_restore errors about existing objects | Restore into an empty database, or use `--clean` with care (drops objects first). |
| Seed fails with FK violations | Ensure you ran the full schema (seed applies schema first) and that fixture files match the tier order (seed script handles order). |

---

## Cleanup

To remove the resource group and all resources (server, database, etc.):

```bash
az group delete --name rg-job-inteligence-engine --no-wait
```

---

## Summary

| Section       | Content                                                                                                                                 |
|---------------|-----------------------------------------------------------------------------------------------------------------------------------------|
| **Azure CLI** | Create `rg-job-inteligence-engine`, then Flexible Server (PG 16, `talent_finder`, Burstable, public access + firewall).                 |
| **pgvector**  | Set server parameter `azure.extensions` = `vector`; run `CREATE EXTENSION vector` in `talent_finder`.                                  |
| **Mirror**    | Option A: `pg_dump` from `postgres-server` → restore to Azure. Option B: Fixtures workflow (seed script) for schema + reference data. |
| **App**       | Set `PYTHON_DATABASE_URL` to Azure connection string; verify with pipeline or dashboard.                                              |

---

## See also

- [DOCKER_POSTGRESQL_SETUP.md](../DOCKER_POSTGRESQL_SETUP.md) — Local PostgreSQL with Docker
- [scripts/pg-seed-data/README.md](../../scripts/pg-seed-data/README.md) — Seed script and fixture layout
- [CLAUDE.md](../../CLAUDE.md) — Agent pipeline architecture and `PYTHON_DATABASE_URL`
