# Architecture orientation — Job Intelligence Engine

**Audience:** New engineers, onboarding.  
**Source:** Derived from `watechcoalition/docs/planning/ARCHITECTURE_DEEP.md`.  
**Purpose:** Quick reference for what each agent does, how it is triggered, and how it fits into the event pipeline.

---

## How agents communicate

- **Agents communicate via typed, versioned events only.** Direct function or RPC calls between agents are forbidden.
- Every event uses the canonical envelope: `event_id`, `correlation_id`, `agent_id`, `timestamp`, `schema_version`, `payload`.
- The **Orchestration Agent** is the sole consumer of `*Failed` and `*Alert` events. No other agent reacts to another agent’s failures.
- No agent writes to another agent’s internal state. Data flows only through events and through shared, agent-owned persistence (e.g. Ingestion → `raw_ingested_jobs`, Normalization → `normalized_jobs`, Enrichment → `job_postings`).

---

## The 8 agents

### 1. Ingestion Agent

**What it does:**  
Polls JSearch via HTTP and scrapes target URLs via Crawl4AI. For each job it computes a fingerprint (e.g. `sha256(source + external_id + title + company + date_posted)`), deduplicates against `raw_ingested_jobs` by `raw_payload_hash`, and discards duplicates while tracking counts. When the same job appears from both JSearch and a scraper, JSearch wins. It attaches provenance: `source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`, and writes only new records to `raw_ingested_jobs`. On source unreachability it retries with back-off and, after max retries, emits `SourceFailure` to the Orchestrator.

**Deterministic / LLM:** Deterministic (no LLM; rules, hashing, dedup).

**Emits:** `IngestBatch`, `SourceFailure` (on unreachable source after retries).

**Consumes:** None (triggered by schedule or Orchestrator).

**Phase 1 vs Phase 2:** Phase 1: full implementation. Phase 2: no change to this agent.

---

### 2. Normalization Agent

**What it does:**  
Consumes `IngestBatch` and maps source-specific fields into the canonical `JobRecord` via per-source field mappers. It standardizes dates (ISO 8601), salaries (min/max/currency/period), locations, and employment types; strips HTML, normalizes whitespace, and sanitizes free-text. It validates each record against the Pydantic schema and quarantines violations with an annotated error path. Successful records are written to `normalized_jobs`. On batch-level failure it emits `NormalizationFailed` to the Orchestrator.

**Deterministic / LLM:** Deterministic (mapping and validation only; no LLM).

**Emits:** `NormalizationComplete`, `NormalizationFailed`.

**Consumes:** `IngestBatch`.

**Phase 1 vs Phase 2:** Phase 1: full implementation. Phase 2: no change to this agent.

---

### 3. Skills Extraction Agent

**What it does:**  
Takes normalized `JobRecord`s and runs LLM inference over `title`, `description`, `requirements`, and `responsibilities` to produce a list of `SkillRecord`s (label, type, confidence, field_source, required_flag). It links skills to the taxonomy in order: exact name match, normalized name match, embedding similarity ≥ 0.92, O*NET occupation code; if no match is found it emits the skill as `raw_skill` (null taxonomy ID) for later resolution. All LLM calls are logged to `llm_audit_log`. On LLM timeout it retries once, then continues with empty skills and `extraction_status = "failed"`.

**Deterministic / LLM:** LLM-required (core responsibility is LLM-based skill extraction).

**Emits:** `SkillsExtracted`.

**Consumes:** `NormalizationComplete`.

**Phase 1 vs Phase 2:** Phase 1: full implementation including taxonomy linking and `raw_skill` emission. Phase 2: resolution of `raw_skill` is done in Enrichment; this agent’s contract stays the same.

---

### 4. Enrichment Agent

