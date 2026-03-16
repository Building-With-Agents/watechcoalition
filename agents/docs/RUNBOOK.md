# Pipeline Testing Runbook

Step-by-step guide for running the Week 03 Ingestion + Normalization pipeline end-to-end.
Covers Windows and Linux/macOS.

---

## 1. Prerequisites

| Requirement | Version | Check command |
|-------------|---------|---------------|
| Python | 3.11 (pinned) | `python --version` or `py -3.11 --version` (Windows) |
| Docker Desktop | Latest | `docker --version` |
| Git | Latest | `git --version` |
| PostgreSQL client (optional) | Any | `psql --version` |

**API keys needed** (set in `.env`):
- `JSEARCH_API_KEY` — RapidAPI JSearch subscription
- `AZURE_OPENAI_API_KEY` — Azure OpenAI (for later weeks; not required for Week 03)
- `LANGSMITH_API_KEY` — LangSmith tracing (optional)

---

## 2. Database Setup

### Option A — Local Docker PostgreSQL

```bash
# Start PostgreSQL + Redis from the repo root
docker compose up -d

# Verify
docker exec -it postgres-db psql -U postgres -d talent_finder -c "SELECT 1"
```

### Option B — Azure PostgreSQL (recommended for class)

No Docker needed. Set `PYTHON_DATABASE_URL` in `.env` to the Azure connection string:

```
PYTHON_DATABASE_URL=postgresql+psycopg2://azadmin:<password>@pg-jobintel-cfa-dev.postgres.database.azure.com:5432/talent_finder?sslmode=require
```

Replace `<password>` with the actual password (shared via class channel).

**Test connectivity:**

```bash
# From the repo root with venv activated
python -c "from agents.common.data_store.database import check_db_connection; print('OK' if check_db_connection() else 'FAIL')"
```

---

## 3. Virtual Environment

### Windows (PowerShell)

```powershell
py -3.11 -m venv agents/.venv
agents\.venv\Scripts\Activate.ps1
pip install -r agents/requirements.txt
```

### Linux / macOS

```bash
python3.11 -m venv agents/.venv
source agents/.venv/bin/activate
pip install -r agents/requirements.txt
```

---

## 4. Environment Variables

Copy the example and fill in your keys:

```bash
cp .env.example .env
```

**Required for Week 03:**
- `PYTHON_DATABASE_URL` — see Section 2
- `JSEARCH_API_KEY` — for live JSearch fetches

**Optional:**
- `LANGSMITH_API_KEY` + `LANGCHAIN_TRACING_V2=true` — enables LangSmith tracing
- `REDIS_URL` — only needed if testing Redis Streams event bus

---

## 5. Database Migration & Seeding

Run migrations to create agent-managed tables:

```bash
# From repo root, venv activated
python -c "
from agents.common.data_store.database import get_engine
from agents.common.data_store.migrations import run_migrations
run_migrations(get_engine())
print('Migrations complete')
"
```

**Verify tables exist:**

**Option A — Local Docker** (no extra tools needed):

```bash
docker exec postgres-server psql -U postgres -d talent_finder -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'dbo'
  ORDER BY table_name;
"
```

**Option B — Azure** (requires admin credentials):

```bash
# Using psql with Azure connection string
psql "postgresql://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require" -c "
  SELECT table_name FROM information_schema.tables
  WHERE table_schema = 'dbo'
  ORDER BY table_name;
"
```

> **Note:** Azure CLI (`az postgres flexible-server execute`) is admin-only.
> Non-admin devs should use **psql**, **pgAdmin**, **DBeaver**, or **Azure Data Studio**
> with the connection string from `.env` (`PYTHON_DATABASE_URL`).

**Option C — Python** (works against whichever DB `.env` points to):

```bash
python -c "
from agents.common.data_store.database import get_engine
from sqlalchemy import text
with get_engine().connect() as conn:
    rows = conn.execute(text(\"\"\"
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'dbo' ORDER BY table_name
    \"\"\")).fetchall()
    for r in rows: print(r[0])
"
```

Expected tables:
- `job_ingestion_runs`
- `normalization_quarantine`
- `normalized_jobs`
- `raw_ingested_jobs`

