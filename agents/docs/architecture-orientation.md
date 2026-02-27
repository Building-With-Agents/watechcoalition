# Job Intelligence Engine — Architecture Orientation

**Author:** Fabian M. Ornelas  
**Audience:** Implementers, reviewers, curriculum (Exercise 1.4)  
**Source of truth:** `docs/planning/ARCHITECTURE_DEEP.md`  
**Last updated:** 2026-02-27

---

## Purpose

This document orients readers to the eight-agent pipeline: what each agent does, how it fits the event-driven flow, and where **Phase 1** ends and **Phase 2** begins. It is a summary for onboarding and review, not a substitute for the canonical spec. All agents communicate **only via typed, versioned events**; direct calls between agents are forbidden. A critical constraint: **the Orchestration Agent is the sole consumer of `*Failed` and `*Alert` events** — no other agent may react to another agent’s failures.

---

## 1. Ingestion Agent

**LLM:** Deterministic (no LLM).

**Role.** Pipeline entry point. Pulls job postings from external sources and stages them for downstream processing without interpreting content.

**Behavior.** Polls the JSearch API via httpx and scrapes target URLs via Crawl4AI. Each record is fingerprinted with `sha256(source + external_id + title + company + date_posted)` and deduplicated against `raw_ingested_jobs.raw_payload_hash`; duplicates are discarded and a counter incremented. JSearch wins over scraped when the same job appears in both (decision #9). Every record gets provenance: `source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`. Successful records are written to `raw_ingested_jobs`; schema violations are quarantined to `data/dead_letter/`. On source unreachable, the agent uses exponential back-off (max 5 retries) and then emits **SourceFailure** so Orchestration can react.

**Events.** Consumes: none. Emits: **IngestBatch** (batch_id, record_count, source, dedup_count, run_id); **SourceFailure** (to Orchestration only, on unreachable source).

**Phase boundary.** Phase 1: full implementation. Phase 2: no additional scope.

---

## 2. Normalization Agent

**LLM:** Deterministic (no LLM).

**Role.** Translates raw, source-specific payloads into the canonical **JobRecord** schema so the rest of the pipeline works on a single, validated shape.

**Behavior.** Consumes **IngestBatch** and reads the corresponding records from staging. Per-source field mappers map into JobRecord; dates are standardized to ISO 8601, salaries to min/max/currency/period, locations and employment types normalized. HTML is stripped, whitespace cleaned, free text sanitized. Pydantic validation enforces the schema; violations are quarantined with an annotated error path so the batch can continue. Ambiguous mappings are marked with `low_confidence`; currency failures leave raw values and `currency_normalized = false`. Output is written to `normalized_jobs`. On batch failure, the agent emits **NormalizationFailed** to Orchestration.

**Events.** Consumes: **IngestBatch**. Emits: **NormalizationComplete** (batch_id, record_count, quarantine_count); **NormalizationFailed** (to Orchestration only, on batch failure).

**Phase boundary.** Phase 1: full implementation. Phase 2: no additional scope.

---

## 3. Skills Extraction Agent

**LLM:** Required (LLM inference is core to extraction).

**Role.** Derives structured skill information from job text and links it to the canonical taxonomy where possible, so Enrichment and Analytics can reason over skills consistently.

**Behavior.** Consumes **NormalizationComplete** and runs LLM inference over each record’s title, description, requirements, and responsibilities. The LLM produces **SkillRecord** items (label, type, confidence, field_source, required_flag). Taxonomy linking follows a strict order: (1) exact name match in `skills` table, (2) normalized name match, (3) embedding cosine similarity ≥ 0.92, (4) O*NET occupation code match, (5) otherwise emit as **raw_skill** (null taxonomy ID) for Enrichment to resolve in Phase 2. Every LLM call is logged to `llm_audit_log`. On LLM timeout, the agent retries once, then sets `skills = []` and `extraction_status = "failed"` and continues the batch so one bad record does not block others.

**Events.** Consumes: **NormalizationComplete**. Emits: **SkillsExtracted** (batch_id, record_count, skills_count, avg_confidence).

**Phase boundary.** Phase 1: full implementation including taxonomy linking and raw_skill fallback. Phase 2: resolution of raw_skill is Enrichment’s responsibility, not this agent’s.

---

## 4. Enrichment Agent

**LLM:** Optional (classifiers and scoring may be rule-based or LLM-assisted).

**Role.** Adds classification, quality and spam signals, and entity resolution so records can be safely promoted to `job_postings` and used for analytics.

**Behavior.** Consumes **SkillsExtracted**. It classifies job role and seniority, computes a quality score [0–1] (completeness, clarity, AI keyword density, structure), and runs spam detection: below 0.7 proceed, 0.7–0.9 flag for review (`is_spam = null`), above 0.9 auto-reject (do not write to `job_postings`). It resolves **company_id** by matching `companies` on normalized name, creating a placeholder when there is no match; resolves **location_id** from `company_addresses` or leaves null and keeps text. It maps **sector_id** to `industry_sectors`. A record is written to `job_postings` only after `company_id` is resolved. Phase 2 adds raw_skill resolution, company/geo/labor-market enrichment, SOC/NOC, and a composite enrichment quality score — do not implement in Phase 1.

**Events.** Consumes: **SkillsExtracted**. Emits: **RecordEnriched** (batch_id, record_count, spam_rejected, flagged_for_review).

**Phase boundary.** Phase 1 (lite): role, seniority, quality, spam, company_id, location_id, sector_id. Phase 2 (full): raw_skill resolution, company/geo/labor-market, SOC/NOC, enrichment_quality_score — scaffold only in Phase 1.

---

## 5. Analytics Agent

**LLM:** Optional (weekly summaries and text-to-SQL may use LLM; template fallback when unavailable).

**Role.** Builds aggregate views and a query interface so stakeholders can understand job market patterns without touching raw data.

**Behavior.** Consumes **RecordEnriched** and maintains aggregates across dimensions: skill, role, industry, region, experience level, company size. It computes salary distributions (median, p25, p75, p95), co-occurrence matrices (skills appearing together), and posting lifecycle metrics (time-to-fill proxies, repost rates). Weekly insight summaries are LLM-generated with a deterministic template fallback. It exposes **POST /analytics/query** for text-to-SQL with strict guardrails: SELECT only, allowed tables only, 100-row max, 30s timeout; all attempts logged to `llm_audit_log`. Stale data is surfaced with timestamp; cardinality explosion is capped and long-tail coalesced into “Other” with a warning.

**Events.** Consumes: **RecordEnriched**. Emits: **AnalyticsRefreshed** (aggregate_types, record_count, refresh_duration_ms).

**Phase boundary.** Phase 1: full implementation. Phase 2: Demand Analysis also consumes RecordEnriched; Analytics has no separate Phase 2 scope.

---

## 6. Visualization Agent

**LLM:** Optional (Weekly Insights and Ask the Data may use LLM; fallbacks and cache keep the dashboard usable).

**Role.** Surfaces pipeline outputs and analytics in a human-readable dashboard and exports, so operators and stakeholders can monitor quality and explore data without running queries.

**Behavior.** Consumes **AnalyticsRefreshed** (Phase 2 also **DemandSignalsUpdated**). It renders Streamlit pages: Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts. Exports are PDF, CSV, and JSON. The dashboard uses **read-only** SQLAlchemy; data is cached with a TTL and a staleness banner so the page is never blank. On upstream unavailability it serves stale data with a banner and emits **VisualizationDegraded**; on render failure it retries once then emits **RenderFailed** to Orchestration.

**Events.** Consumes: **AnalyticsRefreshed**; Phase 2: **DemandSignalsUpdated**. Emits: **RenderComplete** (pages_rendered, exports_generated); **RenderFailed** (to Orchestration only).

**Phase boundary.** Phase 1: full dashboard and exports. Phase 2: consume DemandSignalsUpdated; no other scope change.

---

## 7. Orchestration Agent

**LLM:** Deterministic (no LLM).

**Role.** Runs the pipeline on a schedule, routes events through the pipeline, and **owns all failure and alert handling** so no other agent reacts to another’s failures.

**Behavior.** Uses LangGraph StateGraph for event routing and APScheduler for the master run schedule (e.g. daily cron). It applies retry policies with exponential back-off and jitter (Ingestion 5, Normalization 3, Skills Extraction 2 per record, transient DB 3). It maintains a structured JSON audit log with **100% completeness** — every trigger, retry, and alert is recorded. Alerting tiers: Warning (log + metric), Critical (page on-call), Fatal (circuit broken + human escalation). **It is the sole consumer of all `*Failed` and `*Alert` events.** No other agent may subscribe to or react to failure or alert events. Phase 2 adds circuit breaker, saga pattern, and admin API — scaffold only in Phase 1, do not implement.

**Events.** Consumes: **all pipeline events** (IngestBatch, NormalizationComplete, SkillsExtracted, RecordEnriched, AnalyticsRefreshed, RenderComplete, SourceFailure, **\*Failed**, **\*Alert**). Emits: trigger and retry signals (not domain events in the catalog).

**Phase boundary.** Phase 1: schedule, routing, retries, audit log, health. Phase 2: circuit breaker, saga, admin API — scaffold only.

---

## 8. Demand Analysis Agent

**LLM:** Optional or deterministic (time-series and forecasting; Phase 2 only).

**Role.** (Phase 2.) Would produce demand signals, trends, and forecasts from enriched job data for use by Analytics and Visualization.

**Behavior.** Phase 1: **scaffold only — do not implement.** Directory and stubs only. Phase 2: would consume **RecordEnriched**, maintain a time-series index (skill, role, industry, region), compute velocity windows (7d, 30d, 90d), identify emerging/declining skills, and produce 30-day demand forecasts. It would emit **DemandSignalsUpdated** and **DemandAnomaly** on spikes or cliffs. Metrics would include forecast MAPE, trend accuracy, anomaly precision.

**Events.** Consumes: **RecordEnriched**. Emits: **DemandSignalsUpdated**; **DemandAnomaly** (to Orchestration).

**Phase boundary.** Phase 1: scaffold only. Phase 2: full implementation.

---

## Event Flow Summary

<table>
<thead>
<tr>
  <th>Agent</th>
  <th>Consumes</th>
  <th>Emits</th>
  <th>LLM</th>
</tr>
</thead>
<tbody>
<tr><td>Ingestion</td><td>—</td><td>IngestBatch, SourceFailure</td><td>No</td></tr>
<tr><td>Normalization</td><td>IngestBatch</td><td>NormalizationComplete, NormalizationFailed</td><td>No</td></tr>
<tr><td>Skills Extraction</td><td>NormalizationComplete</td><td>SkillsExtracted</td><td>Required</td></tr>
<tr><td>Enrichment</td><td>SkillsExtracted</td><td>RecordEnriched</td><td>Optional</td></tr>
<tr><td>Analytics</td><td>RecordEnriched</td><td>AnalyticsRefreshed</td><td>Optional</td></tr>
<tr><td>Visualization</td><td>AnalyticsRefreshed</td><td>RenderComplete, RenderFailed</td><td>Optional</td></tr>
<tr><td>Orchestration</td><td>All events; *Failed and *Alert (sole consumer)</td><td>Trigger/retry signals</td><td>No</td></tr>
<tr><td>Demand Analysis*</td><td>RecordEnriched</td><td>DemandSignalsUpdated, DemandAnomaly</td><td>Optional</td></tr>
</tbody>
</table>

*Phase 2 only.

---

## Critical Constraint: Failure and Alert Events

**Only the Orchestration Agent may consume `*Failed` and `*Alert` events.** Normalization, Skills Extraction, Enrichment, Analytics, and Visualization must not subscribe to or react to another agent’s failure or alert events. This keeps failure handling, retries, and audit in one place and avoids cascading or duplicate reactions.

---

## Trace: One Job from Ingestion to Skills Extraction

Ingestion writes records to `raw_ingested_jobs` and emits **IngestBatch** (payload: batch_id, record_count, source, dedup_count, run_id). Normalization consumes that event, maps and validates records into JobRecords, writes to `normalized_jobs`, and emits **NormalizationComplete** (batch_id, record_count, quarantine_count). Skills Extraction consumes NormalizationComplete, runs LLM inference and taxonomy linking, and emits **SkillsExtracted** (batch_id, record_count, skills_count, avg_confidence). All events in a run share the same **correlation_id** from the initial IngestBatch. Phase 1 uses in-process pub/sub; ordering is preserved per run because each agent runs after its upstream producer. There is no cross-run ordering guarantee unless Orchestration sequences batches.

---

*For full specs, event payloads, DB schema, and build order, see `docs/planning/ARCHITECTURE_DEEP.md`.*
