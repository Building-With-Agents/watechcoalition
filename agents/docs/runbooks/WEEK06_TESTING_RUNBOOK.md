# Week 06 — Enrichment Agent Testing Runbook

End-to-end testing guide for the full enrichment pipeline. Covers ingestion through enrichment (temporal, borderplex, fuzzy dedup, quality scoring, spam detection, external adapters) and cloud DB setup for demo day.

All commands assume you are at the **repo root** with the Python venv activated.

### Activate the venv first

**Windows (PowerShell):**

```powershell
cd C:\Users\garyl\repos\cfa-projects\building-with-agents-curriculum\watechcoalition
agents\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
cd ~/repos/cfa-projects/building-with-agents-curriculum/watechcoalition
source agents/.venv/bin/activate
```

---

## Table of Contents

1. [Overview](#1-overview)
2. [Environment Setup](#2-environment-setup)
3. [Clean Slate — Reset Agent Tables](#3-clean-slate--reset-agent-tables)
4. [Layer 1 — Database Connectivity](#4-layer-1--database-connectivity)
5. [Layer 2 — Ingestion (JSearch + Crawl4AI)](#5-layer-2--ingestion-jsearch--crawl4ai)
6. [Layer 3 — Normalization](#6-layer-3--normalization)
7. [Layer 4 — Skills Extraction](#7-layer-4--skills-extraction)
8. [Layer 5 — Enrichment](#8-layer-5--enrichment)
9. [Layer 6 — Full Pipeline End-to-End](#9-layer-6--full-pipeline-end-to-end)
10. [Layer 7 — Streamlit Dashboard](#10-layer-7--streamlit-dashboard)
11. [Cloud DB Demo Setup](#11-cloud-db-demo-setup)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Overview

The Week 6 pipeline runs 7 Phase 1 agents sequentially:

```
Sources (JSearch API + Crawl4AI)
    |
[Ingestion Agent]         → raw_ingested_jobs, job_ingestion_runs
    |
[Normalization Agent]     → normalized_jobs (+ normalization_quarantine)
    |
[Skills Extraction Agent] → extracted_intelligence, llm_audit_log
    |
[Enrichment Agent]        → job_postings (temporal_period, borderplex_subregion,
    |                        is_duplicate, quality_score, is_spam, spam_score)
    |                      → employer_profiles (when SOC/NAICS merged)
    |
[Analytics Agent]         → aggregate metrics
[Visualization Agent]     → dashboard output
[Orchestration Agent]     → alert bus monitoring
```

### What each agent writes

| Agent | Tables Written | Key Columns |
|-------|---------------|-------------|
| Ingestion | raw_ingested_jobs, job_ingestion_runs | source, external_id, raw_payload |
| Normalization | normalized_jobs, normalization_quarantine | title, company, description, requirements |
| Skills Extraction | extracted_intelligence, llm_audit_log | skills, tools, tasks, responsibilities, context |
| Enrichment | job_postings | temporal_period, borderplex_subregion, is_duplicate, quality_score, is_spam |

### Reference tables (preserved across resets)

| Table | Purpose | Rows |
|-------|---------|------|
| socc | SOC occupation codes | 1,024 |
| companies | Company master data | varies |
| industry_sectors | Sector lookup | varies |
| technology_areas | Tech area lookup | varies |
| skills | Skill definitions | varies |
| llm_audit_log | LLM cost audit (persists) | cumulative |

---

## 2. Environment Setup

### Required environment variables

Your `.env` at the repo root must have:

```bash
# Database — point at cloud for shared access, local for development
PYTHON_DATABASE_URL=postgresql+psycopg2://azadmin:<password>@pg-jobintel-cfa-dev.postgres.database.azure.com:5432/talent_finder?sslmode=require

# LLM — Azure OpenAI for skills extraction + enrichment
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=chat-gpt41mini

# Embeddings — for fuzzy dedup
AZURE_OPENAI_EMBEDDING_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_EMBEDDING_API_KEY=<key>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME=embeddings-te3small

# Ingestion sources
JSEARCH_API_KEY=<rapidapi-key>

# Pipeline thresholds
SPAM_FLAG_THRESHOLD=0.7
SPAM_REJECT_THRESHOLD=0.9
SKILL_CONFIDENCE_THRESHOLD=0.75
BATCH_SIZE=100
```

### Verify your environment

```bash
# Check Python + venv
python --version          # Should be 3.11+
pip list | grep sqlalchemy  # Should show sqlalchemy 2.x

# Check database connectivity
python agents/scripts/db_check.py tables
```

If `tables` returns a list of `dbo.*` tables, your database connection is working.

---

## 3. Clean Slate — Reset Agent Tables

Before running the pipeline, clear previous pipeline data to avoid duplicates and short-circuiting.

```bash
# See current row counts
python agents/scripts/db_check.py counts

# Run migrations (ensures all tables and columns exist)
python agents/scripts/db_check.py migrate

# Reset all agent pipeline tables (preserves llm_audit_log and reference data)
python agents/scripts/db_check.py reset
```

The `reset` command truncates these tables (in FK-safe order):
- `extracted_intelligence`
- `employer_profiles`
- `normalization_quarantine`
- `normalized_jobs`
- `raw_ingested_jobs`
- `job_ingestion_runs`
- `job_postings`

It preserves:
- `llm_audit_log` — cost audit data persists across all runs
- `socc`, `companies`, `industry_sectors`, `technology_areas`, `skills` — reference data

You will be prompted to type `yes` to confirm.

### Verify clean state

```bash
python agents/scripts/db_check.py counts
```

All pipeline tables should show 0 rows. `llm_audit_log` retains its previous count.

---

## 4. Layer 1 — Database Connectivity

```bash
# List all tables in dbo schema
python agents/scripts/db_check.py tables

# Verify key tables exist
python agents/scripts/db_check.py query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'dbo' AND table_name IN ('raw_ingested_jobs', 'normalized_jobs', 'extracted_intelligence', 'job_postings', 'employer_profiles', 'llm_audit_log', 'socc') ORDER BY table_name"
```

**Expected:** All 7 tables listed. If any are missing, run `python agents/scripts/db_check.py migrate`.

### Verify enrichment columns on job_postings

```bash
python agents/scripts/db_check.py query "SELECT column_name FROM information_schema.columns WHERE table_schema = 'dbo' AND table_name = 'job_postings' AND column_name IN ('temporal_period', 'borderplex_subregion', 'is_duplicate', 'soc_code', 'naics_code', 'quality_score', 'is_spam', 'dedup_embedding') ORDER BY column_name"
```

**Expected:** All 8 enrichment columns listed.

---

## 5. Layer 2 — Ingestion (JSearch + Crawl4AI)

The Ingestion Agent fetches jobs from two sources:
- **JSearch API** — RapidAPI, fetches software engineering jobs in El Paso region
- **Crawl4AI** — scrapes El Paso city government jobs portal

### Test ingestion independently

```bash
python -c "
from agents.common.env import load_repo_root_dotenv
load_repo_root_dotenv()
from agents.ingestion.agent import IngestionAgent
agent = IngestionAgent()
print(agent.health_check())
"
```

**Expected:** `{'status': 'ok', ...}` or `{'status': 'degraded', ...}` (degraded if one source is down but the other works).

### Verify JSearch API key

```bash
python -c "
import os
from agents.common.env import load_repo_root_dotenv
load_repo_root_dotenv()
key = os.getenv('JSEARCH_API_KEY', '')
print(f'Key configured: {bool(key)}')
print(f'Key length: {len(key)}')
"
```

---

## 6. Layer 3 — Normalization

The Normalization Agent reads from `raw_ingested_jobs` and writes to `normalized_jobs`. Records that fail validation go to `normalization_quarantine`.

### Verify after pipeline run

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(title) AS has_title, COUNT(company) AS has_company, COUNT(description) AS has_desc FROM dbo.normalized_jobs"
```

**Expected:** All records should have title and company. Description may be null for scraped records.

---

## 7. Layer 4 — Skills Extraction

Pass 1 extracts tools via pattern matching (zero cost). Pass 2 extracts skills via LLM (Azure OpenAI). Results go to `extracted_intelligence`. Every LLM call is logged in `llm_audit_log`.

### Verify after pipeline run

```bash
# Check extraction results
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(skills) AS has_skills, COUNT(tools) AS has_tools FROM dbo.extracted_intelligence"

# Check LLM costs
python agents/scripts/db_check.py query "SELECT COUNT(*) AS calls, SUM(prompt_tokens) AS prompt_tok, SUM(completion_tokens) AS comp_tok FROM dbo.llm_audit_log"
```

---

## 8. Layer 5 — Enrichment

The Enrichment Agent adds classification and quality scoring to `job_postings`:

| Column | Source | Status (development branch) |
|--------|--------|---------------------------|
| temporal_period | Date-based classification (4 periods) | Populated |
| borderplex_subregion | Location resolver (4 subregions) | Populated |
| is_duplicate / duplicate_cluster_id | Fuzzy dedup (cosine > 0.92) | Populated |
| quality_score | Quality scorer | Populated |
| is_spam / spam_score | Spam classifier | Populated |
| soc_code | SOC classifier | NULL (PR #149 not merged) |
| naics_code | NAICS classifier | NULL (PR #149 not merged) |

### Verify enrichment columns after pipeline run

```bash
# Temporal period distribution
python agents/scripts/db_check.py query "SELECT temporal_period, COUNT(*) FROM dbo.job_postings WHERE temporal_period IS NOT NULL GROUP BY temporal_period"

# Borderplex subregion distribution
python agents/scripts/db_check.py query "SELECT borderplex_subregion, COUNT(*) FROM dbo.job_postings WHERE borderplex_subregion IS NOT NULL GROUP BY borderplex_subregion"

# Dedup results
python agents/scripts/db_check.py query "SELECT is_duplicate, COUNT(*) FROM dbo.job_postings GROUP BY is_duplicate"

# Quality + spam scoring
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(quality_score) AS has_quality, COUNT(spam_score) AS has_spam, SUM(CASE WHEN is_spam THEN 1 ELSE 0 END) AS spam_count FROM dbo.job_postings"
```

### Key files for cross-team inspection

- Temporal classifier — `classify_temporal_period()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/temporal_period.py
- Borderplex tagger — `classify_borderplex_subregion()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/borderplex_subregion.py
- Fuzzy dedup — `run_fuzzy_dedup()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/dedup/fuzzy_dedup.py
- Enrichment agent — `EnrichmentAgent.process()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/agent.py

---

## 9. Layer 6 — Full Pipeline End-to-End

Run the complete pipeline from ingestion through enrichment:

```bash
python agents/pipeline_runner.py
```

The pipeline runner:
1. Runs health checks on all Phase 1 agents
2. Triggers ingestion with Borderplex region config (El Paso, TX/NM)
3. Chains each agent's output as the next agent's input
4. Writes a run log to `agents/data/output/pipeline_run.json`

**Estimated runtime:** 10-25 minutes depending on record count and LLM latency.

### Verify complete run

```bash
# Row counts across all tables
python agents/scripts/db_check.py counts

# Check pipeline run log
python -c "import json; data = json.load(open('agents/data/output/pipeline_run.json')); print(f'Stages: {len(data)}')"
```

**Expected:** All pipeline tables populated. Run log should show 7+ stage entries.

---

## 10. Layer 7 — Streamlit Dashboard

The dashboard reads from the same database via a read-only SQLAlchemy engine.

```bash
cd agents
streamlit run dashboard/streamlit_app.py
```

### Verify dashboard pages

- **Ingestion Overview:** records-per-day bar chart should show data
- **Normalization Quality:** conformance gauge, quarantine breakdown
- **Staleness banners:** should NOT show if data was just populated
- **Never-blank behavior:** pages should render even with partial data

### Key files

- Streamlit app: https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/dashboard/streamlit_app.py
- Read-only engine: https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/dashboard/readonly_engine.py

---

## 11. Cloud DB Demo Setup

Use this to populate the shared cloud database before demo day. Students connect to the same data without running the pipeline locally.

### Pre-requisites

- `.env` has `PYTHON_DATABASE_URL` set to the Azure Postgres URL
- JSearch API key configured (`JSEARCH_API_KEY`)
- Azure OpenAI keys configured (LLM + embeddings)
- Venv activated with all dependencies installed

### Step-by-step

```bash
# 1. Verify cloud connection
python agents/scripts/db_check.py tables

# 2. Run migrations (ensure all tables/columns exist on cloud)
python agents/scripts/db_check.py migrate

# 3. Check current state
python agents/scripts/db_check.py counts

# 4. Reset pipeline tables (clean slate — no dups, no short-circuiting)
python agents/scripts/db_check.py reset

# 5. Run full pipeline against cloud DB
python agents/pipeline_runner.py

# 6. Verify populated data
python agents/scripts/db_check.py counts
```

### Expected results after pipeline run

| Table | Expected |
|-------|----------|
| job_ingestion_runs | 1 (the run just completed) |
| raw_ingested_jobs | 10-50 (depends on JSearch + Crawl4AI results) |
| normalized_jobs | ~same as raw minus quarantined |
| normalization_quarantine | 0-5 (records that failed validation) |
| extracted_intelligence | ~same as normalized_jobs |
| job_postings | ~same as normalized (promoted records) |
| employer_profiles | 0 (SOC/NAICS not yet merged) |
| llm_audit_log | cumulative (preserved across resets) |

### Student setup for demo day

After the cloud DB is populated, students update their `.env`:

```bash
PYTHON_DATABASE_URL=postgresql+psycopg2://azadmin:<password>@pg-jobintel-cfa-dev.postgres.database.azure.com:5432/talent_finder?sslmode=require
```

Students can then:
- Run queries against cloud data using `db_check.py query "..."`
- Launch Streamlit dashboards that show real enrichment data
- Demo their modules against shared, populated data

---

## 12. Troubleshooting

### Database connection failures

```
sqlalchemy.exc.OperationalError: could not connect to server
```

- Check `PYTHON_DATABASE_URL` in `.env`
- Verify Azure Postgres firewall allows your IP
- Test with: `python agents/scripts/db_check.py tables`

### JSearch API rate limit

```
429 Too Many Requests
```

- Free tier: 500 requests/month
- Check remaining quota at https://rapidapi.com/dashboard
- Pipeline will emit `SourceFailure` event and continue with Crawl4AI only

### Crawl4AI failures

```
playwright._impl._errors.Error: Browser not installed
```

- Run: `playwright install chromium`
- On Windows: may need to run PowerShell as admin

### Migration errors

```
UndefinedTable: relation "dbo.extracted_intelligence" does not exist
```

- Run: `python agents/scripts/db_check.py migrate`
- Migrations are idempotent — safe to run multiple times

### Pipeline stops at a specific agent

- Check the console output for which agent failed
- Phase 1 agent exceptions stop the pipeline (by design)
- Common cause: missing env var or expired API key
- Check `agents/data/output/pipeline_run.json` for the last successful stage

### Enrichment columns are NULL

- `soc_code` / `naics_code`: expected NULL until PR #149 merges
- `temporal_period`: requires `date_posted` on the job posting — null if date missing
- `borderplex_subregion`: requires location data — null if location missing from source
- `is_duplicate`: will be FALSE for first run (no prior records to compare against)
