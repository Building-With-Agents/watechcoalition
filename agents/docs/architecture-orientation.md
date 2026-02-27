# Job Intelligence Engine — Architecture Orientation

**Audience:** Engineers onboarding to the agents pipeline  
**Purpose:** High-level orientation guide for the eight-agent Job Intelligence Engine

---

## Overview

The Job Intelligence Engine is an eight-agent Python pipeline that ingests, normalizes, enriches, and analyzes external job postings for the watechcoalition platform. It runs alongside the existing Next.js/MSSQL application and writes enriched jobs into `job_postings` via SQLAlchemy. All agents are orchestrated via events; there is no direct invocation between agents.

---

## Communication Protocol

**Agents communicate only via typed, versioned events.** Direct function calls between agents are strictly forbidden. Every inter-agent message flows through the message bus as an `AgentEvent` with `event_id`, `correlation_id`, `agent_id`, `timestamp`, `schema_version`, and `payload`.

**The Orchestration Agent is the sole consumer of `*Failed` and `*Alert` events.** No other agent reacts to another agent's failures. When an agent emits `SourceFailure`, `NormalizationFailed`, or any `*Alert`, only the Orchestration Agent processes it. This keeps failure handling centralized and prevents cascading reactions.

---

## Phase Boundary

| Phase | Scope |
|-------|-------|
| **Phase 1** | Core pipeline implementation: Ingestion, Normalization, Skills Extraction, Enrichment (lite), Analytics, Visualization, Orchestration (basic scheduling, retries, audit). In-process message bus, SQLAlchemy to MSSQL, Streamlit dashboard. |
| **Phase 2** | Advanced features: full enrichment (company/geo/labor-market resolvers, raw_skill resolution), Demand Analysis agent, circuit breaker, saga patterns, compensating flows, admin API, external message bus, `demand_signals` and related metrics. |

Phase 2 items are scaffolded in the codebase but **must not be implemented** during Phase 1 unless explicitly instructed.

---

## Agent Summaries

### 1. Ingestion Agent

Ingests raw job postings from JSearch (via httpx) and web scraping (via Crawl4AI). Fingerprints each record, deduplicates against `raw_ingested_jobs`, and stages to `raw_ingested_jobs`. JSearch wins over scraped when the same job appears in both sources. Emits `IngestBatch` for downstream processing. On source failure, uses exponential back-off (max 5 retries) and emits `SourceFailure` to the Orchestrator.

- **Emits:** `IngestBatch`
- **Writes to:** `raw_ingested_jobs`
- **Phase 2:** None — fully Phase 1

---

### 2. Normalization Agent

Consumes `IngestBatch` and maps source-specific fields into the canonical `JobRecord` schema. Standardizes dates (ISO 8601), salaries (min/max/currency/period), locations, and employment types. Validates against Pydantic; quarantines violations. Emits `NormalizationComplete` for downstream agents. On batch failure, emits `NormalizationFailed` to the Orchestrator.

- **Consumes:** `IngestBatch`
- **Emits:** `NormalizationComplete`
- **Writes to:** `normalized_jobs`
- **Phase 2:** None — fully Phase 1

---

### 3. Skills Extraction Agent

Consumes `NormalizationComplete` and uses LLM inference to extract skills from title, description, requirements, and responsibilities. Produces `SkillRecord` entries with label, type, confidence, field_source, and required_flag. Links to the taxonomy via exact match, normalized match, or embedding similarity; unresolved skills are emitted as `raw_skill` (null taxonomy ID) for Enrichment to resolve in Phase 2. Emits `SkillsExtracted`. All LLM calls are logged to `llm_audit_log`.

- **Consumes:** `NormalizationComplete`
- **Emits:** `SkillsExtracted`
- **Phase 2:** Raw-skill resolution is deferred to Enrichment (Phase 2); the agent itself is Phase 1

---

### 4. Enrichment Agent

Consumes `SkillsExtracted` and classifies role, seniority, quality score, and spam. Resolves `company_id` and `location_id`, maps `sector_id`, and writes to `job_postings` only after `company_id` is resolved. Spam thresholds: &lt;0.7 proceed, 0.7–0.9 flag for review, &gt;0.9 auto-reject. Emits `RecordEnriched`.