**What it does:**  
Consumes `SkillsExtracted` and classifies job role and seniority, computes a quality score (completeness, clarity, structure), and runs spam detection (below threshold proceed; mid range flag for review; above threshold auto-reject and do not write to `job_postings`). It resolves `company_id` from the `companies` table (or creates a placeholder), resolves `location_id` from `company_addresses` where possible, and maps `sector_id` to `industry_sectors`. It writes to `job_postings` only after `company_id` is resolved, then emits `RecordEnriched`. Phase 2 adds company/geo/labor-market resolvers, raw-skill resolution, and composite enrichment quality.

**Deterministic / LLM:** LLM-optional (Phase 1 classifiers and scoring may be rule-based or LLM; Phase 2 resolvers may use external APIs or LLM).

**Emits:** `RecordEnriched`.

**Consumes:** `SkillsExtracted`.

**Phase 1 vs Phase 2:** Phase 1: “lite” — role/seniority/quality/spam, company_id, location_id, sector_id, write to `job_postings`. Phase 2: full — company/geo/labor-market data, raw_skill resolution, enrichment_quality_score, etc.

---

### 5. Analytics Agent

**What it does:**  
Consumes `RecordEnriched` and maintains aggregates across dimensions (skill, role, industry, region, experience level, company size), salary distributions (e.g. median, p25, p75, p95), and co-occurrence matrices. It tracks posting lifecycle metrics and produces weekly insight summaries (LLM-generated with template fallback). It exposes a text-to-SQL Q&A endpoint with strict guardrails (SELECT-only, allowlisted tables, row limit, timeout). All attempts are logged to `llm_audit_log`. It emits `AnalyticsRefreshed` when aggregates are updated.

**Deterministic / LLM:** LLM-optional (aggregates are deterministic; weekly insights and text-to-SQL use LLM with fallbacks).

**Emits:** `AnalyticsRefreshed`.

**Consumes:** `RecordEnriched`.

**Phase 1 vs Phase 2:** Phase 1: full implementation (aggregates, weekly insights, Ask the Data). Phase 2: may consume demand signals; no structural change to this agent’s core responsibilities.

---

### 6. Visualization Agent

**What it does:**  
Consumes `AnalyticsRefreshed` (and in Phase 2, `DemandSignalsUpdated`) and serves dashboard pages: Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, and Operations & Alerts. It provides exports (PDF, CSV, JSON) and uses a TTL-based cache. It reads only from the DB (SQLAlchemy); it never writes pipeline state. On upstream unavailability it serves stale data with a banner and emits `VisualizationDegraded`. On render failure it retries once, then emits `RenderFailed` and shows a placeholder.

**Deterministic / LLM:** Deterministic (renders and exports precomputed data; no LLM in this agent).

**Emits:** `RenderComplete`, `RenderFailed`, `VisualizationDegraded`.

**Consumes:** `AnalyticsRefreshed`, `DemandSignalsUpdated` (Phase 2).

**Phase 1 vs Phase 2:** Phase 1: full dashboard and exports. Phase 2: also consumes `DemandSignalsUpdated` for demand-related views.

---

### 7. Orchestration Agent

**What it does:**  
Owns the master run schedule (e.g. cron) and triggers pipeline steps in sequence. It uses a LangGraph StateGraph to route events between agents and applies retry policies (exponential back-off + jitter) per agent and error type. It is the sole consumer of all `*Failed` and `*Alert` events and maintains a structured JSON audit log and system-wide health monitoring. Phase 2 adds circuit-breaking, saga-style checkpoints and compensating flows, and an admin API for overrides and re-runs.

**Deterministic / LLM:** Deterministic (scheduling and event routing; no LLM).

**Emits:** (No domain events in the event catalog; it triggers the pipeline and may emit internal/operational signals.)

**Consumes:** All `*Failed` and `*Alert` events; also observes or coordinates on `IngestBatch`, `NormalizationComplete`, `SkillsExtracted`, `RecordEnriched`, `AnalyticsRefreshed`, `RenderComplete`, `SourceFailure`, and in Phase 2 `DemandSignalsUpdated`, `DemandAnomaly`.

