# Job Intelligence Engine — Complete Canonical Architecture
**Audience:** Implementing engineers, Claude Code, technical leads
**Version:** 1.1 | **Source of truth:** `job_intelligence_engine_architecture.docx`
**Last updated:** 2026-02-18
**Status:** Complete system definition. Phase 1 / Phase 2 split is a delivery concern only — this document describes the full intended system with no scope reductions. Technology choices classified as SA (Student ADR) in `ARCHITECTURAL_DECISIONS.md` are subject to team ADR decisions. The tools listed here are the **reference implementation** — if a team selects a different technology via their ADR, adapt the corresponding agent implementation accordingly. Infrastructure constraints (IC) are fixed by the existing platform and are not open for team choice.

---

## Non-Negotiable Design Rules

1. **One agent = one primary responsibility.** Internal helper logic, transformations, and utility calls remain encapsulated inside the agent that needs them. They are never promoted to agent status. This keeps the agent graph flat, auditable, and easy to orchestrate.
2. **Agents communicate through typed, versioned events only.** Direct function calls between agents are forbidden.
3. **Every agent exposes a health-check and a self-evaluation signal.**
4. **The Orchestrator is the only entity that starts, stops, or replaces agents.**
5. **No agent writes to another agent's internal state.**
6. **The Orchestrator is the sole consumer of `*Failed` and `*Alert` events.** Other agents do not react to each other's failures.

---

## Tech Stack (IC = infrastructure constraint; SA = student ADR with reference implementation)

| Layer | Technology | Type | Decision |
|-------|-----------|------|---------|
| Agent runtime | Python 3.11+ | — | — |
| Multi-agent framework | LangGraph StateGraph | **SA** | #13 |
| LLM adapter | LangChain + Azure OpenAI (provider-agnostic) | **SA** | #11 |
| LLM provider default | Azure OpenAI; switchable via `LLM_PROVIDER` env var | **SA** | #11 |
| Agent tracing | LangSmith — native LangGraph integration | **SA** | #17 |
| Scheduling | APScheduler — inside Orchestration Agent | IC | #3 |
| Ingestion: API source | httpx — JSearch API calls | **SA** | #12 |
| Ingestion: web scraping | Crawl4AI — local, pip-installable | **SA** | #12 |
| DB access (agents) | SQLAlchemy + pyodbc → MSSQL | IC | #19 |
| DB access (Next.js app) | Prisma — do not touch from Python | IC | #19 |
| Message bus (Phase 1) | In-process Python pub/sub | **SA** | #14 |
| Message bus (Phase 2) | External bus (Kafka / RabbitMQ / Redis Streams) | **SA** | #14 |
| Dashboards | Streamlit — read-only SQLAlchemy connection | — | — |
| Analytics query interface | REST — `POST /analytics/query` | **SA** | #18 |
| Logging | structlog — JSON-formatted, no PII | — | — |
| Testing | pytest | — | — |

---

## System Overview

The eight agents form a directed pipeline that fans out at the enrichment stage and re-converges at analytics and visualization. The Orchestrator sits above all agents and is the sole owner of routing decisions.

### Agent Execution Sequence

| Stage | Agent | Primary Responsibility |
|-------|-------|----------------------|
| 1 — Fetch & Stage | Ingestion Agent | Raw data acquisition, dedup, provenance tagging |
| 2 — Clean & Conform | Normalization Agent | Canonical schema mapping, validation, quarantine |
| 3 — NLP Inference | Skills Extraction Agent | Skill identification, taxonomy linking, confidence scoring |
| 4 — Context Append | Enrichment Agent | Company/geo/labor-market context, taxonomy metadata, quality scoring |
| 5a — Trend Signals | Demand Analysis Agent | Time-series velocity, forecasts, anomaly detection |
| 5b — Aggregates | Analytics Agent | Salary distributions, co-occurrence, cohort summaries, ad-hoc queries |
| 6 — Render & Export | Visualization Agent | Dashboards, chart artifacts, PDF/CSV/JSON exports |
| X — Control Plane | Orchestration Agent (always-on) | Scheduling, routing, retries, circuit-breaking, audit log |

### End-to-End Data Flow

