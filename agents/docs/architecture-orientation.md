# Architecture Orientation

Agents communicate via typed, versioned events only; direct function calls between agents are forbidden. This document summarizes each agent, its event boundaries, and Phase 1 vs Phase 2 scope. Event names match the Event Catalog in `docs/planning/ARCHITECTURE_DEEP.md`; only events listed there are used (e.g. `NormalizationFailed`, `RenderFailed`, `VisualizationDegraded` are instances of `*Failed` / `*Alert`, not separate catalog events).

---

## Ingestion Agent

**Classification:** Deterministic. **Consumes:** — **Emits:** `IngestBatch`, `SourceFailure`

The pipeline entry point. Polls JSearch via httpx and scrapes via Crawl4AI, fingerprints and deduplicates, and stages to `raw_ingested_jobs`. JSearch wins over scraped when the same job appears in both. Phase 1: full implementation. Phase 2: no additional responsibilities.

---

## Normalization Agent

**Classification:** Deterministic. **Consumes:** `IngestBatch` **Emits:** `NormalizationComplete`

Maps source fields to the canonical JobRecord via per-source mappers, standardizes dates and salaries, and quarantines schema violations. Writes to `normalized_jobs`. Phase 1: full implementation. Phase 2: no additional responsibilities.

---

## Skills Extraction Agent

**Classification:** LLM-required. **Consumes:** `NormalizationComplete` **Emits:** `SkillsExtracted`

Uses LLM inference over title, description, requirements, and responsibilities to produce SkillRecords. Links skills to taxonomy (exact → normalized → embedding → O*NET → raw_skill) and logs all LLM calls to `llm_audit_log`. Phase 1: full implementation. Phase 2: no additional responsibilities.

---

## Enrichment Agent

**Classification:** LLM-optional. **Consumes:** `SkillsExtracted` **Emits:** `RecordEnriched`

Classifies role and seniority, computes quality and spam scores, and resolves `company_id` and `location_id`. Writes to `job_postings` only after `company_id` is resolved. Phase 1: lite (classifiers, quality, spam, company/location resolution, sector mapping). Phase 2: raw_skill resolution, company/geo/labor-market enrichment, composite quality score.

---

## Analytics Agent

**Classification:** LLM-optional. **Consumes:** `RecordEnriched`; in Phase 2 also `DemandSignalsUpdated`. **Emits:** `AnalyticsRefreshed`

Aggregates across skill, role, industry, region, experience, and company size. Produces salary distributions, co-occurrence matrices, posting lifecycle metrics, weekly insight summaries (LLM or template fallback), and text-to-SQL Q&A with guardrails. Phase 1: full implementation (consumes only `RecordEnriched`). Phase 2: also consumes `DemandSignalsUpdated` per Event Catalog.

---

## Visualization Agent

**Classification:** Deterministic. **Consumes:** `AnalyticsRefreshed`; in Phase 2 also `DemandSignalsUpdated`. **Emits:** `RenderComplete`

Renders dashboard pages (Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts) and provides PDF, CSV, and JSON exports. Uses a TTL cache and serves stale data with a banner rather than a blank page. Phase 1: full implementation (consumes only `AnalyticsRefreshed`). Phase 2: also consumes `DemandSignalsUpdated` per Event Catalog.

---

## Orchestration Agent

**Classification:** Deterministic. **Consumes:** `IngestBatch`, `NormalizationComplete`, `SkillsExtracted`, `RecordEnriched`, `AnalyticsRefreshed`, `RenderComplete`, `SourceFailure`, `DemandSignalsUpdated`, `DemandAnomaly`, `*Failed`, `*Alert`. **Emits:** not specified (orchestration triggers scheduling/routing)

Only the Orchestration Agent consumes `*Failed` and `*Alert`; no other agent does. Uses LangGraph StateGraph and APScheduler for pipeline orchestration, retry policies, audit logging, and health monitoring. Alerting tiers: Warning, Critical, Fatal. Phase 1: basic (schedule, routing, retries, audit log). Phase 2: circuit-breaking, Saga pattern, compensating flows, Admin API.

---

## Demand Analysis Agent

**Classification:** Phase 2 only. **Consumes:** `RecordEnriched` **Emits:** `DemandSignalsUpdated`, `DemandAnomaly`

Time-series index (skill, role, industry, region), velocity windows (7d, 30d, 90d), emerging/declining skills, supply/demand gap estimates, 30-day demand forecasts, and anomaly detection. Phase 1: scaffold directory only; do not implement. Phase 2: full implementation.

---

## Critical Constraints

- **The Orchestration Agent is the sole consumer of *Failed and *Alert events.** No other agent reacts to another agent’s failures.
- **Demand Analysis is Phase 2 only (scaffold in Phase 1).** Do not implement Demand Analysis logic in Phase 1.

---

## Single Job Flow Trace

End-to-end path for a single job through the pipeline, with the event emitted at each hop:

| Step | Agent           | Emitted event        |
|------|-----------------|----------------------|
| 1    | Ingestion       | `IngestBatch`        |
| 2    | Normalization   | `NormalizationComplete` |
| 3    | Skills Extraction | `SkillsExtracted`  |
| 4    | Enrichment      | `RecordEnriched`     |
| 5    | Analytics       | `AnalyticsRefreshed` |
| 6    | Visualization   | `RenderComplete`     |

Flow: **Ingestion → Normalization → Skills Extraction → Enrichment → Analytics → Visualization.**
