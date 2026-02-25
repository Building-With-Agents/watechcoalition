# CLAUDE.md — Job Intelligence Engine

This file is the primary context document for Claude Code.
Read this before touching any file in the repo.
Source of truth: `job_intelligence_engine_architecture.docx` — see `docs/planning/ARCHITECTURE_DEEP.md` for full implementation spec.

---

## Project Summary

**Job Intelligence Engine** — an eight-agent Python pipeline that ingests, normalizes, enriches, and analyzes external job postings for the watechcoalition platform (Next.js + MSSQL).

The existing app is a Next.js/TypeScript/Prisma app. The agent pipeline is a **separate Python layer** that lives in `agents/` and runs alongside it.

**Do NOT modify the Next.js app or `prisma/schema.prisma` unless explicitly instructed.**

---

## Non-Negotiable Rules

1. **One agent = one responsibility.** Helper logic (dedup, validation, field mapping, confidence scoring) stays encapsulated inside the owning agent. Never promoted to its own agent.
2. **Agents communicate via typed, versioned events only.** Direct function calls between agents are forbidden.
3. **The Orchestration Agent is the sole consumer** of `*Failed` and `*Alert` events. No other agent reacts to another agent’s failures.
4. **No agent writes to another agent’s internal state.**
5. **Every agent exposes a `health_check()` method** and emits self-evaluation metrics.
6. **Python agents access MSSQL via SQLAlchemy only.** Prisma is Next.js-only — never import or invoke it from Python.
7. **No credentials in code or logs.** Environment variables only.
8. **Do NOT implement Phase 2 items during Phase 1** unless explicitly instructed.

---

## Repository Structure

```
/                              ← Next.js app root (DO NOT MODIFY)
├── app/
├── prisma/schema.prisma       ← Read-only from Python
└── agents/
    ├── ingestion/
    │   ├── agent.py
    │   ├── sources/           ← jsearch_adapter.py, scraper_adapter.py
    │   ├── deduplicator.py
    │   └── tests/
    ├── normalization/
    │   ├── agent.py
    │   ├── schema/            ← Canonical JobRecord + Pydantic validators
    │   ├── field_mappers/
    │   └── tests/
    ├── skills_extraction/
    │   ├── agent.py
    │   ├── models/            ← LLM wrappers + prompt files
    │   ├── taxonomy/
    │   └── tests/
    ├── enrichment/
    │   ├── agent.py
    │   ├── classifiers/       ← Role, seniority, quality, spam (Phase 1)
    │   ├── resolvers/         ← Company, geo, labor-market lookups (Phase 2 only)
    │   └── tests/
    ├── analytics/
    │   ├── agent.py
    │   ├── aggregators/
    │   ├── query_engine/      ← Text-to-SQL + guardrails
    │   └── tests/
    ├── visualization/
    │   ├── agent.py
    │   ├── renderers/
    │   ├── exporters/         ← PDF, CSV, JSON (all standard — not stretch)
    │   └── tests/
    ├── orchestration/
    │   ├── agent.py
    │   ├── scheduler/         ← APScheduler wrapper
    │   ├── circuit_breaker/   ← Phase 2 only — scaffold, do not implement
    │   ├── saga/              ← Phase 2 only — scaffold, do not implement
    │   ├── admin_api/         ← Phase 2 only — scaffold, do not implement
    │   └── tests/
    ├── demand_analysis/       ← Phase 2 only — scaffold directory, do not implement
    │   ├── agent.py
    │   ├── time_series/
    │   ├── forecasting/
    │   └── tests/
    ├── common/
    │   ├── events/            ← AgentEvent dataclass + all typed event definitions
    │   ├── message_bus/       ← In-process Python pub/sub (Phase 1); bus-agnostic contracts
    │   ├── llm_adapter.py
    │   ├── data_store/
    │   ├── config/
    │   ├── observability/
    │   └── errors/
    ├── dashboard/
    │   └── streamlit_app.py
    ├── platform/              ← Scaffold in Phase 1; populated in Phase 2
    │   ├── infrastructure/
    │   ├── ci_cd/
    │   ├── monitoring/
    │   └── runbooks/
    ├── data/
    │   ├── staging/           ← raw_ingested_jobs output
    │   ├── normalized/        ← normalized_jobs output
    │   ├── enriched/          ← enriched records pre-promotion
    │   ├── analytics/         ← computed aggregates
    │   ├── demand_signals/    ← Phase 2
    │   ├── rendered/          ← Visualization artifact cache
    │   └── dead_letter/       ← quarantined records (retry-exhausted)
    ├── eval/                  ← 30–50 hand-labeled JSON records (Week 4)
    ├── docs/
    │   ├── architecture/
    │   ├── api/               ← Agent & admin API contracts
    │   └── adr/               ← Architecture Decision Records
    └── tests/                 ← Integration tests (pytest)
```

