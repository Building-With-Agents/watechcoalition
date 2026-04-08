# PostgreSQL Seed Data

Seed a fresh PostgreSQL container with reference data for the watechcoalition platform.

> **MSSQL is deprecated.** PostgreSQL is the primary database for all development.
> You do **not** need MSSQL installed or running.

## Quick Start (Junior Devs)

```bash
# 1. Start PostgreSQL container
docker compose --env-file .env.docker up postgres -d

# 2. Activate Python venv
agents\.venv\Scripts\Activate.ps1          # Windows PowerShell
# source agents/.venv/bin/activate         # macOS / Linux

# 3. Install dependencies (if not done yet)
pip install -r agents/requirements.txt

# 4. Seed the database
python scripts/pg-seed-data/seed_pg_database.py

# 5. Verify — run the pipeline
python agents/pipeline_runner.py
```

The seed script is **idempotent** — you can run it multiple times safely.
It truncates all tables before inserting, so you always get a clean state.

## What Gets Seeded

The seed script populates **40 reference tables** with ~56,000 rows:

| Table | Rows | Description |
|-------|------|-------------|
| `postal_geo_data` | 33,787 | WA ZIP codes with lat/long |
| `cip_to_socc_map` | 6,097 | CIP-to-SOC crosswalk |
| `skills` | 5,683 | Skill taxonomy (embeddings excluded) |
| `cip` | 2,849 | Classification of Instructional Programs |
| `_jobpostingskills` | 1,628 | Job-to-skill associations |
| `socc` | 1,024 | Standard Occupation Classification |
| `socc_2018` / `socc_2010` | 868 / 841 | SOC version variants |
| `jobroleskill` | 826 | Role-to-skill links |
| `programs` | 757 | Training programs |
| `provider_programs` | 745 | Provider-program associations |
| `jobroletraining` | 276 | Role-to-training links |
| `edu_providers` | 266 | Education providers |
| `job_postings` | 172 | Job listings |
| `pathwaytraining` | 162 | Pathway-training links |
| `company_addresses` | 149 | Company locations |
| `training` | 135 | Training records |
| `companies` | 122 | Company master data |
| `skill_subcategories` | 85 | Skill subcategory groupings |
| `jobrole` | 48 | Role definitions |
| `events` | 38 | Calendar events |
| + 20 more tables | 0–24 | Reference taxonomies & empty join tables |

### What is NOT seeded

- **PII tables** (users, jobseekers, employers, auth) — excluded for privacy
- **Agent-managed tables** (raw_ingested_jobs, normalized_jobs, job_ingestion_runs) — created empty by the seed script via `run_migrations()`
- **Skill embeddings** — the `embedding` column is excluded from fixtures (107MB of pgvector data). Regenerate via the admin tool if needed.

## How It Works

The seed script (`seed_pg_database.py`) does everything in one command:

1. **Creates schema** — runs `schema.sql` (DDL for all `dbo.*` tables, extensions, indexes)
2. **Disables FK triggers** — allows loading in any order without constraint violations
3. **Truncates all tables** — ensures idempotent re-runs
4. **Loads JSON fixtures** — inserts data in FK-safe tier order (parents before children)
5. **Re-enables FK triggers** — restores referential integrity enforcement
6. **Runs agent migrations** — creates agent-managed tables + adds Phase 1 columns to `job_postings`
7. **Verifies row counts** — compares actual counts against expected from `metadata.json`

## File Structure

```
scripts/pg-seed-data/
  README.md                     ← This file
  seed_pg_database.py           ← Seed script (junior devs run this)
  export_pg_fixtures.py         ← Export script (admin only)
  clean_schema.py               ← Schema cleaner (admin only)
  schema.sql                    ← Cleaned DDL (idempotent)
  schema_raw.sql                ← Raw pg_dump output (admin reference)
  fixtures/
    metadata.json               ← Export metadata with row counts
    skills.json                 ← 5,683 skills (no embeddings)
    companies.json              ← 122 companies
    job_postings.json           ← 172 job postings
    ... (40 fixture files)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ERROR: Set PYTHON_DATABASE_URL` | Add `PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:YourPassword@localhost:5432/talent_finder` to your `.env` file |
| `Waiting for PostgreSQL...` loops | Ensure the postgres container is running: `docker compose --env-file .env.docker up postgres -d` |
| `ERROR executing schema DDL` | The database may have conflicting objects. Try: `docker compose down -v` then start fresh |
| FK constraint violations | This should not happen (triggers are disabled during load). If it does, file a bug. |
| Count mismatches after seeding | Re-run the seed script. If mismatches persist, re-export fixtures from the admin database. |
| `Could not import agent migrations` | Ensure `agents/requirements.txt` is installed and you're in the venv. The seed still works — agent tables will be created when you first run the pipeline. |
| Embeddings are NULL in skills | Expected. Embeddings are excluded from fixtures (107MB). They are regenerated via the admin embedding tool. |

## For Admins: Re-exporting Fixtures

If the admin database changes, re-export fixtures:

```bash
# 1. Ensure PYTHON_DATABASE_URL points to the admin PostgreSQL instance
# 2. Export
python scripts/pg-seed-data/export_pg_fixtures.py

# 3. Optionally regenerate schema.sql
docker exec postgres-server pg_dump -U postgres -d talent_finder \
  --schema-only --schema=dbo --no-owner --no-privileges \
  > scripts/pg-seed-data/schema_raw.sql
python scripts/pg-seed-data/clean_schema.py

# 4. Commit updated fixtures
git add scripts/pg-seed-data/fixtures/ scripts/pg-seed-data/schema.sql
git commit -m "Update PostgreSQL seed fixtures"
```
