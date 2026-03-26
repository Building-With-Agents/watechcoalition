# Week 04 — Workforce Intelligence Agent Testing Runbook

End-to-end testing guide for the Skills Extraction pipeline delivered across four week-04 branches. Covers every layer from database connectivity through LLM extraction, taxonomy linking, audit logging, evaluation, and dashboard verification.

All commands assume you are at the **repo root** with the Python 3.11 venv activated.

### Activate the venv first

Every time you open a new terminal, activate before running any commands:

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

Your prompt should show `(.venv)` when activated. If you see `ModuleNotFoundError` on any command below, you forgot this step.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture Map](#2-architecture-map)
3. [Environment Setup](#3-environment-setup)
4. [Layer 1 — Database](#4-layer-1--database)
5. [Layer 2 — Pass 1 Tools Extraction](#5-layer-2--pass-1-tools-extraction)
6. [Layer 3 — Pass 2 Skills Extraction (LLM)](#6-layer-3--pass-2-skills-extraction-llm)
7. [Layer 4 — Taxonomy Resolution](#7-layer-4--taxonomy-resolution)
8. [Layer 5 — Audit Logging and Cost Tracking](#8-layer-5--audit-logging-and-cost-tracking)
9. [Layer 6 — Evaluation Harness](#9-layer-6--evaluation-harness)
10. [Layer 7 — Full Pipeline](#10-layer-7--full-pipeline)
11. [Layer 8 — Streamlit Dashboard](#11-layer-8--streamlit-dashboard)
12. [Troubleshooting by Layer](#12-troubleshooting-by-layer)

---

## 1. Overview

The Workforce Intelligence Agent (Skills Extraction Agent) is the third stage in the Job Intelligence Engine pipeline:

```
Ingestion  -->  Normalization  -->  Skills Extraction  -->  Enrichment  -->  ...
                                       |
                           +---------------------+
                           | Pass 1: Tools       |  (pattern matching, zero LLM cost)
                           | Pass 2: Skills      |  (LLM via Azure OpenAI)
                           | Taxonomy linking    |  (ESCO + GenAI extension)
                           | Audit log + cost    |  (every LLM call logged)
                           +---------------------+
                                       |
                                       v
                            extracted_intelligence table
                            llm_audit_log table
```

**What Week 04 delivers across the four branches:**


| Branch                          | What it adds                                                                                                                                                          |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `guardrails-cost-observability` | `llm_adapter.py` with `complete()`, `log_extraction_event()`, cost computation, retry/back-off, Langfuse tracing, `LLMAuditLog` model                                 |
| `stubs-pipeline-integration`    | Pipeline runner extraction stubs, context/tasks/responsibilities extractors, extraction models framework                                                              |
| `taxonomy-eval-harness`         | Taxonomy resolver (ESCO + GenAI), evaluation harness, ground truth dataset, ESCO/O*NET data files                                                                     |
| `skills-tools-extraction`       | Skills Extraction Agent rewrite (work-item-loader, ExtractionStore), `llm_client.py` (Azure OpenAI), Pass 1 tools extractor, Pass 2 skills extractor, full test suite |


---

## 2. Architecture Map

### File locations

```
agents/
  common/
    llm_adapter.py               <-- Centralized LLM adapter: complete(), log_extraction_event(),
    |                               cost computation, retry, back-off, alert emission
    llm_client.py                <-- Azure OpenAI client (LangChain): invoke_skills_llm()
    |
    data_store/
      database.py                <-- Engine, session_scope(), check_db_connection()
      models.py                  <-- ORM: LLMAuditLog, ExtractedIntelligence, NormalizedJob, ...
      migrations.py              <-- DDL: CREATE TABLE IF NOT EXISTS for all agent tables
    |
    observability/
      langfuse_tracer.py         <-- Optional Langfuse distributed tracing
    |
    types/
      extraction_types.py        <-- SkillRecord, ToolRecord, SpanRecord, ExtractionMetadata
  |
  skills_extraction/
    agent.py                     <-- SkillsExtractionAgent (WorkItemLoader + ExtractionStore)
    |
    extractors/
      tools.py                   <-- Pass 1: pattern matching against tool catalog
      skills.py                  <-- Pass 2: LLM extraction + taxonomy linking
      taxonomy.py                <-- 6-step ESCO/GenAI/O*NET resolver
    |
    taxonomy/
      esco_digital_skills.json   <-- ESCO digital skills corpus
      genai_extension.json       <-- 10 predefined GenAI skills
      onet_skills.txt            <-- O*NET skill codes
      skills_en.csv              <-- Full ESCO skills (all categories)
    |
    validator.py                 <-- Post-extraction schema validation
  |
  eval/
    extraction_eval.py           <-- Evaluation harness (precision/recall)
    extraction_ground_truth.json <-- 25 hand-labeled records (target: 30-50)
    cost_projection.py           <-- Cost analysis from llm_audit_log
  |
  scripts/
    db_check.py                 <-- DB CLI: migrate, tables, counts, query, reset
    test_llm_connection.py      <-- Azure OpenAI connectivity test
```

### Database connections

```
+-------------------+       +-------------------------+
| llm_adapter.py    |------>| dbo.llm_audit_log       |  (every LLM call)
| complete()        |       +-------------------------+
+-------------------+
        |
        v
+-------------------+       +-----------------------------+
| agent.py          |<------| dbo.normalized_jobs         |  (reads work items)
| ExtractionStore   |------>| dbo.extracted_intelligence  | (writes results)
+-------------------+       +-----------------------------+
```

---

## 3. Environment Setup

### Required for ALL Week 04 testing

```bash
# PostgreSQL connection (Docker or Azure)
PYTHON_DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/talent_finder

# -- OR for Azure --
PYTHON_DATABASE_URL=postgresql+psycopg2://azadmin:<password>@pg-jobintel-cfa-dev.postgres.database.azure.com:5432/talent_finder?sslmode=require
```

### Required for Pass 2 skills extraction (LLM)

```bash
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=<deployment-name>

# Optional: override deployment for skills specifically
EXTRACTION_DEPLOYMENT_SKILLS=<deployment-name>
```

### Optional

```bash
# Cost tracking (defaults shown — override if your pricing differs)
SONNET_INPUT_COST_PER_TOKEN=0.000003
SONNET_OUTPUT_COST_PER_TOKEN=0.000015
HAIKU_INPUT_COST_PER_TOKEN=0.00000025
HAIKU_OUTPUT_COST_PER_TOKEN=0.00000125

# Redis (for full pipeline with Redis Streams)
REDIS_URL=redis://localhost:6379/0

# Tracing
LANGSMITH_API_KEY=<key>
LANGCHAIN_TRACING_V2=true

# Skills extraction cap (limits jobs processed per run — default 10)
SKILLS_EXTRACTION_MAX_JOBS=10
```

### Verify your .env is loaded

```bash
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('DB:', 'SET' if os.getenv('PYTHON_DATABASE_URL') else 'MISSING'); print('LLM:', 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'MISSING')"
```

---

## 4. Layer 1 — Database

### What it does

The database layer provides PostgreSQL storage for all agent tables. SQLAlchemy ORM models in `agents/common/data_store/models.py` define the schema; `migrations.py` creates tables idempotently.

### Key files


| File                                     | Purpose                                                                   |
| ---------------------------------------- | ------------------------------------------------------------------------- |
| `agents/common/data_store/database.py`   | Engine singleton, `session_scope()`, `check_db_connection()`              |
| `agents/common/data_store/models.py`     | ORM models: `LLMAuditLog`, `ExtractedIntelligence`, `NormalizedJob`, etc. |
| `agents/common/data_store/migrations.py` | `run_migrations(engine)` — creates all tables + Phase 1 columns           |
| `agents/scripts/db_check.py`             | CLI tool for DB operations                                                |


### Tables created by Week 04


| Table                        | Purpose                                                      | Written by                                 |
| ---------------------------- | ------------------------------------------------------------ | ------------------------------------------ |
| `dbo.extracted_intelligence` | Extraction output (skills, tools, tasks, confidence, cost)   | `SQLAlchemyExtractionStore` in agent.py    |
| `dbo.llm_audit_log`          | Every LLM call (prompt hash, tokens, cost, latency, success) | `log_extraction_event()` in llm_adapter.py |


### Test steps

**Step 1 — Verify connectivity:**

```bash
python agents/scripts/db_check.py tables
```

Expected: List of tables in `dbo` schema. If this fails, your `PYTHON_DATABASE_URL` is wrong or the database is unreachable.

**Step 2 — Run migrations:**

```bash
python agents/scripts/db_check.py migrate
```

Expected: `Migrations complete` message. Safe to run multiple times (idempotent).

**Step 3 — Verify Week 04 tables exist:**

```bash
python agents/scripts/db_check.py query "SELECT table_name FROM information_schema.tables WHERE table_schema = 'dbo' AND table_name IN ('extracted_intelligence', 'llm_audit_log') ORDER BY table_name"
```

Expected output:

```
extracted_intelligence
llm_audit_log
```

**Step 4 — Verify extracted_intelligence schema:**

```bash
python agents/scripts/db_check.py query "SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema = 'dbo' AND table_name = 'extracted_intelligence' ORDER BY ordinal_position"
```

Key columns to verify: `normalized_job_id` (integer, NOT NULL), `skills` (jsonb), `tools` (jsonb), `extraction_metadata` (jsonb, nullable).

**Step 5 — Verify llm_audit_log schema:**

```bash
python agents/scripts/db_check.py query "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'dbo' AND table_name = 'llm_audit_log' ORDER BY ordinal_position"
```

Key columns to verify: `input_tokens`, `output_tokens`, `token_count` (all three must exist), `cost_usd`, `success`.

**Step 6 — Run DB tests:**

```bash
python -m pytest agents/tests/test_database.py -v --tb=short
```

Expected: All tests pass (requires live DB connection).

### Troubleshooting


| Symptom                       | Cause              | Fix                                             |
| ----------------------------- | ------------------ | ----------------------------------------------- |
| `connection refused`          | DB not running     | `docker compose up -d` or check Azure firewall  |
| `schema "dbo" does not exist` | Old migration      | Run `python agents/scripts/db_check.py migrate` |
| `table does not exist`        | Migrations not run | Run migrations (Step 2)                         |
| `sslmode=require` error       | Azure without SSL  | Add `?sslmode=require` to `PYTHON_DATABASE_URL` |


---

## 5. Layer 2 — Pass 1 Tools Extraction

### What it does

Pattern-based extraction of tools and technologies from job posting text. **Zero LLM cost** — uses a compiled catalog of tool names, aliases, and regex patterns. Runs before Pass 2 so already-found tools can be excluded from the LLM prompt.

### Key files


| File                                           | Purpose                                                |
| ---------------------------------------------- | ------------------------------------------------------ |
| `agents/skills_extraction/extractors/tools.py` | Tool catalog, alias matching, context-aware extraction |
| `agents/common/types/extraction_types.py`      | `ToolRecord` Pydantic model                            |


### How it connects

- **Reads:** Normalized job text (from inline event payload or `dbo.normalized_jobs`)
- **Writes:** Nothing directly — results flow through the agent to `dbo.extracted_intelligence`
- **LLM cost:** None (pure pattern matching)

### Test steps

**Step 1 — Run unit tests:**

```bash
python -m pytest agents/tests/test_tools_extractor.py -v --tb=short
```

Expected: All tests pass. Tests cover canonical matches, alias resolution, ambiguous term handling (e.g., "Go" requires technical context), and deduplication.

**Step 2 — Manual extraction test:**

```python
python -c "
from agents.common.types import JobRecord
from agents.skills_extraction.extractors import extract_tools

job = JobRecord(
    raw_job_id=0, ingestion_run_id='test', region_id='', source='test',
    external_id='test-1', title='Senior Python Developer',
    company='Test Corp',
    description='We need a Python developer with experience in PostgreSQL, Docker, and React. Must know AWS and Terraform.',
)
tools = extract_tools(job)
for t in tools:
    print(f'  {t.tool_name:20s}  category={t.category:12s}  confidence={t.confidence:.2f}  field={t.source_span.field_source}')
"
```

Expected: Python, PostgreSQL, Docker, React, AWS, Terraform extracted with confidence scores and field sources.

**Step 3 — Check for false positives with ambiguous terms:**

```python
python -c "
from agents.common.types import JobRecord
from agents.skills_extraction.extractors import extract_tools

job = JobRecord(
    raw_job_id=0, ingestion_run_id='test', region_id='', source='test',
    external_id='test-2', title='Office Manager',
    company='Test Corp',
    description='Go to the office and manage Excel spreadsheets. Use Word for reports.',
)
tools = extract_tools(job)
print(f'Extracted {len(tools)} tools:')
for t in tools:
    print(f'  {t.tool_name} (confidence={t.confidence:.2f})')
"
```

Expected: "Go" should NOT be extracted (no technical context). "Excel" may be extracted if technical context is present.

### Troubleshooting


| Symptom                            | Cause                        | Fix                                         |
| ---------------------------------- | ---------------------------- | ------------------------------------------- |
| `ImportError: agents.common.types` | Wrong working directory      | Run from repo root                          |
| Tool not extracted                 | Not in catalog or alias list | Check `tools.py` `_TOOL_CATALOG`            |
| False positive on ambiguous term   | Context window too broad     | Check `_AMBIGUOUS_TERMS` and context radius |


---

## 6. Layer 3 — Pass 2 Skills Extraction (LLM)

### What it does

Sends normalized job text to Azure OpenAI (Sonnet-class model) with a structured prompt. The LLM returns a JSON array of skills with type, confidence, and source spans. Every call is logged to `dbo.llm_audit_log` with cost.

### Key files


| File                                            | Purpose                                                                        |
| ----------------------------------------------- | ------------------------------------------------------------------------------ |
| `agents/common/llm_client.py`                   | Azure OpenAI wrapper: `invoke_skills_llm(prompt)`                              |
| `agents/common/llm_adapter.py`                  | `complete()` with retry, back-off, cost, audit logging                         |
| `agents/skills_extraction/extractors/skills.py` | `extract_skills(job_record, pass1_tools)` — prompt building + response parsing |
| `agents/skills_extraction/prompts/`             | Prompt templates (versioned)                                                   |


### How it connects

- **Reads:** Normalized job text (inline or from `dbo.normalized_jobs`)
- **Writes:** `dbo.llm_audit_log` (one row per LLM call, via `log_extraction_event()`)
- **LLM cost:** ~$0.003–$0.01 per job record (Sonnet tier)

### Test steps

**Step 1 — Verify Azure OpenAI connectivity:**

```bash
python -m agents.scripts.test_llm_connection
```

Expected: Returns a model response. If this fails, your Azure OpenAI env vars are wrong.

**Step 2 — Run unit tests (mocked LLM):**

```bash
python -m pytest agents/tests/test_skills_extractor.py -v --tb=short
```

Expected: All tests pass. Tests mock `invoke_skills_llm()` — no real LLM calls or cost.

**Step 3 — Test the skills extractor with a real LLM call:**

> This makes a real API call and costs money. Skip if you just want unit tests.

The script sends this job posting to the LLM for skills extraction:

- **Title:** Machine Learning Engineer
- **Company:** AI Corp
- **Description:** Build ML pipelines using Python, TensorFlow, and PyTorch. Deploy models on AWS SageMaker. Experience with MLOps, CI/CD, and Docker required.
- **Requirements:** 5+ years Python, 3+ years deep learning frameworks

```bash
python agents/scripts/test_skills_extraction_live.py
```

Expected: Skills like "Machine Learning", "Deep Learning", "MLOps" extracted with types and confidence scores. `success=True`.

**Step 4 — Verify prompt includes Pass 1 tools context:**

```bash
python -m pytest agents/tests/test_skills_extractor.py::test_extract_skills_includes_pass1_tools_in_prompt_context -v --tb=long
```

Expected: The prompt sent to the LLM includes "Already extracted tools: Python" so the LLM avoids duplicating Pass 1 results.

### Troubleshooting


| Symptom                                                   | Cause                  | Fix                                                         |
| --------------------------------------------------------- | ---------------------- | ----------------------------------------------------------- |
| `ValueError: EXTRACTION_DEPLOYMENT_SKILLS... must be set` | Missing Azure env vars | Set `AZURE_OPENAI_DEPLOYMENT_NAME` in `.env`                |
| `AuthenticationError`                                     | Bad API key            | Check `AZURE_OPENAI_API_KEY`                                |
| `APITimeoutError`                                         | Azure endpoint slow    | Adapter retries once, then returns `extraction_failed=True` |
| `429 Too Many Requests`                                   | Rate limited           | Adapter uses exponential back-off (1s, 2s, 4s, 8s)          |
| Empty skills list                                         | LLM returned bad JSON  | Check `meta['error_reason']` — may need prompt iteration    |
| `ImportError: langchain_openai`                           | Missing dependency     | `pip install langchain-openai`                              |


---

## 7. Layer 4 — Taxonomy Resolution

### What it does

After extraction, each skill is linked to the ESCO digital skills taxonomy using a 6-step resolution cascade:

1. Exact match against GenAI Extension Layer (10 predefined skills)
2. Exact name match against ESCO digital skills
3. Normalized name match (case-insensitive, punctuation-stripped)
4. Embedding cosine similarity >= 0.92
5. O*NET occupation code match
6. Emit as `raw_skill` (unresolved — null `esco_uri`)

### Key files


| File                                                         | Purpose                                                                |
| ------------------------------------------------------------ | ---------------------------------------------------------------------- |
| `agents/skills_extraction/extractors/taxonomy.py`            | `resolve_taxonomy()`, `resolve_taxonomy_batch()`, `resolution_stats()` |
| `agents/skills_extraction/taxonomy/esco_digital_skills.json` | ESCO corpus                                                            |
| `agents/skills_extraction/taxonomy/genai_extension.json`     | 10 GenAI skills                                                        |
| `agents/skills_extraction/taxonomy/onet_skills.txt`          | O*NET codes                                                            |


### How it connects

- **Reads:** Local JSON/CSV files (no database reads)
- **Writes:** Nothing — enriches SkillRecord objects in memory, written to DB by the agent
- **LLM cost:** None (pure lookup + optional embedding similarity)

### Test steps

**Step 1 — Run taxonomy unit tests:**

```bash
python -m pytest agents/tests/test_taxonomy_resolver.py -v --tb=short
```

Expected: All tests pass. Covers all 6 resolution steps, batch processing, dedup, and stats.

**Step 2 — Test resolution interactively:**

The script resolves these skill labels through the taxonomy pipeline: **Python**, **Machine Learning**, **React**, and **nonexistent-skill-xyz** (deliberate miss).

```bash
python agents/scripts/test_taxonomy_resolution.py
```

Expected: Known skills resolve at steps 1-4 with ESCO URIs. Unknown skills fall to step 6 with `esco_uri=None`. Coverage should be >0% for real skill names.

**Step 3 — Verify GenAI extension skills:**

```python
python -c "
from agents.skills_extraction.extractors.taxonomy import resolve_taxonomy

for skill in ['Prompt Engineering', 'LLM Fine-tuning', 'RAG Architecture']:
    result = resolve_taxonomy(skill)
    print(f'{skill}: step={result.resolution_step}, genai={result.is_genai_extension}, uri={result.esco_uri}')
"
```

Expected: GenAI skills resolve at step 1 with `is_genai_extension=True`.

### Troubleshooting


| Symptom                                       | Cause                           | Fix                                                     |
| --------------------------------------------- | ------------------------------- | ------------------------------------------------------- |
| `FileNotFoundError: esco_digital_skills.json` | Taxonomy data missing           | Check `agents/skills_extraction/taxonomy/` directory    |
| All skills resolve at step 6                  | Corpus not loaded               | Verify `esco_digital_skills.json` is valid JSON         |
| Low coverage (<50%)                           | Many niche or misspelled skills | Expected for specialized domains; check raw skill names |


---

## 8. Layer 5 — Audit Logging and Cost Tracking

### What it does

Every LLM call is logged to `dbo.llm_audit_log` with prompt hash, model, token counts (input + output + total), cost in USD, latency, and success/error status. This is the foundation for cost projections and operational monitoring.

### Key files


| File                                 | Purpose                                                  |
| ------------------------------------ | -------------------------------------------------------- |
| `agents/common/llm_adapter.py`       | `log_extraction_event()` — writes to `dbo.llm_audit_log` |
| `agents/common/data_store/models.py` | `LLMAuditLog` ORM model                                  |
| `agents/eval/cost_projection.py`     | Queries audit log for cost analysis                      |


### How it connects

- **Writes:** `dbo.llm_audit_log` — one row per LLM call
- **Read by:** `cost_projection.py`, Streamlit dashboard (future)
- **Session management:** Uses `session_scope()` — auto-commit on success, rollback on error
- **Never raises:** Logging failures are caught and logged via structlog, never breaking the pipeline

### Test steps

**Step 1 — Verify table exists and check current row count:**

```bash
python agents/scripts/db_check.py query "SELECT COUNT(*) AS audit_rows FROM dbo.llm_audit_log"
```

Note the count. After running the pipeline, it should increase.

**Step 2 — Run a pipeline that triggers LLM calls:**

```bash
python agents/pipeline_runner.py
```

**Step 3 — Verify audit log rows were written:**

```bash
python agents/scripts/db_check.py query "SELECT agent_name, model, provider, latency_ms, input_tokens, output_tokens, token_count, cost_usd, success, error_reason FROM dbo.llm_audit_log ORDER BY created_at DESC LIMIT 5"
```

Expected: Rows with `agent_name='skills-extraction-agent'`, `success=true`, and non-zero `input_tokens`, `output_tokens`, `cost_usd`.

**Step 4 — Verify cost computation:**

```bash
python agents/scripts/db_check.py query "SELECT model, COUNT(*) AS calls, SUM(input_tokens) AS total_in, SUM(output_tokens) AS total_out, ROUND(SUM(cost_usd)::numeric, 4) AS total_cost FROM dbo.llm_audit_log WHERE success = true GROUP BY model"
```

Expected: Cost totals grouped by model tier. Verify costs are non-zero and proportional to token counts.

**Step 5 — Check for failed LLM calls:**

```bash
python agents/scripts/db_check.py query "SELECT agent_name, error_reason, created_at FROM dbo.llm_audit_log WHERE success = false ORDER BY created_at DESC LIMIT 5"
```

Expected: Either no rows (all calls succeeded) or rows with meaningful `error_reason` (timeout, rate limit, etc.).

### Troubleshooting


| Symptom                                       | Cause                                   | Fix                                                            |
| --------------------------------------------- | --------------------------------------- | -------------------------------------------------------------- |
| No rows in `llm_audit_log` after pipeline run | `log_extraction_event()` not called     | Verify `llm_client.py` imports from `llm_adapter` (not a stub) |
| `cost_usd = 0.0` on all rows                  | `compute_extraction_cost()` returning 0 | Check pricing env vars or model tier mapping                   |
| `input_tokens = 0` on success rows            | Token estimation failed                 | Check `response.usage` in LLM response metadata                |
| Rows exist but `success = false` everywhere   | LLM calls failing                       | Check `error_reason` column — usually auth or timeout          |


---

## 9. Layer 6 — Evaluation Harness

### What it does

Compares extraction output against a hand-labeled ground truth dataset of job postings. Computes precision and recall for skills and tools extraction. Currently at 30 records (target: 30-50).

### Key files


| File                                       | Purpose                                                |
| ------------------------------------------ | ------------------------------------------------------ |
| `agents/eval/extraction_eval.py`           | Evaluation runner: load ground truth, extract, compare |
| `agents/eval/extraction_ground_truth.json` | Hand-labeled records with expected skills/tools        |
| `agents/eval/prompt_iteration_log.md`      | Track prompt changes and metric deltas                 |


### How it connects

- **Reads:** Ground truth JSON file (local, no DB)
- **Writes:** Nothing — prints metrics to stdout
- **LLM cost:** Depends on extraction method used (real LLM = cost; stub = free)

### Ground truth record schema

Each record contains:

| Field              | Type       | Description                                                  |
| ------------------ | ---------- | ------------------------------------------------------------ |
| `ground_truth_id`  | string     | Sequential ID (`gt-001` through `gt-030`)                    |
| `external_id`      | string     | Source-specific job ID                                       |
| `source`           | string     | `JSearch` or scrape source                                   |
| `title`            | string     | Job title                                                    |
| `company`          | string     | Employer name                                                |
| `city`, `state`    | string     | Location                                                     |
| `description`      | string     | Full job description text                                    |
| `requirements`     | string     | Requirements section text                                    |
| `responsibilities` | string     | Responsibilities section text                                |
| `skills`           | array      | Hand-labeled skills with `skill_name`, `type`, `confidence`, `required_flag`, `esco_uri`, `is_genai_extension`, `source_span` |
| `tools`            | array      | Hand-labeled tools with `tool_name`, `category`, `confidence`, `is_genai_tool`, `source_span` |
| `labeler_notes`    | object     | Free-form labeler annotations                                |

### Current coverage

| Role category            | Records | GT IDs          | Labeler          |
| ------------------------ | ------- | --------------- | ---------------- |
| AI Product Managers      | 4       | gt-001 – gt-004 | Enrique          |
| AI Product Managers      | 1       | gt-005          | Nestor           |
| AI Product Managers      | 1       | gt-006          | Emilio           |
| Agile Project Managers   | 4       | gt-007 – gt-010 | Juan             |
| Agile Project Managers   | 1       | gt-011          | Emilio           |
| Data Analysts            | 3       | gt-012 – gt-014 | Angel            |
| Data Analysts            | 1       | gt-015          | Nestor           |
| Data Analysts            | 1       | gt-016          | Emilio           |
| Full Stack Developers    | 4       | gt-017 – gt-020 | Bryan            |
| Full Stack Developers    | 1       | gt-021          | Emilio           |
| ML Engineers             | 3       | gt-022 – gt-024 | Fabian           |
| ML Engineers             | 1       | gt-025          | Nestor           |
| Cybersecurity Analysts   | 4       | gt-026 – gt-029 | Fatima           |
| Cybersecurity Analysts   | 1       | gt-030          | Nestor           |
| **Total**                | **30**  |                 |                  |

### Test steps

**Step 1 — Verify ground truth dataset:**

```bash
python agents/scripts/test_ground_truth.py
```

Expected: 30 records with keys: `ground_truth_id`, `external_id`, `source`, `title`, `company`, `city`, `state`, `description`, `requirements`, `responsibilities`, `skills`, `tools`, `labeler_notes`.

**Step 2 — Run the evaluation harness:**

```bash
python -m agents.eval.extraction_eval
```

Expected output: Per-record breakdown showing GT vs predicted skills/tools with set intersections, then aggregate metrics:

```
=== FINAL METRICS ===
Total GT Skills: 177
Total Pred Skills: <N>
Matched Skills: <N>
Skills Precision: <0-1>
Skills Recall:    <0-1>

--- TOOLS ---
Total GT Tools: 104
Total Pred Tools: <N>
Matched Tools: <N>
Tools Precision: <0-1>
Tools Recall:    <0-1>
```

> **Note:** The default eval uses `extract_from_text_testing()` — a keyword-matching baseline (no LLM). Expect low precision/recall (~0.28/0.11 for skills, ~0.43/0.10 for tools). Switch to `extract_from_text()` for LLM-based extraction (requires Azure OpenAI env vars and incurs cost).

**Step 3 — Record baseline metrics:**

After running the harness, update `agents/eval/prompt_iteration_log.md` with the version, date, and metrics. This becomes the baseline for prompt iteration.

### Troubleshooting


| Symptom                                           | Cause                               | Fix                                                                 |
| ------------------------------------------------- | ----------------------------------- | ------------------------------------------------------------------- |
| `FileNotFoundError: extraction_ground_truth.json` | File missing                        | Verify `agents/eval/` directory                                     |
| `UnicodeDecodeError: 'charmap'`                   | Windows CP1252 encoding             | Ensure file reads use `encoding="utf-8"`                            |
| `KeyError: 'skill_name'`                          | Old records using `label` key       | Run schema normalization (rename `label` → `skill_name` in records) |
| Very low precision (<50%)                         | Extractor producing false positives | Check confidence threshold (`SKILL_CONFIDENCE_THRESHOLD`)           |
| Very low recall (<50%)                            | Extractor missing skills            | Check prompt template or extraction logic                           |


---

## 10. Layer 7 — Full Pipeline

### What it does

Runs the complete pipeline end-to-end: Ingestion -> Normalization -> Skills Extraction -> Enrichment -> Analytics -> Visualization. Verifies that all stages complete, all tables are populated, and audit logging captures every LLM call.

### Key files


| File                                        | Purpose                                  |
| ------------------------------------------- | ---------------------------------------- |
| `agents/pipeline_runner.py`                 | Sequential pipeline orchestrator         |
| `agents/scripts/run_full_pipeline_redis.py` | Redis Streams variant (with HTML report) |


### Test steps

**Step 1 — Reset database (optional, for clean run):**

```bash
python agents/scripts/db_check.py reset
```

**Step 2 — Run the in-process pipeline:**

```bash
python agents/pipeline_runner.py
```

Expected: All agents report health, pipeline completes without error, output written to `agents/data/output/pipeline_run.json`.

**Step 3 — Verify all tables populated:**

```bash
python agents/scripts/db_check.py counts
```

Expected output:

```
raw_ingested_jobs:       >0
normalized_jobs:         >0
extracted_intelligence:  >0
llm_audit_log:           >0  (if LLM was called)
job_ingestion_runs:      >0
```

**Step 4 — Verify extracted_intelligence has data:**

```bash
python agents/scripts/db_check.py query "SELECT ei.id, nj.title, ei.extraction_version, ei.extraction_model, jsonb_array_length(ei.skills) AS skill_count, ei.extraction_cost_usd, ei.extraction_failed FROM dbo.extracted_intelligence ei JOIN dbo.normalized_jobs nj ON ei.normalized_job_id = nj.id ORDER BY ei.id DESC LIMIT 5"
```

Expected: Rows showing job titles with skill counts, extraction version, and cost.

**Step 5 — Verify end-to-end data flow (trace one record):**

```bash
# Pick a raw job ID and trace it through all stages
python agents/scripts/db_check.py query "
SELECT 'raw' AS stage, rij.id, rij.title, rij.processing_status AS status
FROM dbo.raw_ingested_jobs rij WHERE rij.id = 1
UNION ALL
SELECT 'normalized', nj.id, nj.title, nj.normalization_status
FROM dbo.normalized_jobs nj WHERE nj.raw_job_id = 1
UNION ALL
SELECT 'extracted', ei.id, 'skills=' || jsonb_array_length(ei.skills)::text, CASE WHEN ei.extraction_failed THEN 'failed' ELSE 'success' END
FROM dbo.extracted_intelligence ei
JOIN dbo.normalized_jobs nj ON ei.normalized_job_id = nj.id
WHERE nj.raw_job_id = 1
"
```

Expected: Three rows showing the record progressing through raw -> normalized -> extracted stages.

**Step 6 — Run with Redis Streams (optional):**

```bash
python -m agents.scripts.run_full_pipeline_redis --redis-url redis://localhost:6379/0
```

Then open the HTML report:

```bash
# Windows
start agents\eval\full_pipeline_redis_metrics.html

# macOS/Linux
open agents/eval/full_pipeline_redis_metrics.html
```

**Step 7 — Run full test suite:**

```bash
python -m pytest agents/tests/ -v --tb=short
```

Expected: 138+ passed, 0 failed. DB-dependent tests require a live connection. Tests skipped without DB are expected.

### Troubleshooting


| Symptom                                | Cause                                      | Fix                                                 |
| -------------------------------------- | ------------------------------------------ | --------------------------------------------------- |
| Pipeline hangs at skills extraction    | LLM rate limit back-off                    | Wait for back-off to complete (max 8s per cycle)    |
| `extracted_intelligence` has 0 rows    | No normalized jobs to extract from         | Run ingestion + normalization first                 |
| `extraction_failed = true` on all rows | LLM calls failing                          | Check Layer 3 troubleshooting (Azure OpenAI config) |
| Pipeline completes but no LLM cost     | Fixture fallback used (no normalized text) | Ensure normalized jobs have `description` populated |
| `KeyError: 'skill_name'`               | Old code using `label`                     | Pull latest — `label` was renamed to `skill_name`   |


---

## 11. Layer 8 — Streamlit Dashboard

### What it does

Visual verification of pipeline results. Shows ingestion runs, record journeys, batch insights, and (in future weeks) extraction coverage and cost dashboards.

### Key files


| File                                | Purpose                    |
| ----------------------------------- | -------------------------- |
| `agents/dashboard/streamlit_app.py` | Main app entry point       |
| `agents/dashboard/pages/`           | Individual dashboard pages |


### How it connects

- **Reads:** `dbo.raw_ingested_jobs`, `dbo.normalized_jobs`, `dbo.job_ingestion_runs` via SQLAlchemy (read-only)
- **Fallback:** JSON files in `agents/data/output/` if DB is unavailable
- **Cache:** 60-second TTL with staleness banner

### Test steps

**Step 1 — Run dashboard tests:**

```bash
python -m pytest agents/tests/test_streamlit_app.py -v --tb=short
```

**Step 2 — Launch the dashboard:**

```bash
streamlit run agents/dashboard/streamlit_app.py
```

Opens at `http://localhost:8501`.

**Step 3 — Verify data source:**

Check the sidebar — it should say "Connected to PostgreSQL" (not "Using fixture data"). If it says fixture, your `PYTHON_DATABASE_URL` is not set or the DB is unreachable.

**Step 4 — Check each page:**

- **Pipeline Run Summary:** Shows recent ingestion runs with record counts
- **Record Journey:** Select a record and trace it through pipeline stages
- **Batch Insights:** Charts for locations, employment types, salary distributions

### Troubleshooting


| Symptom                          | Cause              | Fix                                             |
| -------------------------------- | ------------------ | ----------------------------------------------- |
| "Using fixture data" in sidebar  | DB not connected   | Set `PYTHON_DATABASE_URL` and restart Streamlit |
| Empty charts                     | No data in tables  | Run the pipeline first (Layer 7)                |
| `ModuleNotFoundError: streamlit` | Not installed      | `pip install streamlit`                         |
| Blank page                       | Error in page code | Check terminal for Python traceback             |


---

## 12. Troubleshooting by Layer

Quick-reference: when something fails, identify which layer and check here.

### Connection chain

```
.env (PYTHON_DATABASE_URL)
  --> database.py (get_engine)
    --> session_scope()
      --> models.py (ORM read/write)
        --> migrations.py (table creation)

.env (AZURE_OPENAI_*)
  --> llm_client.py (invoke_skills_llm)
    --> llm_adapter.py (log_extraction_event --> dbo.llm_audit_log)
```

### Diagnostic commands

```bash
# 1. Is the DB reachable?
python -c "from dotenv import load_dotenv; load_dotenv(); from agents.common.data_store import check_db_connection; print('DB:', 'OK' if check_db_connection() else 'FAIL')"

# 2. Do all tables exist?
python agents/scripts/db_check.py tables

# 3. Are there rows in key tables?
python agents/scripts/db_check.py counts

# 4. Is Azure OpenAI reachable?
python -m agents.scripts.test_llm_connection

# 5. Can the skills extractor parse a response?
python -m pytest agents/tests/test_skills_extractor.py -v --tb=short

# 6. Does the taxonomy resolver work?
python -m pytest agents/tests/test_taxonomy_resolver.py -v --tb=short

# 7. Do all tests pass?
python -m pytest agents/tests/ -v --tb=short

# 8. Is ruff clean?
python -m ruff check agents/
```

### Common cross-layer issues


| Issue                                                                     | Layers affected | Root cause                                                | Fix                                                                |
| ------------------------------------------------------------------------- | --------------- | --------------------------------------------------------- | ------------------------------------------------------------------ |
| `SkillRecord has no attribute 'label'`                                    | 2, 3, 6         | Old code using `label` instead of `skill_name`            | Replace `.label` with `.skill_name` everywhere                     |
| `log_extraction_event() got unexpected keyword 'prompt_hash'`             | 5               | Old call signature from pre-merge code                    | Use `prompt=` (raw text), not `prompt_hash=`                       |
| `compute_extraction_cost() takes 2 positional arguments but 3 were given` | 5               | Old 2-arg signature                                       | Use 3 args: `(input_tokens, output_tokens, model_tier)`            |
| `LlmAuditLog` vs `LLMAuditLog` import error                               | 5               | Wrong class name                                          | The canonical name is `LLMAuditLog` (all caps)                     |
| `normalized_job_id cannot be null` on insert                              | 1, 7            | Trying to write `ExtractedIntelligence` without a real FK | Ensure `normalized_job_id` maps to a real `dbo.normalized_jobs.id` |


---

## Appendix: Test Matrix


| Layer            | Test command                                          | Requires DB | Requires LLM | Expected    |
| ---------------- | ----------------------------------------------------- | ----------- | ------------ | ----------- |
| Database         | `pytest agents/tests/test_database.py`                | Yes         | No           | All pass    |
| ORM Models       | `pytest agents/tests/test_models.py`                  | Yes         | No           | All pass    |
| Tools (Pass 1)   | `pytest agents/tests/test_tools_extractor.py`         | No          | No           | All pass    |
| Skills (Pass 2)  | `pytest agents/tests/test_skills_extractor.py`        | No          | No (mocked)  | All pass    |
| Taxonomy         | `pytest agents/tests/test_taxonomy_resolver.py`       | No          | No           | All pass    |
| Agent (bridge)   | `pytest agents/tests/test_skills_extraction_agent.py` | No          | No (mocked)  | All pass    |
| Pipeline         | `pytest agents/tests/test_pipeline_runner.py`         | No          | No           | All pass    |
| Extraction stubs | `pytest agents/skills_extraction/tests/`              | No          | No           | All pass    |
| Dashboard        | `pytest agents/tests/test_streamlit_app.py`           | No          | No           | All pass    |
| Full suite       | `pytest agents/tests/ -v`                             | Partial     | No           | 138+ passed |