---

## Architecture — Eight Agents, One Pipeline

```
Sources (JSearch API via httpx / Web scraping via Crawl4AI)
    ↓  [daily cron: INGESTION_SCHEDULE]
[Ingestion Agent]         → IngestBatch
    ↓
[Normalization Agent]     → NormalizationComplete
    ↓
[Skills Extraction Agent] → SkillsExtracted
    ↓
[Enrichment Agent]        → RecordEnriched
    ↓              ↘
[Analytics Agent]    [Demand Analysis Agent]  ← Phase 2 only
    ↓
[Visualization Agent]     → RenderComplete

[Orchestration Agent]     ← sole consumer of ALL *Failed/*Alert events
                          ← schedules, monitors, retries all agents above
```

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Agent runtime | Python 3.11+ | Lives in `agents/` — separate from Next.js |
| Multi-agent framework | LangGraph | **Locked** — StateGraph for routing (decision #13) |
| LLM adapter | LangChain + Azure OpenAI | Provider-agnostic; switchable via `LLM_PROVIDER` |
| Agent tracing | LangSmith | **Locked** — native LangGraph integration (decision #17) |
| Scheduling | APScheduler | Inside Orchestration Agent; cron-configurable |
| DB access (agents) | SQLAlchemy + pyodbc | → MSSQL; never via Prisma |
| DB access (Next.js) | Prisma | Do not touch from Python |
| Scraping | Crawl4AI | **Locked** — local, pip-installable (decision #12) |
| API ingestion | httpx | JSearch API calls (decision #12) |
| Dashboards | Streamlit | Read-only SQLAlchemy connection |
| Testing | pytest | `agents/tests/` |
| Logging | structlog | JSON-formatted, no PII ever |

---

## Environment Variables

All credentials in `.env` — never hardcode any of these.

```bash
# LLM
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT_NAME=
LLM_PROVIDER=azure_openai          # azure_openai | openai | anthropic

# Database
PYTHON_DATABASE_URL=                # SQLAlchemy pyodbc URL for agents:
                                    #   mssql+pyodbc://user:pass@host:port/db?driver=ODBC+Driver+17+for+SQL+Server
                                    # Note: DATABASE_URL (Prisma sqlserver:// format) is for Next.js only

# Tracing
LANGSMITH_API_KEY=
LANGCHAIN_TRACING_V2=true

# Ingestion
JSEARCH_API_KEY=
SCRAPING_TARGETS=                   # Comma-separated target URLs
INGESTION_SCHEDULE=0 2 * * *        # Cron expression — default: daily at 2am

# Pipeline thresholds
SPAM_FLAG_THRESHOLD=0.7             # Flag for operator review above this
SPAM_REJECT_THRESHOLD=0.9           # Auto-reject above this
SKILL_CONFIDENCE_THRESHOLD=0.75
BATCH_SIZE=100
```

---

## Common Patterns — Follow These Exactly

### Event envelope (every inter-agent event must use this shape)

```python
# agents/common/events/base.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentEvent:
    event_id: str          # uuid4
    correlation_id: str    # propagated unchanged from IngestBatch through all downstream events
    agent_id: str          # e.g. "ingestion_agent"
    timestamp: datetime
    schema_version: str    # "1.0" — increment on breaking payload changes
    payload: dict
```

### LLM adapter usage

```python
from agents.common.llm_adapter import get_adapter

adapter = get_adapter(provider=os.getenv("LLM_PROVIDER", "azure_openai"))
result = adapter.complete(prompt=prompt, schema=OutputSchema)
```

Fallback: 2 retries → log to `llm_audit_log` → set `extraction_status = "failed"` → continue batch. Never block a batch on LLM failure.

### Structured logging (no PII ever)

```python
import structlog
log = structlog.get_logger()
log.info("ingestion_batch_complete", batch_id=batch_id, record_count=n, dedup_count=d)
```

### Health check (required on every agent class)

```python
def health_check(self) -> dict:
    return {
        "status": "ok",       # "ok" | "degraded" | "down"
        "agent": "ingestion",
        "last_run": self.last_run_at.isoformat(),
        "metrics": self.last_run_metrics
    }
```

---

## Database Schema

**Read from `prisma/schema.prisma` — key existing tables:**
- `job_postings` — canonical job records; final destination for enriched jobs
- `companies`, `company_addresses` — company reference data
- `skills` — canonical skill taxonomy with embeddings; M:M with job_postings
- `technology_areas`, `industry_sectors` — watechcoalition classification taxonomy

**New columns on `job_postings` (Phase 1 — SQLAlchemy migration only, never touch schema.prisma):**

```sql
ALTER TABLE job_postings ADD COLUMN source NVARCHAR(50);
ALTER TABLE job_postings ADD COLUMN external_id NVARCHAR(255);
ALTER TABLE job_postings ADD COLUMN ingestion_run_id NVARCHAR(36);
ALTER TABLE job_postings ADD COLUMN ai_relevance_score FLOAT;
ALTER TABLE job_postings ADD COLUMN quality_score FLOAT;
ALTER TABLE job_postings ADD COLUMN is_spam BIT;
ALTER TABLE job_postings ADD COLUMN spam_score FLOAT;
ALTER TABLE job_postings ADD COLUMN overall_confidence FLOAT;
ALTER TABLE job_postings ADD COLUMN field_confidence NVARCHAR(MAX); -- JSON
```

**Agent-managed tables (created by agents, not Prisma):**

| Table | Phase | Purpose |
|-------|-------|---------|
| `raw_ingested_jobs` | 1 | Ingestion staging |
| `normalized_jobs` | 1 | Post-normalization records |
| `job_ingestion_runs` | 1 | Batch run tracking |
| `alerts` | 1 | Active and historical alerts |
| `orchestration_audit_log` | 1 | All orchestration decisions (100% completeness required) |
| `llm_audit_log` | 1 | All LLM calls (prompt hash, model, latency, tokens) |
| `analytics_aggregates` | 1 | Computed aggregate tables |
| `demand_signals` | 2 | Trend and forecast outputs |

**Important:** Write to `job_postings` only after `company_id` is resolved. Do not write a record with a null `company_id`.

---

## Per-Agent Quick Reference

| Agent | File | Phase | Emits | Consumes |
|-------|------|-------|-------|---------|
| Ingestion | `agents/ingestion/agent.py` | 1 | `IngestBatch` | — |
| Normalization | `agents/normalization/agent.py` | 1 | `NormalizationComplete` | `IngestBatch` |
| Skills Extraction | `agents/skills_extraction/agent.py` | 1 | `SkillsExtracted` | `NormalizationComplete` |
| Enrichment (lite) | `agents/enrichment/agent.py` | 1 | `RecordEnriched` | `SkillsExtracted` |
| Analytics | `agents/analytics/agent.py` | 1 | `AnalyticsRefreshed` | `RecordEnriched` |
| Visualization | `agents/visualization/agent.py` | 1 | `RenderComplete` | `AnalyticsRefreshed` |
| Orchestration | `agents/orchestration/agent.py` | 1 | trigger/retry signals | ALL events incl. `*Failed`/`*Alert` |
| Demand Analysis | `agents/demand_analysis/agent.py` | 2 | `DemandSignalsUpdated` | `RecordEnriched` |

---

## Key Agent Behaviors

### Ingestion Agent
- Sources: JSearch via `httpx`; web scraping via Crawl4AI
- Fingerprint: `sha256(source + external_id + title + company + date_posted)`
- **JSearch wins over scraped** when the same job appears in both sources (decision #9)
- Dedup before staging — duplicates discarded silently, counter incremented
- Provenance tags on every record: `source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`

### Normalization Agent
- Maps source fields → canonical `JobRecord` via per-source field mappers
- Standardizes: dates (ISO 8601), salaries (min/max/currency/period), locations, employment types
- Quarantines schema violations — never passes bad records downstream

### Skills Extraction Agent
- Taxonomy linking order (strict):
  1. Exact name match → `skills` table
  2. Normalized name match → `skills` table
  3. Embedding cosine similarity ≥ 0.92 → `skills` table
  4. O\*NET occupation code match
  5. Emit as `raw_skill` (null taxonomy_id) — Enrichment resolves in Phase 2
- Log every LLM call to `llm_audit_log`

### Enrichment Agent (Phase 1 lite)
- Classify role and seniority
- Quality score [0–1]: completeness + clarity + AI keyword density + structural coherence
- Spam detection: `spam_score` < 0.7 → proceed | 0.7–0.9 → flag for review (`is_spam = null`) | > 0.9 → auto-reject, do NOT write to `job_postings`
- Resolve `company_id` before writing: match `companies` by name → no match → create placeholder
- Map `sector_id` → `industry_sectors`

### Analytics Agent
- Aggregates across 6 dimensions: skill, role, industry, region, experience level, company size
- Salary distributions: median, p25, p75, p95 per dimension
- Co-occurrence matrices, posting lifecycle metrics (time-to-fill proxies, repost rates)
- Weekly summaries: LLM-generated; deterministic template fallback if LLM unavailable
- SQL guardrails (always enforced): SELECT only | allowed tables only | no DDL/DML | 100-row limit | 30s timeout
- Cardinality explosion: cap dimensions; coalesce long-tail into “Other”; emit warning

### Visualization Agent
- Dashboard pages: Ingestion Overview | Normalization Quality | Skill Taxonomy Coverage | Weekly Insights | Ask the Data | Operations & Alerts
- Exports: PDF, CSV, JSON — **all standard Phase 1 deliverables, not stretch goals**
- TTL cache with staleness banner — never a blank page
- DB connection is **read-only**

### Orchestration Agent (Phase 1)
- Framework: LangGraph StateGraph + APScheduler
- Sole consumer of all `*Failed` / `*Alert` events
- Alerting tiers:
  - **Warning:** logged + metric emitted
  - **Critical:** paged to on-call
  - **Fatal:** circuit broken + human escalation required
- Retry policies:

| Agent | Max retries | Back-off |
|-------|------------|---------|
| Ingestion (source unreachable) | 5 | Exponential + jitter |
| Normalization (batch failure) | 3 | Exponential |
| Skills Extraction (LLM timeout) | 2 per record | Fixed 2s |
| Any agent (transient DB error) | 3 | Exponential |

- Audit log: 100% completeness required — every trigger, retry, and alert creation must be recorded

---

## Evaluation Targets (non-negotiable — check against these)

| Agent | Metric | Target |
|-------|--------|--------|
| Ingestion | Success rate | ≥ 98% per 24h |
| Ingestion | Duplicate rate forwarded | < 0.5% |
| Ingestion | Dead-letter volume | < 1%; alert above 2% |
| Normalization | Schema conformance | ≥ 99% |
| Normalization | Field mapping accuracy | ≥ 97% (spot check) |
| Normalization | Quarantine rate | < 1%; alert above 3% |
| Skills Extraction | Taxonomy coverage | ≥ 95% |
| Skills Extraction | Precision at taxonomy link | ≥ 92% (human eval) |
| Skills Extraction | Recall of key skills | ≥ 88% |
| Skills Extraction | Avg confidence score | ≥ 0.80 |
| Analytics | Aggregate accuracy | ≥ 99.5% vs raw recount |
| Analytics | Query p50 latency | < 500ms |
| Analytics | Aggregate freshness | Within 15 min of new enriched batch |
| Visualization | Render success rate | ≥ 99.5% |
| Visualization | Dashboard freshness | Within 5 min of trigger |
| Visualization | Export generation p95 | < 10s |
| Visualization | Cache hit rate | ≥ 70% |
| Orchestration | Pipeline end-to-end SLA | ≥ 95% of batches |
| Orchestration | Mean time to detect failure | < 60s |
| Orchestration | Mean time to recover (auto) | < 5 min |
| Orchestration | Audit log completeness | 100% |
| System | Batch throughput | 1,000 jobs < 5 minutes |

---

## Security Rules (enforced always)

- No credentials in code or logs — environment variables only
- No PII in log output (no job seeker names, emails, or personal data)
- Analytics Agent SQL: SELECT only | allowed tables only | no DDL/DML | 100-row limit | 30s timeout
- Visualization Agent DB connection: read-only
- All SQL validation failures logged to `llm_audit_log`

---

## Build Order (12-Week Curriculum)

| Week | Deliverable | Key outputs |
|------|------------|-------------|
| 1 | Environment + first scrape + basic Streamlit | Working Python env, raw JSON scrape, Streamlit prototype |
| 2 | LLM adapter + thin-slice pipeline | `llm_adapter.py`, extraction prompt, extracted JSON, Streamlit extract view |
| 3 | Ingestion Agent + Normalization Agent | `IngestBatch`/`NormalizationComplete` events, staging tables, APScheduler |
| 4 | Skills Extraction Agent + eval harness + Enrichment-lite | `SkillsExtracted` event, eval dataset (30–50 labeled), prompt iteration log |
| 5 | Visualization Agent | Production Streamlit dashboards, PDF/CSV/JSON export, live MSSQL connection |
| 6 | Orchestration Agent | Scheduling, alerting tiers, retry policies, audit log, Operations & Alerts page |
| 7 | Analytics Agent — aggregates + weekly insights | Aggregate tables, LLM summaries, template fallback, `AnalyticsRefreshed` event |
| 8 | Analytics Agent — Ask the Data | Text-to-SQL, SQL guardrails + unit tests, “Ask the Data” Streamlit page |
| 9 | Pipeline hardening | Near-dedup in Ingestion, event contract enforcement, enrichment tuning, perf benchmark |
| 10 | Testing + security review + load testing | Integration test suite, security checklist, 1k-job load test, Dockerfile |
| 11 | Documentation | ARCHITECTURE.md, EVENT_CATALOG.md, RUNBOOK.md, CONFIGURATION.md, DEMO_SCRIPT.md |
| 12 | Capstone demo + release | Live demo to stakeholders, `v0.1.0-capstone` tag, handoff package, retrospective |

---

## Resolved Design Decisions

Copy here when a decision is locked in `docs/planning/ARCHITECTURAL_DECISIONS.md`.

| # | Decision | Resolution |
|---|----------|------------|
| 3 | Batch vs real-time | **Batch-first** — APScheduler, daily cron default |
| 4 | Source of truth for ingested jobs | **Option B — staging tables + promotion** (`raw_ingested_jobs` → `normalized_jobs` → `job_postings`) |
| 8 | Spam threshold | **Tiered** — flag at 0.7, auto-reject above 0.9 |
| 9 | Dedup source priority | **JSearch wins over scraped** on duplicate |
| 11 | LLM provider policy | **Provider-agnostic adapter** — Azure OpenAI default, switchable via env var |
| 12 | Scraping tool | **Crawl4AI** + **httpx** for JSearch |
| 13 | Multi-agent framework | **LangGraph** StateGraph |
| 14 | Message bus | **In-process Python events** (Phase 1); external bus deferred to Phase 2 |
| 15 | Skill taxonomy | **Internal watechcoalition primary** (`technology_areas`, `skills`); O\*NET fallback |
| 16 | Orchestration engine | **LangGraph StateGraph** (consistent with #13) |
| 17 | Agent tracing | **LangSmith** — native LangGraph integration |
| 18 | Analytics query interface | **REST** — `POST /analytics/query` |
| 19 | Database engine | **MSSQL** — stay on existing instance for Phase 1 |
| 20 | Enrichment phase split | **Lite (Phase 1) + Full (Phase 2)** |
| 21 | PDF export scope | **Standard Phase 1 deliverable** — not a stretch goal |

****Open decisions (do not implement — deferred to Phase 2):**

| # | Decision | Recommendation |
|---|----------|----------------|
| 22 | Multi-tenancy | Single shared pipeline for Phase 1; revisit before Phase 2 multi-org work |
| 23 | Feedback loop agent | Defer to Phase 2; requires ground truth, training pipeline, model versioning |

---

## How to Run

```bash
# Install Python deps
cd agents && pip install -r requirements.txt

# Run Streamlit dashboard
streamlit run agents/dashboard/streamlit_app.py

# Run full pipeline (via Orchestration Agent scheduler)
python -m agents.orchestration.scheduler

# Run a single agent manually
python -m agents.ingestion.agent --source jsearch --limit 50
python -m agents.ingestion.agent --source crawl4ai --limit 50

# Run tests
cd agents && pytest tests/

# Run integration tests only
cd agents && pytest tests/test_pipeline_integration.py
```

---

## What NOT to Do

- Do NOT create new agents for helper logic (dedup, validation, field mapping, etc.) — keep inside the owning agent
- Do NOT make agents call each other directly — use events
- Do NOT use Prisma from Python — SQLAlchemy only
- Do NOT write to `job_postings` without a resolved `company_id`
- Do NOT store credentials in code or logs
- Do NOT implement Phase 2 items (circuit-breaking, saga, admin API, demand analysis, full enrichment, external bus)
- Do NOT skip writing tests alongside implementation
- Do NOT modify the Next.js app or `prisma/schema.prisma` unless explicitly instructed
- Do NOT serve a blank dashboard page — always serve stale data with a staleness banner

---

## Full Specification Reference

For complete implementation specs, read in this order:

1. `docs/planning/ARCHITECTURE_DEEP.md` — canonical implementation reference (per-agent specs, JobRecord schema, event catalog, DB migrations, error-handling)
2. `docs/planning/TRD.md` — technical requirements, inter-agent contracts, NFRs
3. `docs/planning/BRD.md` — business scope, success criteria, design decisions
4. `docs/planning/PRD.md` — user stories, feature list, UX requirements
5. Week files in `docs/planning/curriculum/` — weekly deliverables and exercises
