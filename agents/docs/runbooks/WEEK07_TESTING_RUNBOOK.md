# Week 07 — Analytics Agent + Langfuse Observability Testing Runbook

End-to-end testing guide for the Analytics Agent (aggregate tables, LLM summaries) and Langfuse observability (traces, datasets, annotation). Builds on Week 06 (ingestion through enrichment).

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

0. [Quick Start — Verifying Analytics + Langfuse (Seeded Data)](#0-quick-start--verifying-analytics--langfuse-seeded-data)
1. [Overview](#1-overview)
2. [Environment Setup](#2-environment-setup)
3. [Clean Slate — Resetting Data](#3-clean-slate--resetting-data)
4. [Layers 1-5 — Upstream Pipeline (Week 06)](#4-layers-1-5--upstream-pipeline-week-06)
5. [Layer 6 — Analytics Agent Outputs](#5-layer-6--analytics-agent-outputs)
6. [Layer 7 — Langfuse Trace Verification](#6-layer-7--langfuse-trace-verification)
7. [Layer 8 — Dataset Upload and Annotation](#7-layer-8--dataset-upload-and-annotation)
8. [Streamlit Dashboard](#8-streamlit-dashboard)
9. [Troubleshooting](#9-troubleshooting)

---

## 0. Quick Start — Verifying Analytics + Langfuse (Seeded Data)

**If data has already been processed and seeded into your database, you do not need to run the pipeline.** This section walks you through verifying analytics outputs and Langfuse connectivity.

### Prerequisites

1. Your `.env` has `PYTHON_DATABASE_URL` pointing to the seeded database (cloud or local)
2. Venv is activated and dependencies are installed (`pip install -r agents/requirements.txt`)
3. Database is reachable: `python agents/scripts/db_check.py tables`
4. Docker services running for Langfuse: `docker compose up -d`

### Step 1 — Confirm upstream data is present

Run the Week 06 verification first to ensure the pipeline's upstream tables are populated:

```bash
python agents/scripts/db_check.py counts
```

**Expected output (seeded data):**

| Table | Expected | Notes |
|-------|----------|-------|
| raw_ingested_jobs | 1,080 | Ingested JSearch records |
| job_ingestion_runs | 67 | Batch run tracking |
| normalized_jobs | 2 | Most consumed by processing loop |
| normalization_quarantine | 12 | Schema-violation records |
| extracted_intelligence | 2 | Skills/tasks extraction results |
| employer_profiles | 25 | Enrichment-resolved employer metadata |
| companies | 554 | 122 reference + 432 enrichment-resolved |
| naics | 2,125 | NAICS 2022 industry classification |
| job_postings | 596+ | 596 enriched + 172 reference |
| llm_audit_log | 4,700+ | LLM call tracking |

If all tables show 0, the database has not been seeded. Run the seed script (it handles both reference data and enriched pipeline data in one pass):

```bash
python scripts/pg-seed-data/seed_pg_database.py
```

### Step 2 — Verify Analytics aggregate tables

> **Note:** These tables are created by the Analytics Agent, which students build during Week 7. If your pair has not yet implemented the Analytics Agent, these tables may not exist or may be empty. That is expected at the start of Week 7.

```bash
# Skill demand aggregates
python agents/scripts/db_check.py query "SELECT skill_label, posting_count FROM dbo.skill_demand_weekly ORDER BY posting_count DESC LIMIT 10"

# Role snapshot
python agents/scripts/db_check.py query "SELECT role_title, posting_count, median_salary FROM dbo.role_snapshot_weekly ORDER BY posting_count DESC LIMIT 5"

# Insight summaries
python agents/scripts/db_check.py query "SELECT id, summary_type, is_llm_generated, created_at FROM dbo.insight_summary ORDER BY created_at DESC LIMIT 5"
```

**Pair A — automated aggregate checks (IMP-021):** After refreshing aggregates for a chosen anchor Monday (Analytics Agent steps 2–3 then 8, or your pair’s equivalent), run:

```bash
PYTHONPATH=. python agents/scripts/verify_aggregates.py --list-weeks
PYTHONPATH=. python agents/scripts/verify_aggregates.py --week <YYYY-MM-DD>   # Monday

PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week <YYYY-MM-DD>
# Optional filters:
# PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week <Monday> --only skills,tools
# PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week <Monday> --only velocity,cooccurrence
```

Worked examples and notes live in [docs/findings/week-07-skill-tool-demand-findings.md](../../../docs/findings/week-07-skill-tool-demand-findings.md).

If these queries return errors like `relation "dbo.skill_demand_weekly" does not exist`, the Analytics Agent has not been implemented yet. Proceed to Section 5 for the full list of expected tables and queries.

### Step 3 — Verify Langfuse connectivity

Open http://localhost:3000 in your browser. Sign in with `dev@localhost.dev` / `LocalDev123!`.

If the page does not load, check Docker:

```bash
docker compose ps
```

All 6 Langfuse containers (`langfuse-server`, `langfuse-worker`, `langfuse-db`, `langfuse-clickhouse`, `langfuse-minio`, `langfuse-redis`) should show status `running` or `Up`.

### Step 4 — Verify Langfuse traces exist

Navigate to **Tracing** in the Langfuse UI. If the processing loop has been run with `LANGFUSE_SECRET_KEY` configured, you should see traces. If no traces exist:

```bash
# The seeded DB is fully processed (pending: 0) — roll back 3 jobs first
python agents/scripts/reset_sample_jobs.py

# Then run with real LLM for real traces (or LLM_PROVIDER=mock if no API keys)
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 3
```

Then refresh the Tracing page.

### Step 5 — Verify Langfuse dataset

Navigate to **Datasets** in the Langfuse UI. If the ground truth has been uploaded, you should see `extraction-ground-truth-v1`. If not:

```bash
python agents/scripts/upload_langfuse_dataset.py
```

Then refresh the Datasets page and confirm the item count matches your ground truth file.

---

## 1. Overview

Week 7 adds two capabilities to the pipeline:

### Analytics Agent

The Analytics Agent reads enriched records from `job_postings` and computes cross-record aggregates: skill demand by week, role snapshots with salary distributions, sector summaries, geographic demand, skill velocity (week-over-week change), skill co-occurrence matrices, and posting lifecycle metrics. These feed the Streamlit dashboard and the "Ask the Data" query interface (Week 8).

```
[Enrichment Agent]  → job_postings (enriched records)
        |
[Analytics Agent]   → skill_demand_weekly, tool_demand_weekly,
        |              role_snapshot_weekly, sector_summary_weekly,
        |              geo_demand_weekly, skill_velocity,
        |              skill_co_occurrence, posting_freshness,
        |              insight_summary
        |
[Visualization]     → Dashboard pages (Week 7 pair implementations)
```

The Analytics Agent also generates weekly insight summaries using LLM calls. With `LLM_PROVIDER=mock`, it falls back to a deterministic template that fills in aggregate numbers without an LLM call. Both paths write to `insight_summary` with an `is_llm_generated` flag.

### Langfuse Observability

Langfuse receives traces from all LLM calls in the pipeline. Every call to `invoke_skills_llm()`, `invoke_structured_extraction_llm()`, or `complete()` is wrapped in a Langfuse generation span when a tracer is registered. Traces show full prompt input, model output, token counts, costs, and timing.

Langfuse also serves as the dataset and annotation platform. Ground truth data from `agents/eval/extraction_ground_truth.json` is uploaded as a Langfuse dataset for review, annotation, and eval run tracking.

The mock provider (`LLM_PROVIDER=mock`) enables testing both features without Azure OpenAI API keys. Mock calls produce real Langfuse traces with simulated token counts and costs.

---

## 2. Environment Setup

### Required `.env` additions for Langfuse

Add these to your `.env` at the repo root (if not already present):

```bash
# Langfuse Observability — Local Docker
LANGFUSE_SECRET_KEY=sk-lf-local-dev-secret
LANGFUSE_PUBLIC_KEY=pk-lf-local-dev-public
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_HOST=http://localhost:3000
```

If you are using Langfuse Cloud instead of local Docker, replace the keys and URL with your cloud project credentials from https://us.cloud.langfuse.com.

### Start Docker services

```bash
docker compose up -d
```

This starts all services: PostgreSQL (app database), Redis, and the 6 Langfuse containers. Wait ~30 seconds for all containers to become healthy.

### Verify Langfuse is running

```bash
docker compose ps
```

All containers should show `running` or `Up (healthy)`. Then open http://localhost:3000 and confirm the login page loads.

**Pre-provisioned account:**
- Email: `dev@localhost.dev`
- Password: `LocalDev123!`
- Organization: Computing For All
- Project: job-intelligence-engine

### LLM provider — use real Azure OpenAI for Langfuse traces

For Week 7 the goal is **real traces in Langfuse** so pairs can inspect prompt inputs, model outputs, token counts, and costs. Use the real LLM:

```bash
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=chat-gpt41mini
```

With a real provider, every skills/tasks/responsibilities/enrichment call produces a real Langfuse generation span with actual token counts and cost. `is_llm_generated` will be `TRUE` in `insight_summary`.

### Mock provider (fallback — no API keys)

If Azure OpenAI keys are unavailable, set:

```bash
LLM_PROVIDER=mock
```

The mock provider returns ground truth data from `agents/eval/extraction_ground_truth.json` via round-robin, generates realistic token counts and costs, and produces real Langfuse traces. All verification steps work with mock — but traces will show `model: mock-sonnet-v1` and `is_llm_generated: FALSE`.

> **Note on mock traces:** Mock LLM calls only fire for records that have description text. Many JSearch records have empty descriptions — these skip extraction and produce no traces. You will see `skills_extraction_no_text` warnings. This is expected. The seeded fixture data includes descriptions.

> **Note on embeddings:** Taxonomy resolution Step 4 (cosine similarity) requires `AZURE_OPENAI_EMBEDDING_*` env vars. Without embedding keys, skills resolve via Steps 1-3 (exact/normalized match) and Step 6 (raw fallback). This is expected regardless of `LLM_PROVIDER`.

### Seed NAICS reference data (required for NAICS classification)

The NAICS classifier queries the `dbo.naics` reference table. If you ran `seed_pg_database.py`, NAICS data (2,125 rows) is already seeded. Otherwise, seed it manually:

```bash
python scripts/seed_naics.py --env local
```

If neither script has been run, the NAICS classifier will gracefully degrade — jobs will have `naics_code = 'unknown'`. SOC classification and employer profiling may also fail if they share the same database session as a failed NAICS query.

### Verify database connectivity

```bash
python agents/scripts/db_check.py tables
python agents/scripts/db_check.py counts
```

---

## 3. Clean Slate — Resetting Data

### Quick pipeline re-test — 3 jobs (preferred for Week 7 verification)

The seeded database is fully processed (`pending: 0`). Use this script to roll back exactly 3 jobs so `run_processing_loop.py` has real work to process and you can see live traces in Langfuse:

```bash
# 1. Preview which jobs will be reset (no writes)
python agents/scripts/reset_sample_jobs.py --dry-run

# 2. Roll back 3 fully-processed jobs to 'pending'
#    (deletes extracted_intelligence, job_postings rows, normalized_jobs rows
#     and resets raw_ingested_jobs.processing_status -> 'pending')
python agents/scripts/reset_sample_jobs.py

# 3. Re-process those 3 jobs through the full pipeline
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 3
```

After the loop finishes, verify output:

```bash
python agents/scripts/db_check.py counts
```

Expected: `normalized_jobs` +3, `extracted_intelligence` +3, `job_postings` +3 vs before the reset.

To reset more jobs:

```bash
python agents/scripts/reset_sample_jobs.py --count 5
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 5
```

> **Tip:** After each `reset_sample_jobs.py` run you get fresh Langfuse traces for normalization → skills/tasks/responsibilities extraction → enrichment (SOC, NAICS, dedup). This is the fastest way to verify your Week 7 step produces real output without re-running batch_ingest.

---

### Re-running the enrichment pipeline (classification iteration)

To iterate on SOC/NAICS/quality classification without re-ingesting from JSearch, clear the processing output and reset raw records to pending:

```bash
# 1. Clear processing output (keeps raw_ingested_jobs intact)
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.normalized_jobs CASCADE"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.extracted_intelligence CASCADE"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.employer_profiles CASCADE"

# 2. Reset raw records to pending (all or a subset)
python agents/scripts/db_check.py query "UPDATE dbo.raw_ingested_jobs SET processing_status = 'pending'"

# 3. Re-run processing (normalize → extract → enrich)
python agents/scripts/run_processing_loop.py --batch-size 25 --delay 10

# 4. Evaluate — check classification quality
python agents/scripts/db_check.py query "SELECT count(*) as total, count(quality_score) as with_quality, count(soc_code) as with_soc, count(naics_code) as with_naics FROM dbo.job_postings"

# 5. Re-export fixtures to capture improved output
python scripts/pg-seed-data/export_agent_data.py
```

**Never delete the fixture JSON files** in `scripts/pg-seed-data/agent-fixtures/` — they are your checkpoint. To restore to the last known-good state at any time: `python scripts/pg-seed-data/seed_pg_database.py`

### Reset analytics aggregate tables

If you need to clear analytics outputs and re-run the Analytics Agent, truncate the aggregate tables. These tables are created by the Analytics Agent during Week 7 — if they do not exist yet, these commands will produce errors (expected).

```bash
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.skill_demand_weekly"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.tool_demand_weekly"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.role_snapshot_weekly"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.sector_summary_weekly"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.geo_demand_weekly"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.skill_velocity"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.skill_co_occurrence"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.posting_freshness"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.trajectory_map"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.cohort_gap_cache"
python agents/scripts/db_check.py query "TRUNCATE TABLE dbo.insight_summary"
```

### Reset Langfuse data (full wipe)

If you need to start Langfuse from scratch (clear all traces, datasets, and scores):

```bash
docker compose down
docker volume rm watechcoalition_langfuse_db_data watechcoalition_langfuse_clickhouse_data watechcoalition_langfuse_clickhouse_logs watechcoalition_langfuse_minio_data
docker compose up -d
```

This removes all Langfuse persistent storage and re-provisions the default org, project, user, and API keys on restart. Wait ~30 seconds for containers to become healthy before proceeding.

### Verify clean state

```bash
python agents/scripts/db_check.py counts
```

All analytics aggregate tables should show 0 rows (or not exist yet). Upstream pipeline tables (`raw_ingested_jobs`, `normalized_jobs`, `extracted_intelligence`, `job_postings`) should retain their data — do NOT truncate those for analytics testing.

---

## 4. Layers 1-5 — Upstream Pipeline (Week 06)

The Analytics Agent reads from `job_postings`, which is populated by the Ingestion → Normalization → Skills Extraction → Enrichment pipeline. Refer to the [Week 06 Testing Runbook](WEEK06_TESTING_RUNBOOK.md) for detailed verification of these layers.

### Quick verification

```bash
python agents/scripts/db_check.py counts
```

**Minimum data for analytics testing:**

| Table | Minimum Expected | Why |
|-------|-----------------|-----|
| job_postings | 50+ | Analytics aggregates need sufficient data for meaningful grouping |
| extracted_intelligence | 50+ | Skill/tool demand requires extraction results |
| llm_audit_log | 100+ | LLM cost and performance analytics |

If `job_postings` has fewer than 50 records, run the processing loop to populate it:

```bash
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2
```

Or seed from the prepared dataset:

```bash
python scripts/pg-seed-data/seed_pg_database.py
```

### Spot-check enrichment columns

```bash
# Confirm enrichment columns are populated (needed by analytics grouping)
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(temporal_period) AS has_temporal, COUNT(borderplex_subregion) AS has_borderplex, COUNT(quality_score) AS has_quality, COUNT(soc_code) AS has_soc, COUNT(naics_code) AS has_naics FROM dbo.job_postings"
```

**Expected (seeded data):** Of the 596 enriched job_postings: `has_quality` = 596 (100%), `has_soc` ≈ 525 (88%), `has_naics` ≈ 292 non-"unknown" (49%). `has_temporal` and `has_borderplex` depend on the Pair A temporal/borderplex classifiers. The 172 reference job_postings do not have enrichment columns.

---

## 5. Layer 6 — Analytics Agent Outputs

> **Important:** The Analytics Agent is what students build during Week 7. The tables listed below are the expected schema after implementation. If your pair has not yet created these tables, the queries will return "relation does not exist" errors. Use this section as a specification for what to verify after implementation.

### Table 1 — `skill_demand_weekly`

Top skills by posting count, aggregated weekly.

```bash
python agents/scripts/db_check.py query "SELECT skill_label, posting_count, week_start FROM dbo.skill_demand_weekly ORDER BY posting_count DESC LIMIT 15"
```

**What to check:**
- Skills like Python, SQL, JavaScript, AWS should appear near the top
- `posting_count` should be realistic (not 0 or equal to total job_postings count)
- `week_start` should correspond to actual dates in your data

### Table 2 — `tool_demand_weekly`

Top tools by posting count, aggregated weekly.

```bash
python agents/scripts/db_check.py query "SELECT tool_label, posting_count, week_start FROM dbo.tool_demand_weekly ORDER BY posting_count DESC LIMIT 15"
```

**What to check:**
- Tools like Docker, Git, Kubernetes, Jira should appear
- These come from Pass 1 tool extraction (pattern matching, zero LLM cost)

### Table 3 — `role_snapshot_weekly`

Role counts with salary distributions.

```bash
python agents/scripts/db_check.py query "SELECT role_title, posting_count, median_salary, salary_p25, salary_p75 FROM dbo.role_snapshot_weekly ORDER BY posting_count DESC LIMIT 10"
```

**What to check:**
- Role titles should be recognizable (Software Engineer, Data Analyst, etc.)
- Salary values should be realistic (not 0 or astronomically high)
- `median_salary` should fall between `salary_p25` and `salary_p75` when both are non-null

### Table 4 — `sector_summary_weekly`

Sector aggregates from `industry_sectors` classification.

```bash
python agents/scripts/db_check.py query "SELECT sector_name, posting_count, avg_quality_score FROM dbo.sector_summary_weekly ORDER BY posting_count DESC LIMIT 10"
```

**What to check:**
- Sector names should correspond to `industry_sectors` table values
- `avg_quality_score` should be between 0 and 1

### Table 5 — `geo_demand_weekly`

Geographic demand by Borderplex subregion and broader location.

```bash
python agents/scripts/db_check.py query "SELECT region, subregion, posting_count FROM dbo.geo_demand_weekly ORDER BY posting_count DESC LIMIT 10"
```

**What to check:**
- Borderplex subregions: `el_paso_metro`, `las_cruces`, `southern_nm`, `other`
- Non-Borderplex jobs may appear under broader region groupings
- Distribution should roughly match `borderplex_subregion` values in `job_postings`

### Table 6 — `skill_velocity`

Demand trend for skills (Phase 1 Pair A). Values are derived in Python from the last **five** `week_start` slices in `skill_demand_weekly` ending at the anchor Monday: a **4-week rolling mean** of weekly `posting_count`, then week-over-week **`pct_change`** on that smoothed series (not a raw single-week spike). The ORM maps Python attribute **`velocity_week`** → database column **`week`**.

```bash
python agents/scripts/db_check.py query "SELECT skill_label, week, demand_count, week_over_week_change, four_week_trend, trend_confidence, esco_uri FROM dbo.skill_velocity ORDER BY ABS(week_over_week_change) DESC NULLS LAST LIMIT 10"
```

**What to check:**
- **`week`** is the velocity anchor (Monday), same convention as `skill_demand_weekly.week_start`
- **`demand_count`** and **`esco_uri`** for that row match **`skill_demand_weekly`** for the same `skill_label` and `week_start = week` (refresh **step 2** before **step 8**)
- **`week_over_week_change`** is the stored **smoothed** WoW metric; it is always a **finite** float (non-finite values are sanitized to `0.0` in the aggregator)
- **`four_week_trend`** is the label: `accelerating` | `declining` | `stable` | `volatile` | `emerging` (classification can use raw `inf`/`-inf` before sanitization for storage)
- With thin history across weeks, many rows may show **`week_over_week_change = 0.0`** while **`four_week_trend`** is still `emerging` or `stable` — refresh **`skill_demand_weekly`** for multiple consecutive Mondays to see richer trends

### Table 7 — `skill_co_occurrence`

Skill pairs that co-appear in the same job posting.

```bash
python agents/scripts/db_check.py query "SELECT skill_a, skill_b, co_occurrence_count FROM dbo.skill_co_occurrence ORDER BY co_occurrence_count DESC LIMIT 10"
```

**What to check:**
- Common pairs like (Python, SQL), (AWS, Docker), (JavaScript, React) should appear
- `co_occurrence_count` should be less than or equal to each skill's individual count
- Pairs are stored with **`skill_a` < `skill_b`** (lexicographic) to avoid duplicates; the table keeps **at most 200 rows per `week_start`**, with a deterministic top-200 ordering (**`-co_occurrence_count`**, then pair names)

### Table 8 — `posting_freshness`

Posting lifecycle metrics — how quickly jobs turn over.

```bash
python agents/scripts/db_check.py query "SELECT freshness_bucket, posting_count, avg_days_listed FROM dbo.posting_freshness ORDER BY avg_days_listed"
```

**What to check:**
- Freshness buckets should align with `temporal_period` values (current, recent, aging, historical)
- `avg_days_listed` should increase from current → historical

### Table 9 — `trajectory_map` (Phase 2 scaffold)

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS rows FROM dbo.trajectory_map"
```

**Expected:** 0 rows. This table is a Phase 2 scaffold for career trajectory analysis. It should exist (created by migration) but remain empty in Phase 1.

### Table 10 — `cohort_gap_cache` (Phase 2 scaffold)

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS rows FROM dbo.cohort_gap_cache"
```

**Expected:** 0 rows. Phase 2 scaffold for cohort gap analysis.

### Insight summaries

The Analytics Agent generates weekly insight summaries. With mock or when LLM is unavailable, it uses a deterministic template fallback.

```bash
python agents/scripts/db_check.py query "SELECT id, summary_type, is_llm_generated, LENGTH(summary_text) AS text_length, created_at FROM dbo.insight_summary ORDER BY created_at DESC LIMIT 5"
```

**What to check:**
- `is_llm_generated` should be `TRUE` when using `LLM_PROVIDER=azure_openai` (real LLM call); `FALSE` with mock (template fallback)
- `summary_text` should not be empty — the template fills in aggregate numbers even when `is_llm_generated=FALSE`
- `summary_type` indicates which aggregate the summary covers (e.g., `weekly_skills`, `weekly_roles`)

### Aggregate row count summary

```bash
python agents/scripts/db_check.py query "SELECT 'skill_demand_weekly' AS tbl, COUNT(*) AS rows FROM dbo.skill_demand_weekly UNION ALL SELECT 'tool_demand_weekly', COUNT(*) FROM dbo.tool_demand_weekly UNION ALL SELECT 'role_snapshot_weekly', COUNT(*) FROM dbo.role_snapshot_weekly UNION ALL SELECT 'sector_summary_weekly', COUNT(*) FROM dbo.sector_summary_weekly UNION ALL SELECT 'geo_demand_weekly', COUNT(*) FROM dbo.geo_demand_weekly UNION ALL SELECT 'skill_velocity', COUNT(*) FROM dbo.skill_velocity UNION ALL SELECT 'skill_co_occurrence', COUNT(*) FROM dbo.skill_co_occurrence UNION ALL SELECT 'posting_freshness', COUNT(*) FROM dbo.posting_freshness UNION ALL SELECT 'insight_summary', COUNT(*) FROM dbo.insight_summary"
```

---

## 6. Layer 7 — Langfuse Trace Verification

### Step 1 — Reset sample jobs and run the processing loop with tracing

Ensure `.env` has:

```bash
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_DEPLOYMENT_NAME=chat-gpt41mini
LANGFUSE_SECRET_KEY=sk-lf-local-dev-secret
LANGFUSE_PUBLIC_KEY=pk-lf-local-dev-public
LANGFUSE_BASE_URL=http://localhost:3000
```

The seeded database is fully processed — reset 3 jobs first so the loop has work to do:

```bash
# Roll back 3 jobs to 'pending'
python agents/scripts/reset_sample_jobs.py

# Re-process with real LLM (generates real Langfuse traces)
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 3
```

Watch the console output for:

```
langfuse_tracer_registered agent_id=processing-loop
```

If this line does not appear, the tracer was not initialized. Check `LANGFUSE_SECRET_KEY` and that the `langfuse` Python package is installed (`pip install langfuse`).

> **If you do not have Azure OpenAI keys**, set `LLM_PROVIDER=mock` — traces will appear in Langfuse but will show `model: mock-sonnet-v1` instead of the real model name.

### Step 2 — Find traces in the UI

Open http://localhost:3000 → **Tracing**. You should see at least one trace from the run above.

**Verification checklist:**

| Item | Expected |
|------|----------|
| Trace name | Starts with `processing-loop/` |
| Trace has generations | Multiple generations visible in the timeline |
| Generation names | `processing-loop/normalization`, `processing-loop/enrichment-employer-classifier`, and (when records have descriptions) `processing-loop/skills-extraction`, `processing-loop/tasks-extraction`, `processing-loop/responsibilities-extraction` |
| Input tab (LLM generations) | Contains full prompt text (system prompt + job posting fields). Non-LLM spans (normalization) show `null`. |
| Output tab (any generation) | Contains JSON response (skills array, SOC code, etc.) |
| Metadata | Shows `agent_name`, `model: <deployment-name>` (e.g. `chat-gpt41mini`); `mock-sonnet-v1` if using mock |
| Token counts | Non-zero (real tokens with `azure_openai`; simulated with mock) |
| Cost | Non-zero (real cost with `azure_openai`; computed from simulated tokens with mock) |

### Step 3 — Inspect a skills extraction generation

Click a trace → find the `processing-loop/skills-extraction` generation → click it.

**Input tab:** Should contain the full output of `build_skills_prompt()`:
- System prompt with extraction rules and few-shot examples (from `skills_extraction_v4.py`)
- User template with filled job posting fields (title, description, requirements, responsibilities)
- "Already extracted tools" list

**Output tab:** Should contain a JSON object with a `"skills"` array. With mock provider, this is ground truth data.

**Metadata tab:** Should show:
- `agent_name: skills-extraction-agent`
- `model: <deployment-name>` (e.g. `chat-gpt41mini` with real LLM; `mock-sonnet-v1` with mock)
- `latency_seconds`

### Step 4 — Verify normalization and enrichment events

Some generations include event metadata logged via `tracer.log_event()`:

**Normalization metrics** (if normalization traced):
- `normalized_count`: number of records normalized in this batch
- `quarantined_count`: number of records sent to quarantine

**Enrichment metrics** (if enrichment traced):
- `enriched_count`: number of records enriched
- `soc_classified_count`: number of records with SOC codes assigned
- `naics_classified_count`: number of records with NAICS codes assigned

**Taxonomy resolution** (from skills extraction):
- Step distribution: how many skills were resolved at each taxonomy step (exact match, normalized match, embedding similarity, O*NET, raw)
- Coverage: percentage of extracted skills linked to the taxonomy

These metrics appear in the trace metadata or as separate event annotations depending on the agent implementation.

### Step 5 — Verify LLM audit log entries

Check that the processing run wrote to `llm_audit_log`:

```bash
# Real LLM (azure_openai)
python agents/scripts/db_check.py query "SELECT agent_name, model, provider, COUNT(*) AS calls, COALESCE(SUM(cost_usd),0) AS total_usd FROM dbo.llm_audit_log GROUP BY agent_name, model, provider ORDER BY calls DESC LIMIT 10"
```

**With `LLM_PROVIDER=azure_openai`:** Rows show your deployment name (e.g. `chat-gpt41mini`) and `provider = 'azure_openai'`. Cost reflects real token usage.

**With `LLM_PROVIDER=mock`:** Rows show `provider = 'mock'` and `model = 'mock-sonnet-v1'`. Cost is computed from simulated tokens.

---

## 7. Layer 8 — Dataset Upload and Annotation

### Step 1 — Upload ground truth

```bash
python agents/scripts/upload_langfuse_dataset.py
```

The script prints each uploaded item with its `ground_truth_id` and truncated title. At the end, it reports the total count.

**Expected:** Output shows 30 items uploaded to dataset `extraction-ground-truth-v1` (or whatever count matches your `agents/eval/extraction_ground_truth.json`).

### Step 2 — Verify in Langfuse UI

Navigate to **Datasets** → click `extraction-ground-truth-v1`.

**Verification checklist:**

| Item | Expected |
|------|----------|
| Dataset name | `extraction-ground-truth-v1` |
| Item count | Matches count from upload script output |
| Each item has `input` | Object with `title`, `company`, `description`, `requirements`, `responsibilities` |
| Each item has `expected_output` | Object with `skills` array, `tools` array, `tasks`, `responsibilities`, `context` |
| Each item has `metadata` | Object with `ground_truth_id`, `external_id`, `source` |

### Step 3 — Browse dataset items

Click any item in the dataset list. The left panel shows the **input** (job posting text fields). The right panel shows the **expected_output** (human-labeled extractions).

Spot-check one item:
- Does the `title` match a real job posting?
- Does the `skills` array contain reasonable skill labels with types and confidence scores?
- Does the `tools` array contain software/tool names?

### Step 4 — Annotation exercise

Practice editing an annotation directly in Langfuse:

1. Click a dataset item.
2. In the `expected_output` panel, find the `skills` array.
3. Modify one skill — change a confidence score, fix a label typo, or add a missing skill.
4. Save the change.

This demonstrates the quick-edit workflow: small corrections without opening the Streamlit labeler.

### Step 5 — Export back to JSON

```bash
python agents/scripts/export_langfuse_dataset.py
```

**Expected:** The script reports the number of exported records and the output path (`agents/eval/extraction_ground_truth.json`).

### Step 6 — Verify round-trip

Compare the exported JSON against the original to confirm the round-trip preserved data integrity:

```bash
python -c "
import json
with open('agents/eval/extraction_ground_truth.json') as f:
    data = json.load(f)
print(f'Records: {len(data)}')
print(f'First record title: {data[0].get(\"title\", \"?\")[:60]}')
print(f'First record skills count: {len(data[0].get(\"skills\", []))}')
"
```

If you modified a skill in Step 4, that change should appear in the exported JSON. The export overwrites the file — this is intentional. Langfuse becomes the authoritative source for annotation data once you start editing there.

---

## 8. Streamlit Dashboard

The Streamlit dashboard provides a visual interface to all pipeline data.

```bash
streamlit run agents/dashboard/app.py
```

Open http://localhost:8501 in your browser.

### Existing pages (from Week 06)

| Dashboard Page | What It Shows |
|----------------|---------------|
| **Ingestion Overview** | Dedup hit rate, error rate, records-per-day chart, recent runs table |
| **Normalization Quality** | Schema conformance gauge, salary coverage %, quarantine breakdown |
| **Pipeline Run Summary** | Per-run ingestion metrics |
| **Record Journey** | Single-record trace through every pipeline stage |
| **Batch Insights** | Aggregate charts across entire dataset |

### New pages (Week 07 pair implementations)

> **Note:** These pages depend on the Analytics Agent aggregate tables. If your pair has not yet implemented the Analytics Agent, these pages may not exist or may show empty states. This is expected during Week 7 development.

| Expected Page | Data Source | What to Verify |
|--------------|-------------|----------------|
| **Skill Demand** | `skill_demand_weekly` | Top skills chart, trend lines if multi-week data |
| **Weekly Insights** | `insight_summary` | LLM-generated or template-based summaries |

The dashboard uses a read-only SQLAlchemy connection. It should never show a blank page — stale data with a staleness banner is preferred over an empty state.

---

## 9. Troubleshooting

### Langfuse Issues

**Langfuse UI not loading (http://localhost:3000)**

```bash
# Check container status
docker compose ps

# Check langfuse-server logs for startup errors
docker compose logs langfuse --tail 50
```

Common causes:
- Containers not started: run `docker compose up -d`
- Port 3000 conflict with Next.js dev server: stop Next.js (`Ctrl+C` in its terminal) or change `LANGFUSE_PORT` in `.env` (e.g., `LANGFUSE_PORT=3001`) and restart Docker
- ClickHouse unhealthy: check `docker compose logs langfuse-clickhouse --tail 20` — may need more startup time

**Login fails with provisioned credentials**

The auto-provisioned user (`dev@localhost.dev` / `LocalDev123!`) is created on first start only. If you wiped volumes and restarted, it should be re-provisioned. If not:

```bash
# Check if the init vars are set
docker compose exec langfuse-server printenv | grep LANGFUSE_INIT
```

All `LANGFUSE_INIT_*` variables should be present. If they are and login still fails, do a full volume wipe (see Section 3) and restart.

**No traces appearing after pipeline run**

1. Check console output for `langfuse_tracer_registered`. If missing, `LANGFUSE_SECRET_KEY` is not set.
2. Verify environment:
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('SECRET_KEY set:', bool(os.getenv('LANGFUSE_SECRET_KEY'))); print('BASE_URL:', os.getenv('LANGFUSE_BASE_URL', 'NOT SET'))"
   ```
3. Check that `LANGFUSE_BASE_URL` points to `http://localhost:3000` (not `https://us.cloud.langfuse.com` if using local Docker).
4. Check the langfuse-worker container is running — it processes incoming traces:
   ```bash
   docker compose logs langfuse-worker --tail 20
   ```
5. Traces are sent asynchronously. Wait 10–15 seconds after the pipeline completes, then refresh the Tracing page.

**Dataset upload fails**

```bash
python agents/scripts/upload_langfuse_dataset.py
```

If this fails with a connection error:
- Verify `LANGFUSE_SECRET_KEY` and `LANGFUSE_BASE_URL` are set correctly
- Verify the Langfuse server is reachable: `curl http://localhost:3000/api/public/health`
- Check that the `langfuse` Python package is installed: `pip list | grep langfuse`

If it fails with an authentication error:
- The API keys must match what the server was provisioned with: `pk-lf-local-dev-public` / `sk-lf-local-dev-secret`
- If you changed these in `docker-compose.yml`, update `.env` to match

**ClickHouse errors in langfuse-worker logs**

```bash
docker compose logs langfuse-worker --tail 50
```

If you see ClickHouse connection errors, the ClickHouse container may not be healthy:

```bash
docker compose restart langfuse-clickhouse
# Wait 30 seconds
docker compose restart langfuse-worker
```

### Pipeline Issues

**`column normalized_jobs.naics_code does not exist`**

The merge that added SOC/NAICS classification also added `naics_code` and `employer_metadata` columns to the `NormalizedJob` SQLAlchemy model. If your local database predates this merge, the columns don't exist yet:

```bash
python -c "
import os; from dotenv import load_dotenv; from pathlib import Path
load_dotenv(Path('.env'))
from agents.common.data_store.database import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS naics_code TEXT'))
    conn.execute(text('ALTER TABLE dbo.normalized_jobs ADD COLUMN IF NOT EXISTS employer_metadata JSONB'))
    conn.commit()
    print('Columns added')
"
```

**`relation "dbo.naics" does not exist`**

The NAICS classifier needs the `dbo.naics` reference table. Seed it:

```bash
python scripts/seed_naics.py
```

If the script is not available, NAICS classification will return "unknown" for all jobs. SOC classification may also fail if it shares the same database session.

### Analytics Issues

**Aggregate tables do not exist**

Error: `relation "dbo.skill_demand_weekly" does not exist`

This is expected at the start of Week 7. The Analytics Agent creates these tables during implementation. Run migrations once your pair has added the table definitions to `agents/common/data_store/models.py`:

```bash
python agents/scripts/db_check.py migrate
```

**Aggregate tables exist but are empty**

The Analytics Agent requires a minimum data threshold to produce meaningful aggregates. Check the source data:

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS enriched_jobs FROM dbo.job_postings"
```

If fewer than 50 enriched records exist, the minimum data guard may prevent aggregation. Seed more data:

```bash
python scripts/pg-seed-data/seed_pg_database.py
```

Or run the processing loop to enrich more records:

```bash
python agents/scripts/run_processing_loop.py --batch-size 50 --delay 2
```

**Insight summary missing or empty**

The insight summary depends on the Analytics Agent's LLM summary generation. With `LLM_PROVIDER=mock`:

- `is_llm_generated` should be `FALSE`
- `summary_text` should contain a template-generated summary with real aggregate numbers
- If `summary_text` is empty, the template fallback may not have enough data to fill in

Check that aggregate tables have data before expecting summaries:

```bash
python agents/scripts/db_check.py query "SELECT 'skill_demand_weekly' AS tbl, COUNT(*) FROM dbo.skill_demand_weekly UNION ALL SELECT 'role_snapshot_weekly', COUNT(*) FROM dbo.role_snapshot_weekly"
```

**Skill velocity looks “flat” or mostly `week_over_week_change = 0.0`**

`skill_velocity` is **not** a simple `(this_week − last_week) / last_week` on raw counts. The aggregator uses the last **five** `week_start` values from `skill_demand_weekly`, smooths with a **4-week rolling mean**, then stores **finite** `week_over_week_change` (non-finite → `0.0`). With thin weekly history or after sanitization, many rows legitimately show **`0.0`** while **`four_week_trend`** may still read `emerging` or `stable`. Refresh **`skill_demand_weekly`** for **multiple consecutive Mondays** (steps 2–3 before step 8) before expecting large deltas.

**Co-occurrence row counts**

Pair A caps co-occurrence at **200 pairs per `week_start`** with deterministic tie-breaking. Total row count should scale with the number of weeks processed (e.g., on the order of **200 × weeks**), not millions:

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS pairs FROM dbo.skill_co_occurrence"
python agents/scripts/db_check.py query "SELECT week_start, COUNT(*) AS n FROM dbo.skill_co_occurrence GROUP BY week_start ORDER BY n DESC LIMIT 5"
```

Expected: hundreds to low thousands of pairs, not millions.

If any `week_start` shows more than 200 rows, the cap is not applied as shipped.

---

## Pair C — Canonical role clustering findings (template)

Complete after a successful clustering run on a sufficiently large sample (see `CLUSTER_MIN_TOTAL_POSTINGS`).

- **Run date / environment:** (e.g. local Postgres vs Azure)
- **Eligible posting count loaded:** 
- **Clusters formed / noise rate:** 
- **Sample cluster labels (coherence):** 
- **`EmergenceAlert` fired:** yes/no; orchestration log receipt confirmed
- **`role_snapshot_weekly` sanity:** `salary_p25`–`salary_p95` vs `median_salary` spot-check
- **Follow-ups:** (e.g. Pair B `compute_salary_percentiles` swap — issue #188)