- **Consumes:** `SkillsExtracted`
- **Emits:** `RecordEnriched`
- **Writes to:** `job_postings`
- **Phase 2:** Full enrichment: company/industry/size/funding, region/metro/remote classification, SOC/NOC codes, prevailing wage, raw_skill resolution. The `resolvers/` subdirectory (company, geo, labor-market lookups) is Phase 2 only.

---

### 5. Analytics Agent

Consumes `RecordEnriched` and computes aggregates across skill, role, industry, region, experience level, and company size. Produces salary distributions, co-occurrence matrices, and posting lifecycle metrics. Exposes `POST /analytics/query` for text-to-SQL with strict guardrails (SELECT only, allowed tables, 100-row limit, 30s timeout). Generates weekly insight summaries (LLM or template fallback). Emits `AnalyticsRefreshed`.

- **Consumes:** `RecordEnriched`
- **Emits:** `AnalyticsRefreshed`
- **Exposes:** `POST /analytics/query`
- **Phase 2:** None — fully Phase 1

---

### 6. Visualization Agent

Consumes `AnalyticsRefreshed` (and `DemandSignalsUpdated` in Phase 2). Renders Streamlit dashboard pages (Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts) and exports PDF, CSV, JSON. Uses a read-only SQLAlchemy connection and TTL cache; serves stale data with a banner when upstream is unavailable, never a blank page. Emits `RenderComplete`.

- **Consumes:** `AnalyticsRefreshed`; `DemandSignalsUpdated` (Phase 2)
- **Emits:** `RenderComplete`
- **Phase 2:** Consumption of `DemandSignalsUpdated`; no other Phase 2 restrictions

---

### 7. Orchestration Agent

Master scheduler using LangGraph StateGraph and APScheduler. Triggers pipeline steps in sequence and routes events. Enforces retry policies with exponential back-off and jitter. **Sole consumer of all `*Failed` and `*Alert` events.** Maintains a structured audit log with 100% completeness. Alerting tiers: Warning (log + metric), Critical (page on-call), Fatal (circuit broken + escalation).

- **Consumes:** All pipeline events; exclusively `*Failed` and `*Alert`
- **Emits:** Trigger/retry signals to agents
- **Phase 2:** Circuit breaker, saga pattern, compensating flows, admin API — all in `circuit_breaker/`, `saga/`, `admin_api/` (Phase 2 only)

---

### 8. Demand Analysis Agent

**Phase 2 only — scaffold directory in Phase 1; do not implement.** Consumes `RecordEnriched` and produces time-series demand signals by skill, role, industry, region. Identifies emerging vs declining skills, supply/demand gaps, and 30-day forecasts. Emits `DemandSignalsUpdated` and `DemandAnomaly` on spikes or cliffs.

- **Consumes:** `RecordEnriched`
- **Emits:** `DemandSignalsUpdated`, `DemandAnomaly`
- **Phase 2:** Entire agent is Phase 2; scaffold only in Phase 1

---

## Event Flow Summary

```
Ingestion → IngestBatch → Normalization → NormalizationComplete → Skills Extraction
  → SkillsExtracted → Enrichment → RecordEnriched → Analytics → AnalyticsRefreshed
  → Visualization → RenderComplete

RecordEnriched → Demand Analysis (Phase 2) → DemandSignalsUpdated → Visualization / Orchestrator

*Failed / *Alert → Orchestration only (no other consumer)
```

---

## Scope Accuracy Reference

| Agent | Phase 1 Scope | Phase 2 Scope |
|-------|---------------|---------------|
| Ingestion | Full | — |
| Normalization | Full | — |
| Skills Extraction | Full (raw_skill emitted, not resolved) | — |
| Enrichment | Lite: role, seniority, quality, spam, company_id, location_id, sector_id | resolvers/ (company, geo, labor-market), SOC/NOC, prevailing wage, raw_skill resolution |
| Analytics | Full | — |
| Visualization | Full (except DemandSignalsUpdated) | Consume DemandSignalsUpdated |
| Orchestration | Basic: scheduling, retries, audit, alerting | circuit_breaker/, saga/, admin_api/ |
| Demand Analysis | Scaffold only | Full implementation |
