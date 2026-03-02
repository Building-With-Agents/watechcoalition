# Job Intelligence Engine — Architecture Reference
**Audience:** Tech leads, senior engineers, product managers with technical context
**Version:** 1.1 | **Source of truth:** `job_intelligence_engine_architecture.docx`
**Last updated:** 2026-02-18
**Note:** Technology choices classified as SA (Student ADR) are reference implementations subject to team ADR decisions. Infrastructure constraints (IC) are fixed by the existing platform. See `ARCHITECTURAL_DECISIONS.md` for full IC/SA/D classification.

---

## System Overview

The Job Intelligence Engine is a flat, eight-agent Python pipeline that runs alongside the existing watechcoalition Next.js/MSSQL application. It ingests job postings from external sources, processes them through sequential enrichment stages, and writes validated records back to the shared MSSQL database for consumption by the job-seeker-facing UI.

The pipeline is **event-driven**: agents never call each other directly. Every hand-off is a typed, versioned event on an internal message bus. The Orchestration Agent is the sole controller of scheduling, routing, and failure recovery.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                       │
│         JSearch Web API          Web Scraping             │
│         (httpx) [SA #12]       (Crawl4AI) [SA #12]       │
└──────────────────────┬───────────────────────────────────┘
                       ↓  daily cron (INGESTION_SCHEDULE)
┌──────────────────────────────────────────────────────────┐
│  STAGE 1 — Ingestion Agent                               │
│  • Multi-source polling                                  │
│  • Exact dedup via sha256 fingerprint + source ID        │
│  • JSearch wins over scraped on duplicate                │
│  • Provenance tagging, idempotency keys                  │
│  • Writes to: raw_ingested_jobs                          │
│  • Emits: IngestBatch                                    │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  STAGE 2 — Normalization Agent                           │
│  • Maps source fields → canonical JobRecord schema       │
│  • Standardizes dates, salaries, locations, job types    │
│  • Validates schema; quarantines violations              │
│  • Writes to: normalized_jobs                            │
│  • Emits: NormalizationComplete                          │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  STAGE 3 — Skills Extraction Agent                       │
│  • LLM inference (Azure OpenAI default,                  │
│    provider-agnostic via LLM adapter [SA #11])              │
│  • Classifies: Technical/Domain/Soft/Cert/Tool           │
│  • Links to internal taxonomy; O*NET fallback            │
│  • Required vs preferred distinction                     │
│  • Per-skill confidence scores                           │
│  • Emits: SkillsExtracted                                │
└──────────────────────┬───────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────────┐
│  STAGE 4 — Enrichment Agent                              │
│  Phase 1 (lite):                                         │
│  • Seniority + job role classification                   │
│  • Quality scoring [0–1]                                 │
│  • Spam detection: flag 0.7–0.9, auto-reject > 0.9      │
│  • Resolves company_id, location_id before DB write      │
│  • Writes to: job_postings                               │
│  Phase 2 (full):                                         │
│  • Company data, geo enrichment, SOC/NOC codes           │
│  • raw_skill resolution, enrichment quality score        │
│  • Emits: RecordEnriched                                 │
└───────────┬──────────────────────────────────────────────┘
            ↓                         ↓
┌───────────────────────┐  ┌──────────────────────────────┐
│  STAGE 5a             │  │  STAGE 5b                    │
│  Demand Analysis      │  │  Analytics Agent             │
│  Agent (Phase 2)      │  │  • Aggregates: skill, role,  │
│  • Time-series by     │  │    industry, region,         │
│    skill/role/region  │  │    experience level,         │
│  • 7d/30d/90d         │  │    company size              │
│    velocity windows   │  │  • Salary distributions      │
│  • 30-day forecasts   │  │  • Skill co-occurrence       │
│  • Supply/demand gap  │  │  • Posting lifecycle metrics │
│  • Anomaly detection  │  │  • Weekly insight summaries  │
│  • Emits:             │  │  • Text-to-SQL Q&A           │
│  DemandSignalsUpd.    │  │  • Emits: AnalyticsRefreshed │
└───────────┬───────────┘  └──────────────┬───────────────┘
            └──────────────┬──────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│  STAGE 6 — Visualization Agent                           │
│  • Streamlit dashboards                                  │
│  • PDF, CSV, JSON exports (all standard — not stretch)   │
│  • TTL cache; staleness banner if data stale             │
│  • Emits: RenderComplete                                 │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  CONTROL PLANE — Orchestration Agent                     │
│  Phase 1: APScheduler [IC] + LangGraph StateGraph [SA #13] │
│  • Sole consumer of *Failed / *Alert events              │
│  • Retry policies per agent and error class              │
│  • Alerting tiers: Warning / Critical / Fatal            │
│  • Full audit log (100% completeness required)           │
│  Phase 2: circuit-breaking, saga pattern, admin API      │
└──────────────────────────────────────────────────────────┘
```

---

## Design Decisions (IC/SA/D Classification)

SA decisions show the **reference implementation** — teams produce ADRs for all SA decisions before implementing the affected agents. IC decisions are fixed by the existing platform.

| # | Decision | Type | Reference Implementation |
|---|----------|------|--------------------------|
| 3 | Batch vs real-time | IC | **Batch-first** — APScheduler-driven; default daily at 2am (configurable) |
| 4 | Source of truth for ingested jobs | IC | **Staging tables + promotion** — `raw_ingested_jobs` → `normalized_jobs` → `job_postings` |
| 8 | Spam threshold policy | IC | **Tiered** — flag at 0.7, auto-reject above 0.9 |
| 9 | Deduplication source priority | IC | **JSearch wins over scraped** when same job appears in both |
| 11 | LLM provider policy | **SA** | **Provider-agnostic adapter** — Azure OpenAI default; switchable via `LLM_PROVIDER` env var |
| 12 | Scraping tool | **SA** | **Crawl4AI** (local, open source) + **httpx** for JSearch API |
| 13 | Multi-agent framework | **SA** | **LangGraph** — StateGraph maps to pipeline; pairs with LangSmith for tracing |
| 14 | Message bus | **SA** | **In-process Python events** (Phase 1); external bus deferred to Phase 2 |
| 15 | Skill taxonomy | IC | **Internal watechcoalition taxonomy primary** (`technology_areas`, `skills`); O*NET fallback |
| 16 | Orchestration engine | **SA** | **LangGraph StateGraph** — consistent with #13 |
| 17 | Agent tracing | **SA** | **LangSmith** — native LangGraph integration, free tier |
| 18 | Analytics query interface | **SA** | **REST** — `POST /analytics/query`; simplest fit for two internal consumers |
| 19 | Database engine | IC | **MSSQL** — stays on existing watechcoalition instance |
| 20 | Enrichment phase split | IC | **Lite (Phase 1) + Full (Phase 2)** — external data sources not available in curriculum |
| 21 | PDF export scope | IC | **Standard Phase 1 deliverable** — not a stretch goal |

---

## Inter-Agent Event Catalog

All events share a standard envelope: `event_id`, `correlation_id`, `agent_id`, `timestamp`, `schema_version`, `payload`.

| Event | Producer | Consumers |
|-------|----------|-----------|
| `IngestBatch` | Ingestion | Normalization, Orchestrator |
| `NormalizationComplete` | Normalization | Skills Extraction, Orchestrator |
| `SkillsExtracted` | Skills Extraction | Enrichment, Orchestrator |
| `RecordEnriched` | Enrichment | Analytics, Demand Analysis*, Orchestrator |
| `DemandSignalsUpdated` | Demand Analysis* | Analytics, Visualization, Orchestrator |
| `AnalyticsRefreshed` | Analytics | Visualization, Orchestrator |
| `RenderComplete` | Visualization | Orchestrator |
| `*Failed` / `*Alert` | Any agent | **Orchestrator only** |
| `SourceFailure` | Ingestion | Orchestrator |
| `DemandAnomaly` | Demand Analysis* | Orchestrator |

*Phase 2

---

## Tech Stack

| Layer | Technology | Type | Notes |
|-------|-----------|------|-------|
| Agent runtime | Python 3.11+ | — | Lives in `agents/` — separate from Next.js app |
| Multi-agent framework | LangGraph | **SA** #13 | StateGraph for routing |
| LLM adapter | LangChain + Azure OpenAI | **SA** #11 | Provider-agnostic; switchable via `LLM_PROVIDER` env var |
| Agent tracing | LangSmith | **SA** #17 | Native LangGraph integration |
| Scheduling | APScheduler | IC #3 | Inside Orchestration Agent; cron-configurable |
| DB access (agents) | SQLAlchemy + pyodbc | IC #19 | → MSSQL; never via Prisma |
| DB access (Next.js app) | Prisma | IC #19 | Do not touch from Python |
| Dashboards | Streamlit | — | Read-only SQLAlchemy connection |
| Scraping | Crawl4AI | **SA** #12 | Local, pip-installable, no external service |
| API ingestion | httpx | **SA** #12 | JSearch API calls |
| Message bus | In-process Python pub/sub | **SA** #14 | Phase 1; external bus deferred to Phase 2 |
| Analytics query | REST — `POST /analytics/query` | **SA** #18 | Query interface for ad-hoc requests |
| Testing | pytest | — | `agents/tests/` |
| Logging | structlog | — | JSON-formatted, no PII |

---

## Database Layout

**Prisma-managed tables** (agents read/write via SQLAlchemy only):

| Table | Purpose |
|-------|---------|
| `job_postings` | Canonical job records — final destination for enriched jobs |
| `companies`, `company_addresses` | Company reference data |
| `skills` | Canonical skill taxonomy with embeddings |
| `technology_areas`, `industry_sectors` | Classification taxonomy |

**New columns on `job_postings`** (Phase 1 via SQLAlchemy migration — never touch `schema.prisma`):

`source`, `external_id`, `ingestion_run_id`, `ai_relevance_score`, `quality_score`, `is_spam`, `spam_score`, `overall_confidence`, `field_confidence` (JSON)

**Phase 2 additions:** `enrichment_quality_score`, `enrichment_partial`, `soc_code`, `remote_classification`

**Agent-managed tables:**

| Table | Phase | Purpose |
|-------|-------|---------|
| `raw_ingested_jobs` | 1 | Ingestion staging |
| `normalized_jobs` | 1 | Post-normalization records |
| `job_ingestion_runs` | 1 | Batch tracking |
| `alerts` | 1 | Active and historical alerts |
| `orchestration_audit_log` | 1 | All orchestration decisions |
| `llm_audit_log` | 1 | All LLM calls (prompt hash, model, latency, tokens) |
| `analytics_aggregates` | 1 | Computed aggregate tables |
| `demand_signals` | 2 | Trend and forecast outputs |

---

## Required Agent Interface

Every agent class must implement the following — no exceptions:

```python
def health_check(self) -> dict:
    return {
        "status": "ok",       # "ok" | "degraded" | "down"
        "agent": "<name>",
        "last_run": self.last_run_at.isoformat(),
        "metrics": self.last_run_metrics
    }
```

The Orchestration Agent polls `health_check()` on all agents and escalates degraded/down status per the alerting tier policy.

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
    │   ├── resolvers/         ← Company, geo, labor-market lookups (Phase 2)
    │   └── tests/
    ├── analytics/
    │   ├── agent.py
    │   ├── aggregators/
    │   ├── query_engine/      ← Text-to-SQL + guardrails
    │   └── tests/
    ├── visualization/
    │   ├── agent.py
    │   ├── renderers/
    │   ├── exporters/         ← PDF, CSV, JSON
    │   └── tests/
    ├── orchestration/
    │   ├── agent.py
    │   ├── scheduler/         ← APScheduler wrapper
    │   ├── circuit_breaker/   ← Phase 2 — scaffold only
    │   ├── saga/              ← Phase 2 — scaffold only
    │   ├── admin_api/         ← Phase 2 — scaffold only
    │   └── tests/
    ├── demand_analysis/       ← Phase 2 — scaffold only
    │   ├── agent.py
    │   ├── time_series/
    │   ├── forecasting/
    │   └── tests/
    ├── common/
    │   ├── events/            ← Typed event definitions
    │   ├── message_bus/       ← In-process pub/sub (Phase 1)
    │   ├── llm_adapter.py
    │   ├── data_store/
    │   ├── config/
    │   ├── observability/
    │   └── errors/
    ├── dashboard/
    │   └── streamlit_app.py
    ├── platform/              ← Scaffold Phase 1; populate Phase 2
    │   ├── infrastructure/
    │   ├── ci_cd/
    │   ├── monitoring/
    │   └── runbooks/
    ├── data/
    │   ├── staging/
    │   ├── normalized/
    │   ├── enriched/
    │   ├── analytics/
    │   ├── demand_signals/    ← Phase 2
    │   ├── rendered/
    │   └── dead_letter/       ← Quarantined records
    ├── eval/
    ├── docs/
    │   ├── architecture/
    │   ├── api/
    │   └── adr/
    └── tests/
```

---

## Per-Agent Summary

### Ingestion Agent
Polls JSearch via httpx and scrapes via Crawl4AI [SA #12] on a configurable cron schedule. Fingerprints and deduplicates records before staging. JSearch wins when the same job appears in both sources [IC #9].

### Normalization Agent
Maps source-specific fields to canonical `JobRecord` schema. Standardizes dates, salaries (min/max/currency/period), locations, and employment types. Quarantines schema violations without blocking the batch.

### Skills Extraction Agent
LLM inference over job text. Classifies skills into five types and links them to the internal taxonomy via exact match → normalized match → embedding similarity → O*NET fallback → `raw_skill`. Scores confidence per skill and distinguishes required vs preferred.

### Enrichment Agent
**Phase 1:** Classifies role and seniority, computes quality score, detects spam with tiered thresholds (flag at 0.7, reject above 0.9), resolves `company_id` and `location_id` before writing to `job_postings`.
**Phase 2:** Resolves `raw_skill` entries, appends company data (industry, size band, funding stage), geographic hierarchy (region, metro, remote), and labor-market codes (SOC/NOC, prevailing wage).

### Analytics Agent
Maintains aggregate tables across six dimensions: skill, role, industry, region, experience level, and company size. Computes salary distributions (median, p25, p75, p95), skill co-occurrence matrices, and posting lifecycle metrics (time-to-fill proxies, repost rates, posting duration). Generates LLM weekly summaries with template fallback. Handles text-to-SQL queries with SELECT-only guardrails, 100-row limit, and 30-second timeout. Handles dimension cardinality explosions by capping and coalescing long-tail values into "Other".

### Visualization Agent
Streamlit dashboards across six pages (Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts). Exports as PDF, CSV, and JSON — all standard deliverables. TTL cache with staleness banner; never serves a blank page.

### Orchestration Agent
**Phase 1:** APScheduler [IC #3] + LangGraph StateGraph [SA #13/#16] for routing. Sole consumer of all failure and alert events. Three-tier alerting: Warning (log + metric), Critical (page on-call), Fatal (circuit break + escalation). Structured JSON audit log with 100% completeness requirement.
**Phase 2:** Circuit-breaking (≥ 90% precision target), saga pattern at stage transitions, compensating flows, admin API.

### Demand Analysis Agent *(Phase 2)*
Time-series index by skill/role/industry/region. Velocity windows at 7d/30d/90d. Emerging vs declining skill identification. Supply/demand gap estimates where candidate-side data is available. 30-day forecasts with `DemandAnomaly` events on spikes or cliffs.

---

## Error-Handling Strategy

| Strategy | Phase | How It Works |
|----------|-------|-------------|
| Dead-letter store | 1 | Retry-exhausted records quarantined with full error context |
| Exponential back-off | 1 | All retries use back-off + jitter; max per agent and error class |
| Graceful degradation | 1 | Analytics/Visualization serve stale data with staleness flags; pipeline never halts for non-critical failures |
| Alerting tiers | 1 | Warning: log + metric. Critical: page on-call. Fatal: circuit break + human escalation |
| Circuit breaker | 2 | Orchestrator opens when error rate > threshold; ≥ 90% precision (no false positives) |
| Compensating sagas | 2 | Mid-pipeline failure rolls back to last successful checkpoint; records re-queued from there |

---

## Evaluation Targets

| Agent | Metric | Target |
|-------|--------|--------|
| Ingestion | Ingest success rate | ≥ 98% per 24h |
| Ingestion | Duplicate rate forwarded | < 0.5% |
| Normalization | Schema conformance | ≥ 99% |
| Normalization | Field mapping accuracy | ≥ 97% (spot check) |
| Skills Extraction | Taxonomy coverage | ≥ 95% |
| Skills Extraction | Precision at taxonomy link | ≥ 92% (human eval) |
| Skills Extraction | Recall of key skills | ≥ 88% |
| Analytics | Aggregate accuracy | ≥ 99.5% vs raw recount |
| Analytics | Query p50 latency | < 500ms |
| Visualization | Render success rate | ≥ 99.5% |
| Visualization | Export generation p95 | < 10s |
| Orchestration | Pipeline SLA | ≥ 95% of batches |
| Orchestration | Circuit-break precision | ≥ 90% (Phase 2) |
| Orchestration | Audit log completeness | 100% |
| System | Batch throughput | 1,000 jobs < 5 minutes |
| Demand Analysis | Forecast MAPE (30-day) | < 15% (Phase 2) |

---

## Build Order (12-Week Curriculum)

| Week(s) | Deliverable |
|---------|------------|
| 1–2 | Environment setup, first scrape, thin-slice pipeline, basic Streamlit |
| 3 | Ingestion Agent + Normalization Agent (with events) |
| 4 | Skills Extraction Agent + evaluation harness + Enrichment-lite |
| 5 | Visualization Agent (production Streamlit + PDF/CSV/JSON export) |
| 6 | Orchestration Agent (scheduling, alerting tiers, audit log) |
| 7 | Analytics Agent — aggregates + weekly insights |
| 8 | Analytics Agent — Ask the Data (text-to-SQL) |
| 9 | Pipeline hardening (near-dedup, event contract enforcement) |
| 10 | Testing, security review, load testing |
| 11 | Documentation (ARCHITECTURE.md, EVENT_CATALOG.md, RUNBOOK.md) |
| 12 | Capstone demo + release tag `v0.1.0-capstone` |
