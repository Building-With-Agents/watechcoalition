# Architecture Orientation — Job Intelligence Engine

Short reference for what each agent does, how they communicate, and the Phase 1 vs Phase 2 boundary.

---

## How Agents Communicate

**Agents communicate only via typed, versioned events.** There are no direct function calls between agents. Every inter-agent message is an `AgentEvent` (event_id, correlation_id, agent_id, timestamp, schema_version, payload) published to the in-process message bus. The pipeline is: Ingestion → Normalization → Skills Extraction → Enrichment → Analytics → Visualization; each step consumes the previous agent’s output event and emits the next. **Critical constraint: the Orchestration Agent is the sole consumer of all `*Failed` and `*Alert` events.** No other agent subscribes to or reacts to another agent’s failures or alerts.

---

## Per-Agent Summary

### Ingestion Agent
Pulls job postings from external sources (JSearch API via httpx, web scraping via Crawl4AI), deduplicates by fingerprint (source + external_id + title + company + date_posted), and stages records into `raw_ingested_jobs`. JSearch wins over scraped when the same job appears in both. It emits `IngestBatch` for the Normalization Agent and, on source unreachable after retries, `SourceFailure` to the Orchestrator only.

### Normalization Agent
Consumes `IngestBatch`, maps source-specific fields to the canonical `JobRecord` schema via per-source field mappers, and standardizes dates (ISO 8601), salaries, locations, and employment types. It validates with Pydantic, quarantines schema violations, and writes to `normalized_jobs`. It emits `NormalizationComplete` downstream and `NormalizationFailed` to the Orchestrator on batch failure.

### Skills Extraction Agent
Consumes `NormalizationComplete`, runs LLM-based extraction over title/description/requirements to produce `SkillRecord` entries with taxonomy linking (exact → normalized → embedding similarity ≥ 0.92 → O*NET → raw_skill). All LLM calls are logged to `llm_audit_log`. It emits `SkillsExtracted` to Enrichment and `SkillsExtractionFailed` to the Orchestrator on failure.

### Enrichment Agent (Phase 1 lite)
Consumes `SkillsExtracted`, classifies role and seniority, computes quality and spam scores, and resolves `company_id` (and optionally location) before writing to `job_postings`. Spam: < 0.7 proceed, 0.7–0.9 flag for review, > 0.9 auto-reject (no write). It emits `RecordEnriched` and, on failure, `EnrichmentFailed` to the Orchestrator only.

### Analytics Agent
Consumes `RecordEnriched`, builds aggregates (skill, role, industry, region, experience, company size), salary distributions, co-occurrence matrices, and posting lifecycle metrics. It offers weekly LLM summaries (with template fallback) and a text-to-SQL “Ask the Data” interface with strict guardrails (SELECT only, allowlist, row/time limits). It emits `AnalyticsRefreshed` and `AnalyticsFailed` to the Orchestrator.

### Visualization Agent
Consumes `AnalyticsRefreshed`, serves the Streamlit dashboards (Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts) and generates PDF/CSV/JSON exports. It uses a read-only DB connection and TTL cache; stale data is shown with a banner and `VisualizationDegraded`/`RenderFailed` sent only to the Orchestrator.

### Orchestration Agent
Schedules the pipeline (e.g. APScheduler), routes events via LangGraph StateGraph, and applies retry/back-off policies. **It is the sole consumer of all `*Failed` and `*Alert` events** (e.g. `SourceFailure`, `NormalizationFailed`, `SkillsExtractionFailed`, `EnrichmentFailed`, `AnalyticsFailed`, `RenderFailed`, `VisualizationDegraded`, `Alert`). No other agent handles these. It maintains the orchestration audit log (100% completeness), monitors health, and implements alerting tiers (Warning, Critical, Fatal).

### Demand Analysis Agent (Phase 2 only)
Scaffolded but not implemented in Phase 1. Would consume `RecordEnriched`, produce time-series and demand signals, and emit `DemandSignalsUpdated` and `DemandAnomaly`. Phase 1 does not implement this agent.

---

## Phase 1 vs Phase 2 Boundary

**Phase 1 (implemented):** Ingestion, Normalization, Skills Extraction, Enrichment (lite), Analytics, Visualization, Orchestration. In-process Python pub/sub message bus. Enrichment resolvers are lite (company/location match, sector mapping); no full company/geo/labor-market lookups. Orchestration has no circuit-breaker, saga, or admin API.

**Phase 2 (scaffold only — do not implement unless instructed):** Demand Analysis agent; circuit_breaker, saga, admin_api under orchestration; full enrichment resolvers (company/geo/labor-market); external message bus; demand_signals and related tables.

---

## Critical Constraint

**The Orchestration Agent is the sole consumer of `*Failed` and `*Alert` events.** No other agent may subscribe to or react to `SourceFailure`, `NormalizationFailed`, `SkillsExtractionFailed`, `EnrichmentFailed`, `AnalyticsFailed`, `RenderFailed`, `VisualizationDegraded`, or `Alert`. This keeps failure and alert handling centralized and avoids cross-agent coupling.
