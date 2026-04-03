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
9. [Decoupled Processing Loop](#9-decoupled-processing-loop)
10. [Full Pipeline End-to-End](#10-full-pipeline-end-to-end)
11. [Streamlit Dashboard](#11-streamlit-dashboard)
12. [Cloud DB Demo Setup](#12-cloud-db-demo-setup)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Overview

The pipeline has two operational modes:

### Option A — Single-pass demo (`pipeline_runner.py`)

Chains all agents in one sequential run. Good for quick demos with small record counts (<50).

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

### Option B — Flywheel pattern (production, 1K+ jobs)

Decouples ingestion (API budget-constrained) from processing (LLM rate-limit-constrained) via the database as a queue. See issue #161.

```
Loop 1: Batch Ingest (batch_ingest.py)
    JSearch API  ──→  raw_ingested_jobs (processing_status='pending')
    (budget-aware, key rotation, ingestion_queries.yaml config)

         ↓  (DB as queue — runs independently)

Loop 2: Paced Processing (run_processing_loop.py)
    raw_ingested_jobs ──→ [Normalize] ──→ [Extract Skills] ──→ [Enrich]
    (polls DB, processes in batches, pauses for LLM rate limits)
```

Loop 1 can fill the queue with 500–1,500 raw records across many role categories. Loop 2 drains the queue at a pace matched to Azure OpenAI rate limits. They run independently — you can re-run Loop 1 to add more records without restarting Loop 2.

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
JSEARCH_API_KEY_2=<optional-secondary-key>     # For API key rotation in batch ingestion

# Pipeline thresholds
SPAM_FLAG_THRESHOLD=0.7
SPAM_REJECT_THRESHOLD=0.9
SKILL_CONFIDENCE_THRESHOLD=0.75
BATCH_SIZE=100

# Flywheel processing loop tuning (adjust to match your Azure OpenAI TPM)
SKILLS_EXTRACTION_CHUNK_SIZE=50
SKILLS_EXTRACTION_CHUNK_COOLDOWN=2
SKILLS_EXTRACTION_DELAY=0.1
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
- **JSearch API** — RapidAPI, fetches jobs across many role categories (AI/ML, DevOps, data science, etc.)
- **Crawl4AI** — scrapes Borderplex government jobs portals (El Paso, Las Cruces, EPCC)

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

### Batch ingestion (flywheel Loop 1)

For production-scale ingestion (500–1,500 records), use the batch ingestion script instead of `pipeline_runner.py`:

```bash
# Preview what will be ingested (no API calls)
python agents/scripts/batch_ingest.py --dry-run

# Run all queries from config (with 5s delay between queries)
python agents/scripts/batch_ingest.py --delay 5
```

The script reads query configuration from `agents/config/ingestion_queries.yaml`, which defines keyword groups (e.g., `react-frontend`, `java-enterprise`, `ml-scientist`) and how many pages to fetch per group.

**API key rotation:** Set `JSEARCH_API_KEY` and optionally `JSEARCH_API_KEY_2` in `.env`. The script rotates to the secondary key when the primary key's budget is exhausted or a 429 is received. Free tier: 200 requests/month per key.

### Verify after ingestion

```bash
python agents/scripts/db_check.py counts
```

**Expected:** `raw_ingested_jobs` should show 500–1,500 rows depending on query config and API key budget.

### Known issue: empty descriptions (#165)

Approximately 46% of JSearch results arrive with empty `job_description` fields. These records are staged but will be skipped by Skills Extraction (logged as `skills_extraction_no_text`). This is a JSearch API limitation, not a mapping bug. See [issue #165](https://github.com/Building-With-Agents/watechcoalition/issues/165) for backfill solutions.

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

Pass 1 extracts tools via pattern matching (zero cost). Pass 2 extracts tasks, responsibilities, and skills via LLM (Azure OpenAI). Results go to `extracted_intelligence`. Every LLM call is logged in `llm_audit_log`.

### Rate-limit management

Skills Extraction makes 2–3 LLM calls per job (tasks + responsibilities + skills). With large batches, Azure OpenAI rate limits become the bottleneck. Tune these env vars to match your deployment's TPM/RPM:

```bash
# Set in .env or as shell env vars before running the processing loop
SKILLS_EXTRACTION_CHUNK_SIZE=50      # Records per chunk before cooldown
SKILLS_EXTRACTION_CHUNK_COOLDOWN=2   # Seconds between chunks
SKILLS_EXTRACTION_DELAY=0.1          # Seconds between records within a chunk
```

**Check your Azure OpenAI rate limits:**

```bash
az cognitiveservices account deployment list \
  --name <your-resource-name> \
  --resource-group <your-resource-group> \
  -o table
```

For 1K+ job batches, set the `chat-gpt41mini` deployment to at least 100K TPM (capacity 100) via the Azure Portal or CLI. See the Troubleshooting section for details.

### Known issue: empty descriptions

Approximately 46% of JSearch records have empty `job_description` fields. These records skip LLM extraction entirely (logged as `skills_extraction_no_text`). Only records with description/requirements/responsibilities text are processed. See [issue #165](https://github.com/Building-With-Agents/watechcoalition/issues/165).

### Verify after pipeline run

```bash
# Check extraction results
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(skills) AS has_skills, COUNT(tools) AS has_tools FROM dbo.extracted_intelligence"

# Check extraction success vs. failure
python agents/scripts/db_check.py query "SELECT extraction_status, COUNT(*) FROM dbo.extracted_intelligence GROUP BY extraction_status"

# LLM audit — by agent (tasks / responsibilities / skills / taxonomy use distinct names)
python agents/scripts/db_check.py query "SELECT agent_name, COUNT(*) AS calls, COALESCE(SUM(cost_usd),0) AS usd, COALESCE(SUM(COALESCE(input_tokens,0)+COALESCE(output_tokens,0)),0) AS tokens FROM dbo.llm_audit_log GROUP BY agent_name ORDER BY usd DESC NULLS LAST"
```

### Cost projection (1k jobs)

Run the cost report (uses `llm_audit_log`, `extracted_intelligence.extraction_cost_usd`, and description fill rate):

```bash
python agents/scripts/llm_audit_cost_report.py --project-jobs 1000
```

It prints per-agent spend, a projection from stored `extraction_cost_usd`, and a second projection from audit totals (usually closer to real LLM spend). `orchestration_audit_log` is for orchestration decisions, not token billing — use `llm_audit_log` for model costs.

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

## 9. Decoupled Processing Loop

The processing loop (`run_processing_loop.py`) is flywheel Loop 2 — it drains the queue of pending/unextracted records through Normalization, Skills Extraction, and Enrichment.

### When to use

| Scenario | Use |
|----------|-----|
| Quick demo with <50 records | `pipeline_runner.py` (Option A) |
| Production run with 500+ records | `batch_ingest.py` then `run_processing_loop.py` (Option B) |
| Re-process after code changes | `run_processing_loop.py` only (raw records already staged) |

### Preview pending work

```bash
python agents/scripts/run_processing_loop.py --dry-run
```

This shows pending raw records, unextracted normalized records, enriched job postings, and estimated iterations/time.

### Run the processing loop

```bash
# Default: batch-size 50, 10s delay between iterations
python agents/scripts/run_processing_loop.py

# Faster (requires sufficient Azure OpenAI TPM):
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2

# Limit to 5 iterations (for testing):
python agents/scripts/run_processing_loop.py --max-iterations 5 --batch-size 25
```

**For faster throughput**, set the extraction chunk env vars before running:

```powershell
$env:SKILLS_EXTRACTION_CHUNK_SIZE="50"
$env:SKILLS_EXTRACTION_CHUNK_COOLDOWN="2"
$env:SKILLS_EXTRACTION_DELAY="0.1"
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2
```

### Monitoring progress

The loop emits structured JSON logs. Key events to watch:

| Event | Meaning |
|-------|---------|
| `iteration_start` | New iteration; shows `pending_raw` and `unextracted` counts |
| `skills_extraction_no_text` | Job skipped (empty description) |
| `tasks_extraction_complete` | LLM extracted tasks for one job |
| `responsibilities_extraction_complete` | LLM extracted responsibilities for one job |
| `iteration_complete` | Iteration done; shows `remaining_raw`, `remaining_unextracted`, `total_enriched` |
| `all_records_processed` | Queue fully drained |
| `*_llm_failed` with `429` | Rate limit hit — increase Azure OpenAI TPM or slow down |

### Stop conditions

The loop exits when:
- No pending raw records AND no unextracted normalized records
- `--max-iterations` reached
- No progress (0 records normalized and 0 extracted in an iteration)

---

## 10. Full Pipeline End-to-End

### Option A — Single-pass demo (small batches)

For quick demos with <50 records:

```bash
python agents/pipeline_runner.py
```

The pipeline runner:
1. Runs health checks on all Phase 1 agents
2. Triggers ingestion with Borderplex region config (El Paso, TX/NM)
3. Chains each agent's output as the next agent's input
4. Writes a run log to `agents/data/output/pipeline_run.json`

**Estimated runtime:** 10-25 minutes for ~10-50 records.

### Option B — Flywheel (production-scale, 500+ records)

For production runs with large record counts:

```bash
# Step 1: Bulk ingest (fills the queue)
python agents/scripts/batch_ingest.py --delay 5

# Step 2: Verify raw records staged
python agents/scripts/db_check.py counts

# Step 3: Preview processing work
python agents/scripts/run_processing_loop.py --dry-run

# Step 4: Run paced processing
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2
```

**Estimated runtime:** 2-6 hours for ~1,000 records (depends on Azure OpenAI rate limits and how many records have descriptions). See [issue #166](https://github.com/Building-With-Agents/watechcoalition/issues/166) for planned parallelism improvements.

### Verify complete run

```bash
# Row counts across all tables
python agents/scripts/db_check.py counts

# Check enrichment output
python agents/scripts/db_check.py query "SELECT COUNT(*) AS enriched_jobs FROM dbo.job_postings"
```

**Expected (Option A):** 10-50 records across pipeline tables. **Expected (Option B):** 500-1,500 raw records; ~54% with descriptions processed through extraction and enrichment.

---

## 11. Streamlit Dashboard

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

## 12. Cloud DB Demo Setup

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

# 5a. Option A — Single-pass demo (small batch)
python agents/pipeline_runner.py

# 5b. Option B — Flywheel (production-scale)
python agents/scripts/batch_ingest.py --delay 5
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2

# 6. Verify populated data
python agents/scripts/db_check.py counts
```

### Expected results after pipeline run

**Option A (pipeline_runner.py):**

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

**Option B (flywheel):**

| Table | Expected |
|-------|----------|
| job_ingestion_runs | 20-50 (one per query in ingestion_queries.yaml) |
| raw_ingested_jobs | 500-1,500 (across many role categories) |
| normalized_jobs | ~same as raw |
| normalization_quarantine | 0-10 |
| extracted_intelligence | ~54% of normalized (records with descriptions) |
| job_postings | ~same as extracted_intelligence |
| employer_profiles | 0 (SOC/NAICS not yet merged) |
| llm_audit_log | cumulative; 2-3 calls per extracted record |

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

## 13. Troubleshooting

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

### Azure OpenAI 429 rate limits (Skills Extraction)

```
Error code: 429 - {'error': {'message': 'Too Many Requests'}}
```

Your Azure OpenAI deployment's TPM (tokens per minute) is too low for the extraction throughput. To check and increase:

```bash
# Check current deployments and rate limits
az cognitiveservices account deployment list \
  --name <your-resource-name> \
  --resource-group <your-resource-group> \
  -o json

# Increase gpt-4.1-mini to 100K TPM (capacity=100)
az cognitiveservices account deployment create \
  --name <your-resource-name> \
  --resource-group <your-resource-group> \
  --deployment-name chat-gpt41mini \
  --model-name gpt-4.1-mini \
  --model-version "2025-04-14" \
  --model-format OpenAI \
  --sku-capacity 100 \
  --sku-name Standard
```

Alternatively, slow down extraction by increasing cooldown env vars:

```bash
SKILLS_EXTRACTION_CHUNK_SIZE=5
SKILLS_EXTRACTION_CHUNK_COOLDOWN=30
SKILLS_EXTRACTION_DELAY=1.0
```

### Empty descriptions from JSearch

Many `skills_extraction_no_text` warnings in the processing loop output indicate JSearch returned metadata-only listings without descriptions. This affects approximately 46% of records. See [issue #165](https://github.com/Building-With-Agents/watechcoalition/issues/165). These records are skipped by Skills Extraction — this is expected behavior, not an error.

### Processing loop exits with "no_progress"

The loop exits when an iteration produces 0 normalized records AND 0 extracted records. This can happen when:

- All remaining raw records are already normalized (pending=0) and all normalized records have already been extracted (unextracted=0) — this is the normal completion path
- All remaining unextracted records have empty descriptions and were skipped — the loop sees "0 extracted" and exits. Re-run with `--dry-run` to check if unextracted records remain; if they do but all lack descriptions, this is expected

### Processing loop killed or interrupted

The processing loop can be safely interrupted (Ctrl+C) and restarted. It polls the database for pending work on each iteration, so no records are lost. Records that were mid-extraction when interrupted may need to be re-processed — the loop will pick them up on the next run since they will still show as unextracted in the database.