**Phase 1 vs Phase 2:** Phase 1: basic — schedule, LangGraph routing, retries, alert handling, health, audit log. Phase 2: circuit breaker, saga pattern, admin API.

---

### 8. Demand Analysis Agent (Phase 2 only)

**What it does:**  
Consumes `RecordEnriched` and builds time-series indices by skill, role, industry, and region with velocity windows (e.g. 7d, 30d, 90d). It identifies emerging vs declining skills, estimates supply/demand gaps where data exists, and produces configurable-horizon demand forecasts. It emits `DemandSignalsUpdated` and, on detected spikes or cliffs, `DemandAnomaly`. In Phase 1 this agent is scaffold-only (no implementation).

**Deterministic / LLM:** LLM-optional or deterministic (forecasting and trend logic may be statistical; no LLM specified in the spec).

**Emits:** `DemandSignalsUpdated`, `DemandAnomaly`.

**Consumes:** `RecordEnriched`.

**Phase 1 vs Phase 2:** Phase 1: directory and placeholder only; no events consumed or produced. Phase 2: full implementation.

---

## End-to-end event flow (single job posting)

For one job posting, the flow is:

1. **Orchestrator** runs the schedule and triggers ingestion (no event consumed for “start”; schedule or internal trigger).
2. **Ingestion** fetches/scrapes data, deduplicates, and writes new rows to `raw_ingested_jobs`, then emits **`IngestBatch`** (payload includes the raw job(s)).
3. **Normalization** consumes **`IngestBatch`**, maps to `JobRecord`, validates, writes to `normalized_jobs`, and emits **`NormalizationComplete`**.
4. **Skills Extraction** consumes **`NormalizationComplete`**, runs LLM extraction and taxonomy linking, and emits **`SkillsExtracted`** (JobRecord + skills).
5. **Enrichment** consumes **`SkillsExtracted`**, classifies, scores, resolves company/location/sector, writes to `job_postings`, and emits **`RecordEnriched`**.
6. **Analytics** consumes **`RecordEnriched`**, refreshes aggregates (and optionally runs weekly insights / text-to-SQL), and emits **`AnalyticsRefreshed`**.
7. **Visualization** consumes **`AnalyticsRefreshed`** (and in Phase 2, **`DemandSignalsUpdated`**), renders dashboard and exports, and emits **`RenderComplete`**.

At any step, if the agent fails after retries, it emits a `*Failed` or `*Alert` event; **only the Orchestration Agent** consumes those and handles retries, alerting, and audit.

In **Phase 2**, **Demand Analysis** also consumes **`RecordEnriched`**, produces **`DemandSignalsUpdated`** and **`DemandAnomaly`**; Visualization then consumes **`DemandSignalsUpdated`** for demand-related views.

---

## Event catalog (quick reference)

| Event                   | Producer        | Consumers                          |
|-------------------------|-----------------|------------------------------------|
| `IngestBatch`           | Ingestion       | Normalization, Orchestrator        |
| `NormalizationComplete` | Normalization   | Skills Extraction, Orchestrator    |
| `SkillsExtracted`       | Skills Extraction | Enrichment, Orchestrator        |
| `RecordEnriched`        | Enrichment      | Analytics, Demand Analysis (P2), Orchestrator |
| `DemandSignalsUpdated`  | Demand Analysis (P2) | Visualization, Orchestrator   |
| `AnalyticsRefreshed`    | Analytics       | Visualization, Orchestrator       |
| `RenderComplete`        | Visualization   | Orchestrator                       |
| `*Failed` / `*Alert`    | Any agent       | **Orchestrator only**              |
| `SourceFailure`         | Ingestion       | Orchestrator                       |
| `DemandAnomaly`         | Demand Analysis (P2) | Orchestrator                  |