```
External Sources (JSearch API via httpx / Web scraping via Crawl4AI) [SA #12]
          ↓  [daily cron: INGESTION_SCHEDULE — default: 0 2 * * *]
   [Ingestion Agent]           → IngestBatch
          ↓
   [Normalization Agent]       → NormalizationComplete
          ↓
   [Skills Extraction Agent]   → SkillsExtracted
          ↓
   [Enrichment Agent]          → RecordEnriched
          ↓              ↘
   [Demand Analysis Agent]   [Analytics Agent]
          ↓              ↗
   [Visualization Agent]       → RenderComplete

   [Orchestration Agent]       ← consumes ALL events; sole consumer of *Failed/*Alert
```

---

## Agent Specifications

---

### 2.1 Ingestion Agent

*Owns all raw data acquisition. Nothing enters the system without passing through here.*

**Sources:**
- JSearch Web API via `httpx` — structured, high-quality job data (SA #12 — reference implementation)
- Web scraping via Crawl4AI — local, open source, no external service dependency (SA #12 — reference implementation)
- When the same job appears in both sources, **JSearch wins** and the scraped record is discarded (IC #9)

**Responsibilities:**
- Poll JSearch API and scrape configured targets on a daily cron schedule (`INGESTION_SCHEDULE`, default: `0 2 * * *`)
- Perform deduplication using fingerprint `sha256(source + external_id + title + company + date_posted)` before writing to staging (IC #4)
- Apply configurable rate-limiting and back-off per source
- Tag every record with provenance metadata: `source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`
- Emit a structured `IngestBatch` event per batch to the message bus

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Source configurations (URLs, credentials, schedules) from config store; optional manual trigger from Orchestrator |
| OUTPUT | Staged raw records in `raw_ingested_jobs` + `IngestBatch` event on message bus |
| SIDE EFFECT | Deduplication log, fetch audit trail, source health metrics |

**Error-Handling Strategy:**
- Source unreachable: exponential back-off (max 5 retries), then emit `SourceFailure` alert to Orchestrator
- Partial batch: stage what succeeded; mark failed records with `error_reason`; do not block downstream
- Duplicate detected: discard silently, increment dedup counter (observable via metrics)
- Schema violation at intake: quarantine record to dead-letter store for manual review

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Ingest success rate | ≥ 98% of attempted fetches per 24h window |
| Duplicate rate | < 0.5% of records forwarded are true duplicates |
| Source coverage | All configured sources polled within their SLA window |
| Data freshness | Records available in staging within 5 min of source publication |
| Dead-letter volume | < 1% of daily volume; alert above 2% |

---

### 2.2 Normalization Agent

*Transforms heterogeneous raw records into a single, validated canonical schema.*

**Responsibilities:**
- Read staged raw records from `raw_ingested_jobs` (IC #4: staging tables + promotion)
- Map source-specific field names and formats to the canonical JobRecord schema via per-source field mappers
- Parse and standardize dates (ISO 8601), salaries (min/max/currency/period), locations, and employment types
- Strip HTML, clean whitespace, and sanitize free-text fields
- Validate the output record against schema; reject and quarantine non-conforming records
- Write validated records to `normalized_jobs`
- Emit `NormalizationComplete` event per batch

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Raw records from `raw_ingested_jobs`; canonical schema definition from config |
| OUTPUT | Validated JobRecord documents written to `normalized_jobs` + `NormalizationComplete` event |
| SIDE EFFECT | Quarantine store entries for schema violations; field-mapping metrics |

**Error-Handling Strategy:**
- Schema violation: route to quarantine with annotated error path; do not block batch
- Ambiguous field mapping: apply best-effort heuristic; flag record with `low_confidence = true` for downstream awareness
- Currency conversion failure: store raw value, mark `currency_normalized = false`, continue
- Batch-level failure: emit `NormalizationFailed` event; Orchestrator decides whether to retry or skip

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Schema conformance rate | ≥ 99% of input records produce valid output |
| Field mapping accuracy | ≥ 97% of spot-checked records correctly mapped (human eval sample) |
| Salary normalization coverage | ≥ 90% of salary-bearing records normalized to standard unit |
| Processing latency | Median < 200ms per record; p99 < 1s |
| Quarantine rate | < 1% of volume; review triggered above 3% |

---

### 2.3 Skills Extraction Agent

*Runs NLP/LLM inference to surface structured, taxonomy-linked skills from job text.*

**Responsibilities:**
- Consume normalized JobRecord documents
- Run skill identification over title, description, requirements, and responsibilities fields
- Classify each skill into: **Technical, Domain, Soft, Certification, Tool**
- Link extracted skills to the canonical skill taxonomy using the following order (IC #15):
  1. Exact name match → internal `skills` table
  2. Normalized name match → internal `skills` table
  3. Embedding cosine similarity ≥ 0.92 → internal `skills` table
  4. O\*NET occupation code match
  5. Emit as `raw_skill` with `null` taxonomy_id — Enrichment Agent will attempt resolution
- Attach confidence score and extraction provenance (which field the skill was found in)
- Distinguish required vs. preferred skills where signal exists in the text
- Log all LLM calls to `llm_audit_log`
- Emit `SkillsExtracted` event per batch

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Normalized JobRecord documents; internal `skills` taxonomy table; model configuration |
| OUTPUT | JobRecord augmented with `skills[]` array (each: `skill_id`, `label`, `type`, `confidence`, `field_source`, `required_flag`) + `SkillsExtracted` event |
| SIDE EFFECT | Model inference logs in `llm_audit_log`; extraction confidence distribution metrics |

**Error-Handling Strategy:**
- Model inference timeout: retry once; on second failure emit record with `skills = []` and `extraction_status = failed`; do not block batch
- Low-confidence extraction (< configured threshold): flag record for downstream agents; do not discard
- Unknown skill not in taxonomy: emit as `raw_skill` with `null` taxonomy_id; Enrichment Agent will attempt resolution
- Rate-limit on LLM provider: back-off and queue; Orchestrator alerted if queue depth exceeds threshold

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Precision at taxonomy link | ≥ 92% of extracted skills correctly linked (human eval) |
| Recall (key skills) | ≥ 88% of human-labeled key skills captured |
| Taxonomy coverage | ≥ 95% of extracted skills map to a known taxonomy node |
| Avg confidence score | ≥ 0.80 across production volume |
| Inference throughput | ≥ 500 records/min at p50 |

---

### 2.4 Enrichment Agent

*Appends external market context, company data, and taxonomy metadata to every record.*

**Responsibilities:**
- Receive skill-annotated records from the Skills Extraction Agent
- Resolve `raw_skill` entries (unmapped skills) against alternative taxonomy sources
- Classify job role and seniority
- Compute quality score [0–1]: field completeness + linguistic clarity + AI keyword density + structural coherence
- Spam detection with tiered thresholds (IC #8): `spam_score` < 0.7 → proceed | 0.7–0.9 → flag for operator review (`is_spam = null`) | > 0.9 → auto-reject, do not write to `job_postings`
- Resolve `company_id` before writing to `job_postings`: match `companies` by normalized name → no match: create placeholder
- Append company-level data: industry, size band, funding stage, location hierarchy
- Attach geographic enrichment: region, metro area, remote-work classification
- Append labor-market context: BLS/ONS category, SOC/NOC code, prevailing wage band
- Compute composite enrichment quality score per record
- Write to `job_postings` only after `company_id` is resolved — never write with null `company_id`
- Emit `RecordEnriched` event per batch

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Skill-annotated JobRecord; company reference DB; taxonomy extension tables; geo lookup service |
| OUTPUT | Fully enriched JobRecord with all context fields populated + `RecordEnriched` event |
| SIDE EFFECT | Enrichment quality scores; unresolved entity log; external API call metrics |

**Error-Handling Strategy:**
- External lookup failure (company DB, geo API): store null for that field, set `enrichment_partial = true`; continue
- Unresolvable `raw_skill` after all sources exhausted: persist as-is with `resolution_status = unresolved`; log for taxonomy review queue
- Enrichment quality score below threshold: flag record; Demand Analysis and Analytics agents treat as lower-confidence input

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Company match rate | ≥ 90% of records matched to company reference |
| Geo enrichment rate | ≥ 95% of records receive valid region/metro |
| SOC/NOC code coverage | ≥ 85% of records receive a labor-market code |
| Raw skill resolution rate | ≥ 75% of previously unmapped skills resolved |
| Enrichment quality score (avg) | ≥ 0.85 |

---

### 2.5 Demand Analysis Agent

*Detects demand trends, velocity signals, and forward-looking forecasts at skill and role level.*

**Responsibilities:**
- Consume enriched records; maintain a time-series index keyed by skill, role, industry, region
- Compute demand velocity: rate-of-change in posting volume per skill/role over configurable windows (7d, 30d, 90d)
- Identify emerging skills (fast-rising velocity, low base volume) vs declining skills
- Produce supply/demand gap estimates where candidate-side data is available
- Generate short-range demand forecasts (horizon configurable, default 30 days)
- Emit `DemandSignalsUpdated` event on each analysis cycle

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Enriched JobRecord stream; historical demand time-series from data store; forecast model config |
| OUTPUT | DemandSignal documents (per skill/role/region/industry) + `DemandSignalsUpdated` event |
| SIDE EFFECT | Trend index updates; forecast model artifacts; anomaly alert events |

**Error-Handling Strategy:**
- Insufficient history for forecast: return observed trend only; set `forecast_available = false`
- Anomaly detected (spike or cliff): emit `DemandAnomaly` event to Orchestrator for possible investigation flag
- Model inference failure: fall back to naive moving average; flag signal with `degraded_model = true`

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Forecast MAPE (30-day) | < 15% on held-out validation set |
| Trend classification accuracy | ≥ 85% vs human-labeled trend ground truth |
| Signal freshness | Demand signals updated within 1h of new batch landing |
| Anomaly precision | ≥ 80% of flagged anomalies confirmed genuine by analyst review |

---

### 2.6 Analytics Agent

*Computes descriptive statistics, cohort breakdowns, and queryable aggregate datasets.*

**Responsibilities:**
- Maintain queryable aggregate tables across 6 dimensions: skill, role, industry, region, experience level, company size
- Compute salary distributions (median, p25, p75, p95) per dimension intersection
- Generate co-occurrence matrices (skills that appear together)
- Track posting lifecycle metrics: time-to-fill proxies, repost rates, posting duration
- Produce cohort-level summaries (LLM-generated weekly insights; deterministic template fallback if LLM unavailable)
- Expose a REST query interface (`POST /analytics/query`) for ad-hoc slice-and-dice requests (SA #18 — reference implementation)
- Enforce SQL guardrails on all queries: SELECT only | allowed tables only | no DDL/DML | 100-row limit | 30s timeout
- Handle dimension cardinality explosion: cap dimensions, coalesce long-tail into “Other”, emit warning

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Enriched JobRecord stream; demand signals from Demand Analysis Agent; query requests via REST |
| OUTPUT | Aggregate tables in analytics store; cohort summary documents; ad-hoc query results + `AnalyticsRefreshed` event |
| SIDE EFFECT | Index updates; query performance metrics; LLM calls logged to `llm_audit_log` |

**Error-Handling Strategy:**
- Stale data: surface staleness timestamp on every aggregate; trigger recompute if staleness exceeds SLA
- Ad-hoc query timeout: return partial result with `is_partial = true`; log for query optimization review
- Dimension cardinality explosion: enforce configurable caps; emit warning and coalesce long-tail categories into “Other”
- LLM unavailable for weekly summary: use deterministic template fallback; never block aggregate refresh

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Aggregate accuracy | ≥ 99.5% match to raw-record recount (automated audit) |
| Query p50 latency | < 500ms for standard cohort queries |
| Data freshness (aggregates) | Refreshed within 15 min of new enriched batch |
| Salary distribution coverage | ≥ 80% of role/region intersections have sufficient N for distribution |

---

### 2.7 Visualization Agent

*Renders dashboards, charts, and export artifacts from analytics and demand outputs.*

**Responsibilities:**
- Subscribe to `AnalyticsRefreshed` and `DemandSignalsUpdated` events; refresh affected views on trigger
- Render configured dashboard views: Ingestion Overview | Normalization Quality | Skill Taxonomy Coverage | Weekly Insights | Ask the Data | Operations & Alerts
- Generate exportable report artifacts: PDF summaries, CSV extracts, JSON payloads — all standard deliverables
- Support parameterized view requests from external callers (API or UI) via the Orchestrator
- Maintain a rendered-artifact cache with TTL; serve from cache when upstream data is unchanged
- Never serve a blank page — always serve stale data with a staleness warning banner
- DB connection is read-only

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | Aggregate datasets from Analytics Agent; demand signals from Demand Analysis Agent; view config + render requests |
| OUTPUT | Dashboard views (HTML/JSON); chart artifacts; export files (PDF, CSV, JSON) + `RenderComplete` event |
| SIDE EFFECT | Rendered artifact cache; render latency metrics |

**Error-Handling Strategy:**
- Upstream data unavailable: serve stale cached view with staleness warning banner; emit `VisualizationDegraded` alert
- Render failure: retry once; on second failure log `RenderFailed` event and serve placeholder with error context
- Export generation timeout: stream partial export with truncation notice; log for investigation

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Render success rate | ≥ 99.5% of triggered renders complete successfully |
| Dashboard freshness | Views refreshed within 5 min of triggering event |
| Export generation time | p95 < 10s for standard exports |
| Cache hit rate | ≥ 70% of view requests served from cache |

---

### 2.8 Orchestration Agent

*The control plane. Schedules, monitors, routes, retries, and maintains system coherence.*

**Framework:** LangGraph StateGraph [SA #13/#16 — reference implementation] + APScheduler [IC #3]
**Tracing:** LangSmith [SA #17 — reference implementation]

**Responsibilities:**
- Own the master run schedule for all agents; trigger pipeline steps in correct sequence
- Subscribe to all agent events; route messages between agents via the message bus
- Implement circuit-breaking: suspend downstream agents when upstream failure rate exceeds threshold
- Manage retry policies per agent and per error class
- Collect and expose system-wide health: per-agent status, SLA adherence, queue depths
- Handle graceful degradation: route to fallback paths when agents are unavailable
- Provide an administrative API for manual overrides, re-runs, and configuration changes
- Maintain an immutable audit log of all orchestration decisions (100% completeness required)

**Alerting Tiers:**
- **Warning:** logged + metric emitted
- **Critical:** paged to on-call
- **Fatal:** circuit broken + human escalation required

**Retry Policies:**

| Agent | Max retries | Back-off |
|-------|------------|---------|
| Ingestion (source unreachable) | 5 | Exponential + jitter |
| Normalization (batch failure) | 3 | Exponential |
| Skills Extraction (LLM timeout) | 2 per record | Fixed 2s |
| Any agent (transient DB error) | 3 | Exponential |

**Orchestration Coordination Model:**

The Orchestrator uses an event-driven choreography model within each stage, and an orchestrated saga pattern across stage boundaries:

- **Intra-stage:** agents react to events on the bus with no explicit sequencing commands
- **Stage transitions:** Orchestrator explicitly signals when a stage may begin, ensuring data consistency gates are passed
- **Failure sagas:** if a downstream agent fails mid-pipeline, Orchestrator executes a compensating flow (e.g., re-queue records at the last successful stage)

**Input / Output:**

| Direction | Description |
|-----------|-------------|
| INPUT | All agent events (`IngestBatch`, `NormalizationComplete`, `SkillsExtracted`, `RecordEnriched`, `DemandSignalsUpdated`, `AnalyticsRefreshed`, `RenderComplete`, all `*Failed` / `*Alert` events) |
| OUTPUT | Trigger commands, retry signals, circuit-break states, health reports, admin API responses, audit log entries |

**Evaluation Criteria:**

| Metric | Target |
|--------|--------|
| Pipeline end-to-end SLA | ≥ 95% of batches complete full pipeline within configured SLA window |
| Mean time to detect failure | < 60s from failure event to Orchestrator awareness |
| Mean time to recover (auto) | < 5 min for retryable failures via automated retry |
| Circuit-break precision | ≥ 90% of circuit breaks are justified (no false positives) |
| Audit log completeness | 100% of orchestration actions captured in immutable log |

---

## Message Bus & Inter-Agent Contract

All inter-agent communication is asynchronous and mediated by a central message bus. Agents never call each other directly. Each event is versioned, typed, and carries a correlation ID for end-to-end tracing.

**Phase 1 implementation:** In-process Python pub/sub (SA #14 — reference implementation). The event envelope contracts are bus-agnostic — migrating to an external bus (Kafka, RabbitMQ, Redis Streams) in Phase 2 requires changing only the transport layer, not the event definitions or agent logic.

Every event envelope carries: `event_id`, `correlation_id` (batch lineage), `agent_id`, `timestamp`, `schema_version`, `payload`.

The Orchestrator is the **only** consumer of `*Failed` and `*Alert` events — other agents do not react to each other's failures.

### Event Catalog

| Event Name | Producer | Consumer(s) |
|------------|----------|-------------|
| `IngestBatch` | Ingestion | Normalization, Orchestrator |
| `NormalizationComplete` | Normalization | Skills Extraction, Orchestrator |
| `SkillsExtracted` | Skills Extraction | Enrichment, Orchestrator |
| `RecordEnriched` | Enrichment | Demand Analysis, Analytics, Orchestrator |
| `DemandSignalsUpdated` | Demand Analysis | Analytics, Visualization, Orchestrator |
| `AnalyticsRefreshed` | Analytics | Visualization, Orchestrator |
| `RenderComplete` | Visualization | Orchestrator |
| `*Failed` / `*Alert` | Any agent | Orchestrator (exclusive) |
| `SourceFailure` | Ingestion | Orchestrator |
| `DemandAnomaly` | Demand Analysis | Orchestrator |

---

## System-Level Error-Handling Strategy

| Strategy | How It Works |
|----------|-------------|
| Dead-letter store | Records that cannot be processed after all retries are written to a quarantine store with full error context for human review |
| Exponential back-off | All retries use exponential back-off with jitter; max retry counts are per-agent and per-error-class |
| Circuit breaker | Orchestrator opens circuit when error rate > threshold for T seconds; downstream agents receive no new work until circuit resets |
| Graceful degradation | Analytics and Visualization can operate on stale data with staleness flags; pipeline does not halt for non-critical enrichment failures |
| Compensating sagas | Mid-pipeline failures trigger rollback to last successful stage checkpoint; records re-queued from there |
| Alerting tiers | **Warning:** logged + metric emitted. **Critical:** paged to on-call. **Fatal:** circuit broken + human escalation required |

---

## Directory Scaffold

```
job-intelligence-engine/
├── agents/
│   ├── ingestion/
│   │   ├── agent.py               # Agent entrypoint & lifecycle
│   │   ├── sources/               # jsearch_adapter.py, scraper_adapter.py (internal)
│   │   ├── deduplicator.py        # Fingerprint & dedup logic (internal)
│   │   └── tests/
│   ├── normalization/
│   │   ├── agent.py
│   │   ├── schema/                # Canonical JobRecord schema + validators
│   │   ├── field_mappers/         # Per-source mapping rules (internal)
│   │   └── tests/
│   ├── skills_extraction/
│   │   ├── agent.py
│   │   ├── models/                # LLM/NLP model wrappers (internal)
│   │   ├── taxonomy/              # Taxonomy reference data & linker (internal)
│   │   └── tests/
│   ├── enrichment/
│   │   ├── agent.py
│   │   ├── classifiers/           # Role, seniority, quality, spam (internal)
│   │   ├── resolvers/             # Company, geo, labor-market lookups (internal)
│   │   └── tests/
│   ├── demand_analysis/
│   │   ├── agent.py
│   │   ├── time_series/           # Index maintenance & trend math (internal)
│   │   ├── forecasting/           # Forecast model wrappers (internal)
│   │   └── tests/
│   ├── analytics/
│   │   ├── agent.py
│   │   ├── aggregators/           # Aggregate computation logic (internal)
│   │   ├── query_engine/          # REST query interface + SQL guardrails (internal)
│   │   └── tests/
│   ├── visualization/
│   │   ├── agent.py
│   │   ├── renderers/             # Chart & dashboard renderers (internal)
│   │   ├── exporters/             # PDF, CSV, JSON export (internal)
│   │   └── tests/
│   └── orchestration/
│       ├── agent.py
│       ├── scheduler/             # APScheduler — run-schedule management (internal)
│       ├── circuit_breaker/       # Circuit-break logic (internal)
│       ├── saga/                  # Compensating saga definitions (internal)
│       ├── admin_api/             # Admin REST interface (internal)
│       └── tests/
├── common/
│   ├── events/                    # Typed event definitions & versioning
│   ├── message_bus/               # Bus client abstraction (in-process Phase 1)
│   ├── llm_adapter.py             # Provider-agnostic adapter [SA #11]
│   ├── data_store/                # Storage client abstraction
│   ├── config/                    # Config schema & loaders
│   ├── observability/             # structlog, metrics, tracing helpers [SA #17]
│   └── errors/                    # Shared error types & dead-letter utilities
├── platform/
│   ├── infrastructure/            # IaC definitions (cloud resources)
│   ├── ci_cd/                     # Pipeline definitions
│   ├── monitoring/                # Dashboards & alert rules
│   └── runbooks/                  # Operational runbooks per agent
├── data/
│   ├── staging/                   # Ingestion staging area
│   ├── normalized/                # Post-normalization records
│   ├── enriched/                  # Fully enriched records
│   ├── analytics/                 # Aggregate tables
│   ├── demand_signals/            # Trend & forecast outputs
│   ├── rendered/                  # Visualization artifact cache
│   └── dead_letter/               # Quarantined records
├── docs/
│   ├── architecture/              # This document and subsequent revisions
│   ├── api/                       # Agent & admin API contracts
│   └── adr/                       # Architecture Decision Records
└── README.md
```

---

## Design Decisions (IC/SA/D Classification)

This table cross-references all decisions from `ARCHITECTURAL_DECISIONS.md`. See that file for full evaluation criteria and alternative options. **SA decisions show the reference implementation — not the final answer.** Teams produce ADRs for all SA decisions before implementing the affected agents.

| # | Decision | Type | Reference Implementation |
|---|----------|------|--------------------------|
| 3 | Batch vs real-time | IC | **Batch-first** — APScheduler, daily cron default (`0 2 * * *`) |
| 4 | Source of truth for ingested jobs | IC | **Staging tables + promotion** — `raw_ingested_jobs` → `normalized_jobs` → `job_postings` |
| 8 | Spam threshold policy | IC | **Tiered** — flag at 0.7, auto-reject above 0.9 |
| 9 | Dedup source priority | IC | **JSearch wins over scraped** when same job appears in both |
| 11 | LLM provider policy | **SA** | **Provider-agnostic adapter** — Azure OpenAI default, switchable via `LLM_PROVIDER` |
| 12 | Scraping tool | **SA** | **Crawl4AI** + **httpx** for JSearch API |
| 13 | Multi-agent framework | **SA** | **LangGraph** StateGraph |
| 14 | Message bus | **SA** | **In-process Python events** (Phase 1); external bus upgrade path for Phase 2 |
| 15 | Skill taxonomy | IC | **Internal watechcoalition taxonomy primary** (`skills` table); O\*NET fallback |
| 16 | Orchestration engine | **SA** | **LangGraph StateGraph** (consistent with #13) |
| 17 | Agent tracing | **SA** | **LangSmith** — native LangGraph integration |
| 18 | Analytics query interface | **SA** | **REST** — `POST /analytics/query` |
| 19 | Database engine | IC | **MSSQL** — stay on existing watechcoalition instance |
| 20 | Enrichment phase split | IC | **Lite (Phase 1) + Full (Phase 2)** — external data sources not available in curriculum |
| 21 | PDF export scope | IC | **Standard deliverable** — not a stretch goal |

### Deferred (D)

| # | Decision | Recommendation |
|---|----------|----------------|
| 22 | Multi-tenancy | Single shared pipeline for Phase 1; revisit before any Phase 2 multi-org work |
| 23 | Feedback loop agent | Defer to Phase 2; requires ground truth source, training pipeline, and model versioning strategy |
