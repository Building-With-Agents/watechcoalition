## Job Intelligence Engine — Architecture Orientation (Phase 1 / Phase 2)

This document is a quick orientation for implementing engineers. It summarizes the eight-agent pipeline, the canonical event flow, and the Phase 1 vs Phase 2 boundary. Agents communicate **only** through typed events, and the `correlation_id` is propagated end-to-end beginning with `IngestBatch`.

## Agent summaries (what, events, determinism, phase boundary)

### Ingestion Agent
The Ingestion Agent collects raw job postings from external sources (JSearch via HTTP and web pages via Crawl4AI) and stages them for downstream processing. It emits **`IngestBatch`** and does not consume upstream pipeline events. It is **deterministic** (no LLM) and performs **deduplication inside the agent** (deduplication is not a separate agent). Phase 1 includes source polling/scraping, fingerprinting, and staging; Phase 2 adds no new ingestion responsibilities (the Phase 2 work is elsewhere, e.g., orchestration hardening and demand analysis).

### Normalization Agent
The Normalization Agent converts raw ingested payloads into the canonical `JobRecord` shape and quarantines schema violations. It consumes **`IngestBatch`** and emits **`NormalizationComplete`**. It is **deterministic** (no LLM): field mapping, standardization (dates/salary/location/employment type), HTML stripping, and schema validation are rule-based. Phase 1 implements the full normalization boundary; Phase 2 does not change the contract, but may add additional normalized fields only if the canonical schema evolves with a versioned event change.

### Skills Extraction Agent
The Skills Extraction Agent extracts and links skills from normalized job text into `SkillRecord` entries suitable for analytics and enrichment. It consumes **`NormalizationComplete`** and emits **`SkillsExtracted`**. This agent is **LLM-required** in Phase 1 because skill extraction is defined as LLM inference with a fallback behavior (continue batch even if extraction fails). Phase 2 may improve taxonomy resolution and linking depth, but the event boundary remains `SkillsExtracted` into enrichment.

### Enrichment Agent
The Enrichment Agent applies "enrichment-lite" in Phase 1 (role/seniority classification, quality scoring, spam scoring) and is responsible for **persistence to the canonical `job_postings` table** (there is no Storage Agent). It consumes **`SkillsExtracted`** and emits **`RecordEnriched`**. In Phase 1 it is **deterministic / LLM-optional** (the scoring and classifiers can be implemented without an LLM), and it must resolve `company_id` before writing to `job_postings`. Phase 2 expands enrichment to external resolvers and deeper company/geo/labor-market augmentation, but still emits `RecordEnriched` as the downstream trigger.

### Analytics Agent
The Analytics Agent computes aggregates and query-ready views over enriched records (dimensions like skill, role, industry, region, etc.) and refreshes analytics artifacts for dashboards and exports. It consumes **`RecordEnriched`** and emits **`AnalyticsRefreshed`**. It is **LLM-optional** in Phase 1: aggregate computation is deterministic, while "weekly insight summaries" and text-to-SQL assistance can use an LLM with strict guardrails and a deterministic fallback. Phase 2 may incorporate demand signals (when available) and additional derived metrics, but the Phase 1 contract remains: `RecordEnriched` → `AnalyticsRefreshed`.

### Visualization Agent
The Visualization Agent renders dashboards and exports from analytics outputs with a read-only database connection and a TTL cache (serve stale with a banner; never blank). It consumes **`AnalyticsRefreshed`** (and, in Phase 2, also consumes **`DemandSignalsUpdated`**) and emits **`RenderComplete`**. It is **deterministic** (no LLM) in Phase 1; any narrative content is sourced from Analytics outputs (which may be LLM-generated but has a fallback). Phase 1 includes Streamlit dashboards plus PDF/CSV/JSON exports; Phase 2 adds demand-signal visualizations without changing the Phase 1 rendering contract.

### Orchestration Agent
The Orchestration Agent schedules, routes, retries, and monitors the pipeline using LangGraph + APScheduler, and it maintains a complete audit trail of orchestration decisions. It consumes the normal pipeline events (`IngestBatch`, `NormalizationComplete`, `SkillsExtracted`, `RecordEnriched`, `AnalyticsRefreshed`, `RenderComplete`, and in Phase 2 also `DemandSignalsUpdated`) to track progress and system health. **It is the SOLE consumer of all `*Failed` and `*Alert` events** — no other agent reacts to failures — so failure handling and escalation live only here. It is **deterministic** in Phase 1; Phase 2 adds circuit breaker, saga/compensating flows, and admin controls without changing the other agents' event contracts.

### Demand Analysis Agent (Phase 2 only)
The Demand Analysis Agent is a Phase 2 component that computes time-series demand signals (trends, velocity windows, forecasts) from enriched records. It consumes **`RecordEnriched`** and emits **`DemandSignalsUpdated`**, and it emits **`DemandAnomaly`** when spikes or cliffs are detected. Phase 1 must **only scaffold** this agent (no implementation); the first functional demand outputs begin in Phase 2.

## End-to-end event flow (single job posting)

For a single job posting, the canonical Phase 1 flow is:

- **Ingestion Agent** stages raw data and emits **`IngestBatch`**
- **Normalization Agent** consumes `IngestBatch`, produces canonical records, emits **`NormalizationComplete`**
- **Skills Extraction Agent** consumes `NormalizationComplete`, extracts skills, emits **`SkillsExtracted`**
- **Enrichment Agent** consumes `SkillsExtracted`, scores/classifies, persists to `job_postings`, emits **`RecordEnriched`**
- **Analytics Agent** consumes `RecordEnriched`, refreshes aggregates, emits **`AnalyticsRefreshed`**
- **Visualization Agent** consumes `AnalyticsRefreshed`, renders dashboards/exports, emits **`RenderComplete`**

In Phase 2, **Demand Analysis Agent** also consumes `RecordEnriched` and emits **`DemandSignalsUpdated`** (and **`DemandAnomaly`**), which may be consumed by Visualization (and tracked by Orchestration) alongside the Phase 1 analytics refresh.

## Phase boundary summary (what changes in Phase 2)

- **Phase 1 (implement now)**: Ingestion → Normalization → Skills Extraction → Enrichment-lite (and persistence) → Analytics → Visualization, all scheduled/monitored by Orchestration.
- **Phase 2 (do not implement in Phase 1 unless instructed)**: Demand Analysis (signals + anomalies), Orchestration circuit breaker/saga/admin controls, and Enrichment "full" resolvers (company/geo/labor-market) beyond the Phase 1 lite classifiers.
- **Invariant rule across both phases**: events are the only coupling, event names are stable and versioned, and **Orchestration remains the sole consumer of all `*Failed` and `*Alert` events**.

---

*Reviewed against `ARCHITECTURE_DEEP.md`. The only correction made was to the Demand Analysis Agent — Cursor described it as "deterministic / statistical" but the spec doesn't classify its determinism since it's Phase 2 only and never implemented in Phase 1, so that label was removed.*
