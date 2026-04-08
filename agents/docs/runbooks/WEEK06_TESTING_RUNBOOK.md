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

0. [Quick Start — Verifying Pipeline Outputs (Seeded Data)](#0-quick-start--verifying-pipeline-outputs-seeded-data)
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

## 0. Quick Start — Verifying Pipeline Outputs (Seeded Data)

**If data has already been processed and seeded into your database, you do not need to run the pipeline.** This section walks you through verifying outputs at every stage and exploring the data via the Streamlit dashboard.

### Prerequisites

1. Your `.env` has `PYTHON_DATABASE_URL` pointing to the seeded database (cloud or local)
2. Venv is activated and dependencies are installed (`pip install -r agents/requirements.txt`)
3. Database is reachable: `python agents/scripts/db_check.py tables`

### Step 1 — Confirm data is present

```bash
python agents/scripts/db_check.py counts
```

**Expected output (seeded data):**

| Table | Expected |
|-------|----------|
| raw_ingested_jobs | 1,000+ |
| job_ingestion_runs | 20+ |
| normalized_jobs | 1,000+ |
| normalization_quarantine | 0–10 |
| extracted_intelligence | 500+ (records with descriptions) |
| job_postings | 500+ (enriched, promoted records) |
| llm_audit_log | 1,000+ (cumulative LLM call records) |

If all tables show 0, the database has not been seeded. Run `python scripts/pg-seed-data/seed_agent_data.py` or ask your instructor to seed it.

### Step 2 — Verify Ingestion outputs

Ingestion writes raw job data from JSearch API and Crawl4AI into `raw_ingested_jobs` and tracks each run in `job_ingestion_runs`.

```bash
# How many raw records per source?
python agents/scripts/db_check.py query "SELECT source, COUNT(*) AS records FROM dbo.raw_ingested_jobs GROUP BY source ORDER BY records DESC"

# How many ingestion runs completed successfully?
python agents/scripts/db_check.py query "SELECT status, COUNT(*) FROM dbo.job_ingestion_runs GROUP BY status"

# What does a raw record look like? (sample 1 row)
python agents/scripts/db_check.py query "SELECT id, source, external_id, title, company, city, state, date_posted, processing_status FROM dbo.raw_ingested_jobs LIMIT 1"
```

**What to check:**
- `source` should show `jsearch` (and optionally `crawl4ai`)
- `processing_status` should be `normalized` for records that flowed through the pipeline
- Each record has `source`, `external_id`, `title`, `company` — these are the provenance tags

### Step 3 — Verify Normalization outputs

Normalization maps source-specific fields into a canonical schema and writes to `normalized_jobs`. Records that fail validation go to `normalization_quarantine`.

```bash
# Total normalized records and field coverage
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(title) AS has_title, COUNT(company) AS has_company, COUNT(description) AS has_description, COUNT(city) AS has_city, COUNT(state_province) AS has_state FROM dbo.normalized_jobs"

# Quarantine rate (should be < 1%)
python agents/scripts/db_check.py query "SELECT COUNT(*) AS quarantined FROM dbo.normalization_quarantine"

# If there are quarantined records, see why:
python agents/scripts/db_check.py query "SELECT error_type, COUNT(*) FROM dbo.normalization_quarantine GROUP BY error_type"

# Sample a normalized record to see canonical field structure
python agents/scripts/db_check.py query "SELECT id, title, company, city, state_province, employment_type, experience_level, salary_min, salary_max, date_posted FROM dbo.normalized_jobs LIMIT 1"
```

**What to check:**
- All records should have `title` and `company` populated
- `description` will be NULL for ~46% of JSearch records (known API limitation, see issue #165)
- Dates are standardized to ISO 8601
- Salary fields are split into `salary_min`/`salary_max`/`salary_currency`/`salary_period`
- Quarantine rate should be < 1% of total raw records

### Step 4 — Verify Skills Extraction outputs

Skills Extraction uses LLM calls to extract skills, tools, tasks, and responsibilities from job descriptions. Results go to `extracted_intelligence`. Every LLM call is logged in `llm_audit_log`.

```bash
# Extraction success vs failure breakdown
python agents/scripts/db_check.py query "SELECT extraction_status, COUNT(*) FROM dbo.extracted_intelligence GROUP BY extraction_status"

# How many records have extracted skills, tools, tasks?
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(skills) AS has_skills, COUNT(tools) AS has_tools, COUNT(tasks) AS has_tasks, COUNT(responsibilities) AS has_responsibilities FROM dbo.extracted_intelligence"

# Sample one extracted record to see output structure
python agents/scripts/db_check.py query "SELECT id, normalized_job_id, extraction_status, skills, tools FROM dbo.extracted_intelligence WHERE extraction_status = 'success' LIMIT 1"

# LLM cost audit — spend per agent
python agents/scripts/db_check.py query "SELECT agent_name, COUNT(*) AS calls, COALESCE(SUM(cost_usd), 0) AS total_usd, COALESCE(SUM(COALESCE(input_tokens,0) + COALESCE(output_tokens,0)), 0) AS total_tokens FROM dbo.llm_audit_log GROUP BY agent_name ORDER BY total_usd DESC NULLS LAST"
```

**What to check:**
- `extraction_status` should show mostly `success`; `failed` records are those with empty descriptions (expected)
- `skills` and `tools` columns contain JSON arrays of extracted items
- `llm_audit_log` shows per-agent LLM spend — useful for cost projection
- Records with `extraction_status = 'failed'` and `error_reason` containing "no text" are expected — these are JSearch records without descriptions

### Step 5 — Verify Enrichment outputs

Enrichment adds classification, quality scoring, spam detection, and dedup results to `job_postings`. This is the final promoted table.

```bash
# Total enriched records
python agents/scripts/db_check.py query "SELECT COUNT(*) AS enriched_jobs FROM dbo.job_postings"

# Temporal period distribution (4 periods: current, recent, aging, historical)
python agents/scripts/db_check.py query "SELECT temporal_period, COUNT(*) FROM dbo.job_postings WHERE temporal_period IS NOT NULL GROUP BY temporal_period ORDER BY COUNT(*) DESC"

# Borderplex subregion distribution (el_paso_metro, las_cruces, southern_nm, other)
python agents/scripts/db_check.py query "SELECT borderplex_subregion, COUNT(*) FROM dbo.job_postings WHERE borderplex_subregion IS NOT NULL GROUP BY borderplex_subregion ORDER BY COUNT(*) DESC"

# Duplicate detection results
python agents/scripts/db_check.py query "SELECT is_duplicate, COUNT(*) FROM dbo.job_postings GROUP BY is_duplicate"

# Quality and spam scoring summary
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(quality_score) AS has_quality, ROUND(AVG(quality_score)::numeric, 3) AS avg_quality, COUNT(spam_score) AS has_spam, ROUND(AVG(spam_score)::numeric, 3) AS avg_spam, SUM(CASE WHEN is_spam THEN 1 ELSE 0 END) AS spam_count FROM dbo.job_postings"

# Sample an enriched record to see all classification columns
python agents/scripts/db_check.py query "SELECT id, title, company_name, temporal_period, borderplex_subregion, is_duplicate, quality_score, spam_score, is_spam, soc_code FROM dbo.job_postings LIMIT 1"
```

**What to check:**
- `temporal_period` should distribute across `current`, `recent`, `aging`, `historical` based on `date_posted`
- `borderplex_subregion` classifies jobs by Borderplex region — `NULL` for non-Borderplex locations
- `is_duplicate = TRUE` flags jobs detected as near-duplicates via cosine similarity > 0.92
- `quality_score` is [0–1] — higher is better (completeness + clarity + structural coherence)
- `spam_score` is [0–1] — below 0.7 passes, 0.7–0.9 flagged for review, above 0.9 auto-rejected
- `is_spam = TRUE` records were auto-rejected (should be rare in curated data)
- `soc_code` — SOC occupation code (e.g., "15-1252"); populated by the SOC classifier via LLM
- `naics_code` — NAICS industry code (e.g., "541511"); populated by the NAICS classifier via LLM

### Step 6 — Explore via Streamlit Dashboard

The dashboard provides a visual interface to all the data verified above.

```bash
streamlit run agents/dashboard/app.py
```

Open `http://localhost:8501` in your browser and walk through all 5 pages:

| Dashboard Page | What It Shows | What to Verify |
|----------------|---------------|----------------|
| **Ingestion Overview** | Dedup hit rate, error rate, records-per-day chart, recent runs table | Dedup rate should be < 10%, error rate near 0%, runs show `completed` status |
| **Normalization Quality** | Schema conformance gauge, salary coverage %, quarantine breakdown | Conformance should be 100% (or near it), quarantine count should be very low |
| **Pipeline Run Summary** | Per-run ingestion metrics — select a run from dropdown | Shows total fetched, staged, deduplicated, errors for each ingestion run |
| **Record Journey** | Select any record and trace it through every pipeline stage | Expand each stage to see raw payload, normalization result, extraction output, enrichment scores |
| **Batch Insights** | Aggregate charts across entire dataset | Source distribution, top locations, remote vs on-site, employment types, experience levels, salary histogram, processing status |

**Key things to look for on the dashboard:**
- Sidebar shows green "Connected to PostgreSQL (read-only)" — if yellow, check your `PYTHON_DATABASE_URL`
- Batch Insights header shows total row count (should match `normalized_jobs` count from Step 3)
- Record Journey lets you drill into individual records — try expanding the Skills Extraction and Enrichment stages to see extracted skills and quality scores
- Processing Status chart on Batch Insights shows pipeline throughput — most records should be in `normalized` or later states

### Step 7 — Verify end-to-end record flow (optional deep dive)

Pick a single record and trace it through every table to confirm the full pipeline chain:

```bash
# Pick a raw record
python agents/scripts/db_check.py query "SELECT id, external_id, title, company FROM dbo.raw_ingested_jobs LIMIT 1"

# Use its id to find the normalized version
python agents/scripts/db_check.py query "SELECT id, title, company, description IS NOT NULL AS has_desc FROM dbo.normalized_jobs WHERE raw_job_id = <RAW_ID>"

# Use the normalized id to find extraction results
python agents/scripts/db_check.py query "SELECT id, extraction_status, skills, tools FROM dbo.extracted_intelligence WHERE normalized_job_id = <NORM_ID>"

# Find the promoted job_postings record (joined on source + external_id)
python agents/scripts/db_check.py query "SELECT id, title, company_name, temporal_period, borderplex_subregion, quality_score, spam_score, is_spam FROM dbo.job_postings WHERE external_id = '<EXTERNAL_ID>'"
```

Replace `<RAW_ID>`, `<NORM_ID>`, and `<EXTERNAL_ID>` with actual values from the previous queries. This traces a single job from raw ingestion through normalization, skills extraction, and enrichment — the full Phase 1 pipeline path.

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
    |                        is_duplicate, quality_score, is_spam, spam_score,
    |                        soc_code, naics_code)
    |                      → employer_profiles
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

Approximately 46% of JSearch results arrive with empty `job_description` fields. This is a JSearch API limitation, not a mapping bug. See [issue #165](https://github.com/Building-With-Agents/watechcoalition/issues/165) for backfill solutions.

**Staging status (S3):** New ingests set `dbo.raw_ingested_jobs.processing_status` to `awaiting_description` when the mapped description is empty or whitespace-only. Rows with text are `pending`. The Normalization Agent only reads `pending`, so metadata-only rows do not enter the normalize queue until a future backfill sets them to `pending`. To restore legacy behavior (all rows `pending`), set `ALLOW_EMPTY_DESCRIPTION_PENDING=1` before ingestion.

**Operator CLI — description coverage sample:**

```bash
python agents/scripts/ingest_description_sample.py --limit 50
python agents/scripts/ingest_description_sample.py --limit 50 --query "data engineer" --location "Texas"
```

Prints `Description coverage: X/Y (Z%)` plus counts of `pending` vs `awaiting_description` for that run’s `ingestion_run_id`. The script resyncs PostgreSQL SERIAL/IDENTITY sequences before ingest (fixes `duplicate key ... job_ingestion_runs_pkey` after restores). To skip that step: `--no-sync-sequences`. To run sync only: `python agents/scripts/sync_agent_sequences.py` (or `run_migrations`, which also syncs).

**SQL — description fill rate by ingestion run:**

```sql
SELECT ingestion_run_id,
       COUNT(*) AS total,
       COUNT(*) FILTER (WHERE description IS NOT NULL AND btrim(description) <> '') AS with_description,
       COUNT(*) FILTER (WHERE processing_status = 'awaiting_description') AS awaiting_description
FROM dbo.raw_ingested_jobs
GROUP BY ingestion_run_id
ORDER BY MAX(created_at) DESC
LIMIT 20;
```

**Skills Extraction:** Jobs with no description/requirements/responsibilities skip Pass 1 extractors early; structured log event `skills_extraction_no_text` is emitted at **info** (not warning).

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
| soc_code | SOC classifier (LLM) | Populated (e.g., "15-1252") |
| naics_code | NAICS classifier (LLM) | Populated (e.g., "541511") |

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

# SOC code distribution (top 10)
python agents/scripts/db_check.py query "SELECT soc_code, COUNT(*) FROM dbo.job_postings WHERE soc_code IS NOT NULL AND soc_code != 'unclassified' GROUP BY soc_code ORDER BY COUNT(*) DESC LIMIT 10"

# NAICS code distribution (top 10)
python agents/scripts/db_check.py query "SELECT naics_code, COUNT(*) FROM dbo.job_postings WHERE naics_code IS NOT NULL AND naics_code != 'unknown' GROUP BY naics_code ORDER BY COUNT(*) DESC LIMIT 10"

# Employer profiles
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total_profiles FROM dbo.employer_profiles"
```

### Key files for cross-team inspection

- Temporal classifier — `classify_temporal_period()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/temporal_period.py
- Borderplex tagger — `classify_borderplex_subregion()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/borderplex_subregion.py
- Fuzzy dedup — `run_fuzzy_dedup()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/dedup/fuzzy_dedup.py
- SOC classifier — `classify_soc()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/soc_classifier.py
- NAICS classifier — `classify_naics()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/naics_classifier.py
- Employer classifier — `build_employer_profile()`:
  https://github.com/Building-With-Agents/watechcoalition/blob/development/agents/enrichment/classifiers/employer_classifier.py
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

The dashboard reads from the same database via a read-only SQLAlchemy engine. It has five pages covering ingestion, normalization, pipeline tracing, and aggregate analytics.

### Launch the dashboard

```bash
# From repo root with venv activated
streamlit run agents/dashboard/app.py
```

The app opens at `http://localhost:8501`. The sidebar shows connection status — green "Connected to PostgreSQL (read-only)" when `PYTHON_DATABASE_URL` is set, or a yellow JSON-fallback warning otherwise.

### Data source

- **Database mode (default):** All five pages query PostgreSQL via a read-only SQLAlchemy engine. Data is cached for 300 seconds (`@st.cache_data(ttl=300)`).
- **JSON fallback:** If no database URL is configured, three pages (Pipeline Run Summary, Record Journey, Batch Insights) fall back to `agents/data/output/pipeline_run.json`. The two observability pages (Ingestion Overview, Normalization Quality) require PostgreSQL and will show a setup prompt.

### Page-by-page guide

#### Page 1 — Ingestion Overview

Shows ingestion run history and record counts per run.

**What to look for:**
- Table of ingestion runs with `run_id`, `source`, `started_at`, `status`, `total_fetched`, `staged_count`, `dedup_count`
- Runs should show `status = completed`
- `dedup_count` shows how many duplicates were discarded per run

#### Page 2 — Normalization Quality

Shows schema conformance and quarantine breakdown.

**What to look for:**
- Total normalized records vs. quarantined records
- Quarantine breakdown by `error_type` — should be < 1% of total
- If quarantine rate exceeds 3%, investigate the source data or field mappers

#### Page 3 — Pipeline Run Summary

Shows per-record completion across all pipeline stages.

**What to look for:**
- Completion table: one row per job record, columns for each agent stage (Ingestion, Normalization, Skills Extraction, Enrichment, Analytics, Visualization, Orchestration)
- Each cell shows Pass/Fail for whether the record reached that stage
- "All Stages" column shows end-to-end completion
- Top metrics: total records processed, total log entries, run timestamp, duration

#### Page 4 — Record Journey

Trace a single record through the full pipeline.

**How to use:**
1. Select a record from the dropdown (shows `[correlation_id] Title @ Company`)
2. Expand each stage to see the event payload, event ID, schema version
3. Skills Extraction stage shows extracted skills as a table
4. Enrichment stage shows quality_score, spam_score, role_classification, seniority

**What to look for:**
- Records should flow through Ingestion → Normalization → Skills Extraction → Enrichment
- Records with empty descriptions will show `extraction_status = "failed"` at Skills Extraction — this is expected for ~46% of JSearch records (see issue #165)
- Quarantined records stop at Normalization with an error detail

#### Page 5 — Batch Insights

Aggregate analytics across the full dataset using SQL GROUP BY queries.

**Charts and metrics displayed:**
- **Source Distribution** — bar chart of records by source (jsearch, crawl4ai)
- **Top Locations (State)** — top 15 states by record count
- **Top Cities** — top 15 cities by record count
- **Remote vs On-site** — distribution of remote work flags
- **Employment Type** — full-time, part-time, contract, etc.
- **Experience Level** — entry, mid, senior, etc.
- **Salary Distribution** — median min/max salary, records with salary data, 10-bucket histogram
- **Processing Status** — bar chart of `raw_ingested_jobs.processing_status` (pending, normalized, quarantined, etc.)
- **Recent Records** — 50-row sample table of the most recent records

**What to look for:**
- Header shows total row count and which table is being queried (normalized if available, raw otherwise)
- Source distribution should show both `jsearch` and `crawl4ai` if both sources were used
- Salary histogram only renders when there is enough spread in `salary_min` values
- Processing status chart shows pipeline throughput — most records should be in `normalized` or later states after a full run

### Seeded data (no pipeline run needed)

If you seeded the database using `python scripts/pg-seed-data/seed_agent_data.py`, the dashboard will display the seeded fixture data immediately. This is useful for:
- Students who want to explore the dashboard without running the pipeline
- Demo prep when API keys or LLM budget are unavailable
- Verifying dashboard functionality after code changes

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Sidebar shows "Using fixture data (JSON)" | `PYTHON_DATABASE_URL` not set or DB unreachable | Set the env var in `.env` and restart |
| Ingestion Overview / Normalization Quality show setup prompt | These pages require PostgreSQL, no JSON fallback | Configure database connection |
| Charts show "No data" | Tables are empty — pipeline hasn't run or was reset | Run the pipeline or seed data |
| Stale data after a new pipeline run | 300-second cache TTL | Wait 5 minutes or restart Streamlit |
| Dashboard crashes on startup | Missing dependency | Run `pip install -r agents/requirements.txt` |

### Key files

| File | Purpose |
|------|---------|
| `agents/dashboard/streamlit_app.py` | Main app — all 5 pages, DB + JSON modes |
| `agents/dashboard/app.py` | Entry point with sys.path bootstrap |
| `agents/dashboard/batch_insights_queries.py` | Full-table SQL aggregates for Batch Insights |
| `agents/dashboard/pages_observability.py` | Ingestion Overview + Normalization Quality pages |
| `agents/dashboard/observability_queries.py` | DB query helpers for observability pages |
| `agents/dashboard/observability_metrics.py` | Metric calculations |
| `agents/dashboard/readonly_engine.py` | Read-only PostgreSQL engine setup |

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
| employer_profiles | ~same as job_postings (one per company) |
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
| employer_profiles | ~same as job_postings (one per company) |
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

- `soc_code` / `naics_code`: populated by SOC and NAICS classifiers (requires LLM calls); NULL if job has no description text or LLM returned "unclassified"/"unknown"
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

`skills_extraction_no_text` at **info** level indicates a normalized row had no description/requirements/responsibilities text. New JSearch ingests also stage empty-description rows as `awaiting_description` (skipped by Normalization until backfill). See [issue #165](https://github.com/Building-With-Agents/watechcoalition/issues/165).

### Processing loop exits with "no_progress"

The loop exits when an iteration produces 0 normalized records AND 0 extracted records. This can happen when:

- All remaining raw records are already normalized (pending=0) and all normalized records have already been extracted (unextracted=0) — this is the normal completion path
- All remaining unextracted records have empty descriptions and were skipped — the loop sees "0 extracted" and exits. Re-run with `--dry-run` to check if unextracted records remain; if they do but all lack descriptions, this is expected

### Processing loop killed or interrupted

The processing loop can be safely interrupted (Ctrl+C) and restarted. It polls the database for pending work on each iteration, so no records are lost. Records that were mid-extraction when interrupted may need to be re-processed — the loop will pick them up on the next run since they will still show as unextracted in the database.