---

## 6. Ingestion Smoke Test

Run ingestion standalone with a small limit:

```bash
python -m agents.ingestion.agent --source all --limit 5 --migrate
```

**Verify in the database:**

**Docker:**

```bash
docker exec postgres-server psql -U postgres -d talent_finder -c "
  SELECT source, external_id, title, company, processing_status
  FROM dbo.raw_ingested_jobs ORDER BY created_at DESC LIMIT 10;
"
docker exec postgres-server psql -U postgres -d talent_finder -c "
  SELECT run_id, source, status, total_fetched, staged_count, dedup_count
  FROM dbo.job_ingestion_runs ORDER BY started_at DESC LIMIT 3;
"
```

**Azure (psql with connection string):**

```bash
psql "postgresql://<ADMIN_USER>:<ADMIN_PASSWORD>@<SERVER_NAME>.postgres.database.azure.com:5432/talent_finder?sslmode=require" -c "
  SELECT source, external_id, title, company, processing_status
  FROM dbo.raw_ingested_jobs ORDER BY created_at DESC LIMIT 10;
"
```

**Python (works against whichever DB `.env` points to):**

```bash
python -c "
from agents.common.data_store.database import get_engine
from sqlalchemy import text
with get_engine().connect() as conn:
    rows = conn.execute(text('SELECT source, external_id, title, company, processing_status FROM dbo.raw_ingested_jobs ORDER BY created_at DESC LIMIT 10')).fetchall()
    for r in rows: print(r)
"
```

**Expected:** `status = 'completed'`, `staged_count > 0`, `processing_status = 'pending'` on raw rows.

---

## 7. Full Pipeline Run

Run the complete pipeline (Ingestion → Normalization → stub agents):

```bash
python agents/pipeline_runner.py
```

**Verify normalization:**

> **How to run these queries:** Use the method matching your environment:
> - **Docker:** `docker exec postgres-server psql -U postgres -d talent_finder -c "<query>"`
> - **Azure:** `psql "<PYTHON_DATABASE_URL from .env>" -c "<query>"`
> - **Python:** See the Python snippet in Section 5 above.
> - **GUI tools:** pgAdmin, DBeaver, or Azure Data Studio with your connection string.

```sql
-- Check normalized jobs
SELECT title, company, employment_type, salary_min, salary_max, mapper_used
FROM dbo.normalized_jobs
ORDER BY created_at DESC
LIMIT 10;

-- Check quarantine (should be low)
SELECT COUNT(*) AS quarantined FROM dbo.normalization_quarantine;

-- Check processing status distribution
SELECT processing_status, COUNT(*) AS cnt
FROM dbo.raw_ingested_jobs
GROUP BY processing_status;
```

**Expected:** Most raw records transition to `processing_status = 'normalized'`.

---

## 8. Dedup Verification

```sql
-- Should return 0 rows (no duplicates in raw_ingested_jobs)
SELECT external_id, COUNT(*) AS cnt
FROM dbo.raw_ingested_jobs
GROUP BY external_id
HAVING COUNT(*) > 1;
```

---

## 9. Test Suite

### Full run

```bash
# Windows
python -m pytest agents/tests/ -v --tb=short

# Linux / macOS
python -m pytest agents/tests/ -v --tb=short
```

### Per-module

```bash
# Ingestion tests only
python -m pytest agents/ingestion/tests/ -v --tb=short

# Normalization tests only
python -m pytest agents/normalization/tests/ -v --tb=short

# Pipeline runner tests
python -m pytest agents/tests/test_pipeline_runner.py -v --tb=short
```

**Expected:** 83+ passed, ~11 skipped (DB-dependent tests skip when `PYTHON_DATABASE_URL` is unset).

### Ruff lint

```bash
python -m ruff check agents/
```

**Expected:** `All checks passed!`

---

## 10. Dashboard (Streamlit)

```bash
streamlit run agents/dashboard/streamlit_app.py
```

Opens in browser at `http://localhost:8501`. Check pages:
- Ingestion Overview
- Pipeline Journey

---

## 11. Health Checks

