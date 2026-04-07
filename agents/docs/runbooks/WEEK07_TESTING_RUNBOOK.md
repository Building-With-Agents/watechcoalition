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
3. [Clean Slate — Reset Analytics Tables](#3-clean-slate--reset-analytics-tables)
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

| Table | Expected |
|-------|----------|
| raw_ingested_jobs | 1,000+ |
| job_ingestion_runs | 20+ |
| normalized_jobs | 1,000+ |
| normalization_quarantine | 0–10 |
| extracted_intelligence | 500+ |
| job_postings | 500+ |
| llm_audit_log | 1,000+ |

If all tables show 0, the database has not been seeded. Run `python scripts/pg-seed-data/seed_agent_data.py` or refer to the Week 06 runbook.

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

If these queries return errors like `relation "dbo.skill_demand_weekly" does not exist`, the Analytics Agent has not been implemented yet. Proceed to Section 5 for the full list of expected tables and queries.

### Step 3 — Verify Langfuse connectivity

Open http://localhost:3000 in your browser. Sign in with `glarson@localhost.dev` / `LocalDev123!`.

If the page does not load, check Docker:

```bash
docker compose ps
```

All 6 Langfuse containers (`langfuse-server`, `langfuse-worker`, `langfuse-db`, `langfuse-clickhouse`, `langfuse-minio`, `langfuse-redis`) should show status `running` or `Up`.

### Step 4 — Verify Langfuse traces exist

Navigate to **Tracing** in the Langfuse UI. If the processing loop has been run with `LANGFUSE_SECRET_KEY` configured, you should see traces. If no traces exist, run:

```bash
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 5
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
- Email: `glarson@localhost.dev`
- Password: `LocalDev123!`
- Organization: Computing For All
- Project: job-intelligence-engine

### Mock provider option

For testing without Azure OpenAI API keys, set in `.env`:

```bash
LLM_PROVIDER=mock
```

The mock provider returns ground truth data from `agents/eval/extraction_ground_truth.json` via round-robin, generates realistic token counts and costs, and produces real Langfuse traces. All verification steps in this runbook work with mock.

> **Note on mock traces:** Mock LLM calls (skills, tasks, responsibilities) only fire for records that have description text. Many JSearch records have empty descriptions — these skip extraction and produce no mock LLM traces. You will see `skills_extraction_no_text` warnings in the console. This is expected. To generate rich mock traces, ensure your database has records with descriptions (the seeded data includes them).

> **Note on embeddings:** Taxonomy resolution Step 4 (cosine similarity) requires Azure OpenAI embedding API keys (`AZURE_OPENAI_EMBEDDING_*` env vars). With mock mode and no embedding keys, skills resolve via Steps 1-3 (exact/normalized match) and Step 6 (raw fallback). This is expected.

### Seed NAICS reference data (required for NAICS classification)

The NAICS classifier queries the `dbo.naics` reference table. If this table does not exist, seed it:

```bash
python scripts/seed_naics.py
```

If `scripts/seed_naics.py` is not available, the NAICS classifier will gracefully degrade — jobs will have `naics_code = NULL`. SOC classification and employer profiling may also fail if they share the same database session as a failed NAICS query.

### Verify database connectivity

```bash
python agents/scripts/db_check.py tables
python agents/scripts/db_check.py counts
```

---

## 3. Clean Slate — Reset Analytics Tables

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
python scripts/pg-seed-data/seed_agent_data.py
```

### Spot-check enrichment columns

```bash
# Confirm enrichment columns are populated (needed by analytics grouping)
python agents/scripts/db_check.py query "SELECT COUNT(*) AS total, COUNT(temporal_period) AS has_temporal, COUNT(borderplex_subregion) AS has_borderplex, COUNT(quality_score) AS has_quality, COUNT(soc_code) AS has_soc, COUNT(naics_code) AS has_naics FROM dbo.job_postings"
```

**Expected:** `has_temporal`, `has_quality`, `has_soc`, and `has_naics` should be close to `total`. `has_borderplex` will be lower (only Borderplex-region jobs have this value).

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
python agents/scripts/db_check.py query "SELECT role_title, posting_count, median_salary, p25_salary, p75_salary FROM dbo.role_snapshot_weekly ORDER BY posting_count DESC LIMIT 10"
```

**What to check:**
- Role titles should be recognizable (Software Engineer, Data Analyst, etc.)
- Salary values should be realistic (not 0 or astronomically high)
- `median_salary` should fall between `p25_salary` and `p75_salary`

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

Week-over-week demand change for skills.

```bash
python agents/scripts/db_check.py query "SELECT skill_label, current_week_count, prior_week_count, velocity_pct FROM dbo.skill_velocity ORDER BY ABS(velocity_pct) DESC LIMIT 10"
```

**What to check:**
- `velocity_pct` is the percentage change: `(current - prior) / prior * 100`
- Requires at least 2 weeks of data to be meaningful
- With seeded data from a single batch, velocity may be 0 or NULL (expected)

### Table 7 — `skill_co_occurrence`

Skill pairs that co-appear in the same job posting.

```bash
python agents/scripts/db_check.py query "SELECT skill_a, skill_b, co_occurrence_count FROM dbo.skill_co_occurrence ORDER BY co_occurrence_count DESC LIMIT 10"
```

**What to check:**
- Common pairs like (Python, SQL), (AWS, Docker), (JavaScript, React) should appear
- `co_occurrence_count` should be less than or equal to each skill's individual count
- Pairs should be unordered (skill_a < skill_b alphabetically to avoid duplicates)

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
- `is_llm_generated` should be `FALSE` when using `LLM_PROVIDER=mock` (template fallback)
- `summary_text` should not be empty — the template fills in aggregate numbers
- `summary_type` indicates which aggregate the summary covers (e.g., `weekly_skills`, `weekly_roles`)

### Aggregate row count summary

```bash
python agents/scripts/db_check.py query "SELECT 'skill_demand_weekly' AS tbl, COUNT(*) AS rows FROM dbo.skill_demand_weekly UNION ALL SELECT 'tool_demand_weekly', COUNT(*) FROM dbo.tool_demand_weekly UNION ALL SELECT 'role_snapshot_weekly', COUNT(*) FROM dbo.role_snapshot_weekly UNION ALL SELECT 'sector_summary_weekly', COUNT(*) FROM dbo.sector_summary_weekly UNION ALL SELECT 'geo_demand_weekly', COUNT(*) FROM dbo.geo_demand_weekly UNION ALL SELECT 'skill_velocity', COUNT(*) FROM dbo.skill_velocity UNION ALL SELECT 'skill_co_occurrence', COUNT(*) FROM dbo.skill_co_occurrence UNION ALL SELECT 'posting_freshness', COUNT(*) FROM dbo.posting_freshness UNION ALL SELECT 'insight_summary', COUNT(*) FROM dbo.insight_summary"
```

---

## 6. Layer 7 — Langfuse Trace Verification

### Step 1 — Run the processing loop with tracing

Ensure `.env` has:

```bash
LLM_PROVIDER=mock
LANGFUSE_SECRET_KEY=sk-lf-local-dev-secret
LANGFUSE_PUBLIC_KEY=pk-lf-local-dev-public
LANGFUSE_BASE_URL=http://localhost:3000
```

Run a small batch:

```bash
python agents/scripts/run_processing_loop.py --max-iterations 1 --batch-size 5
```

Watch the console output for:

```
langfuse_tracer_registered agent_id=processing-loop
```

If this line does not appear, the tracer was not initialized. Check `LANGFUSE_SECRET_KEY` and that the `langfuse` Python package is installed (`pip install langfuse`).

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
| Metadata | Shows `agent_name`, `model: mock-sonnet-v1` |
| Token counts | Non-zero (simulated by mock provider) |
| Cost | Non-zero (computed from simulated tokens) |

### Step 3 — Inspect a skills extraction generation

Click a trace → find the `processing-loop/skills-extraction` generation → click it.

**Input tab:** Should contain the full output of `build_skills_prompt()`:
- System prompt with extraction rules and few-shot examples (from `skills_extraction_v4.py`)
- User template with filled job posting fields (title, description, requirements, responsibilities)
- "Already extracted tools" list

**Output tab:** Should contain a JSON object with a `"skills"` array. With mock provider, this is ground truth data.

**Metadata tab:** Should show:
- `agent_name: skills-extraction-agent`
- `model: mock-sonnet-v1`
- `latency_seconds` (simulated)

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

### Step 5 — Verify mock provider trace fidelity

With `LLM_PROVIDER=mock`, confirm that traces contain realistic data:

```bash
# Check llm_audit_log for mock entries
python agents/scripts/db_check.py query "SELECT agent_name, model, provider, COUNT(*) AS calls, COALESCE(SUM(cost_usd),0) AS total_usd FROM dbo.llm_audit_log WHERE provider = 'mock' GROUP BY agent_name, model, provider ORDER BY calls DESC"
```

**Expected:** Rows with `provider = 'mock'` and `model = 'mock-sonnet-v1'`. Cost should be non-zero (computed from simulated tokens using standard pricing).

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

The auto-provisioned user (`glarson@localhost.dev` / `LocalDev123!`) is created on first start only. If you wiped volumes and restarted, it should be re-provisioned. If not:

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
python scripts/pg-seed-data/seed_agent_data.py
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

**Skill velocity shows all zeros**

`skill_velocity` computes week-over-week change. If all your data was ingested in a single week, there is no prior week to compare against, so velocity is 0 or NULL. This is expected with a single-batch seed. Re-running the pipeline after a week (or with data spanning multiple weeks) produces non-zero velocities.

**Co-occurrence matrix is very large**

With many unique skills, the co-occurrence matrix can grow quadratically. The Analytics Agent should implement a cardinality cap — only track the top N skills (e.g., top 100 by posting count) and coalesce the long tail into "Other." If the `skill_co_occurrence` table has millions of rows, the cap may not be implemented:

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS pairs FROM dbo.skill_co_occurrence"
```

Expected: hundreds to low thousands of pairs, not millions.