```bash
python -c "
from agents.ingestion.agent import IngestionAgent
from agents.normalization.agent import NormalizationAgent
import json

for Agent in [IngestionAgent, NormalizationAgent]:
    a = Agent()
    h = a.health_check()
    print(f'{a.agent_id}: {json.dumps(h, indent=2)}')
"
```

**Expected keys in each response:**
- `status` — `"healthy"` or `"degraded"`
- `agent` — agent ID string
- `last_run` — `null` (no runs tracked yet)
- `metrics` — `{}`
- `db_reachable` — `true` if DB is connected

Normalization also includes:
- `mappers_registered` — `["jsearch", "crawl4ai"]`

---

## 12. Where to Check the Database

### psql via Docker

```bash
docker exec -it postgres-db psql -U postgres -d talent_finder
```

### Azure direct

```bash
psql "host=pg-jobintel-cfa-dev.postgres.database.azure.com port=5432 dbname=talent_finder user=azadmin password=<password> sslmode=require"
```

### GUI tools

- **pgAdmin** — connect with the same Azure/local credentials
- **DBeaver** — supports PostgreSQL natively
- **Azure Data Studio** — install PostgreSQL extension

### Useful queries

> Run these via Docker (`docker exec postgres-server psql -U postgres -d talent_finder -c "..."`),
> Azure (`psql` with connection string), or a GUI tool. See Section 5 for details.

```sql
-- Row counts for all agent tables
SELECT 'raw_ingested_jobs' AS tbl, COUNT(*) FROM dbo.raw_ingested_jobs
UNION ALL
SELECT 'normalized_jobs', COUNT(*) FROM dbo.normalized_jobs
UNION ALL
SELECT 'job_ingestion_runs', COUNT(*) FROM dbo.job_ingestion_runs
UNION ALL
SELECT 'normalization_quarantine', COUNT(*) FROM dbo.normalization_quarantine;

-- Latest ingestion run summary
SELECT run_id, source, status, total_fetched, staged_count, dedup_count, error_count,
       started_at, completed_at
FROM dbo.job_ingestion_runs
ORDER BY started_at DESC
LIMIT 1;

-- Normalization success rate
SELECT
    COUNT(*) FILTER (WHERE processing_status = 'normalized') AS normalized,
    COUNT(*) FILTER (WHERE processing_status = 'quarantined') AS quarantined,
    COUNT(*) FILTER (WHERE processing_status = 'pending') AS pending,
    COUNT(*) AS total
FROM dbo.raw_ingested_jobs;
```

---

## 13. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `FATAL: password authentication failed` | Wrong credentials in `.env` | Check `PYTHON_DATABASE_URL` — verify user/password |
| `could not connect to server: Connection refused` | DB not running | Start Docker (`docker compose up -d`) or verify Azure firewall |
| `UndefinedTable: relation "dbo.raw_ingested_jobs" does not exist` | Migrations not run | Run migration script from Section 5 |
| `schema "dbo" does not exist` | Old migration code | Pull latest — `migrations.py` now auto-creates `dbo` schema |
| `SSL connection is required` (Azure) | Missing `sslmode=require` | Add `?sslmode=require` to `PYTHON_DATABASE_URL` |
| `ModuleNotFoundError: No module named 'agents'` | Wrong working directory or venv | Run from repo root with venv activated |
| `Port 5432 already in use` | Another PostgreSQL instance | Stop it or change Docker port mapping |
| `JSEARCH_API_KEY not set` (tests skip) | Missing API key | Set `JSEARCH_API_KEY` in `.env`; some tests skip without it |
| `datetime.UTC` / `UP017` ruff error | Python 3.12+ alias used | Codebase uses `timezone.utc`; `UP017` is globally ignored in ruff |

---

## 14. Cleanup

### Stop services

```bash
docker compose down
```

### Truncate agent tables (keep schema)

> Run via Docker psql or Azure psql — see Section 5 for connection details.

```sql
TRUNCATE dbo.normalization_quarantine CASCADE;
TRUNCATE dbo.normalized_jobs CASCADE;
TRUNCATE dbo.raw_ingested_jobs CASCADE;
TRUNCATE dbo.job_ingestion_runs CASCADE;
```

### Full volume reset (destroys all data)

```bash
docker compose down -v
```
