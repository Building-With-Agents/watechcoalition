# Architecture Orientation — Job Intelligence Engine

This document summarizes each of the eight agents in the Job Intelligence Engine pipeline: what each agent does, how they communicate, and the Phase 1 vs Phase 2 boundary.

**Key principle:** Agents communicate exclusively through typed, versioned `AgentEvent` objects via the in-process message bus. Direct function calls between agents are forbidden. The Orchestration Agent is the **sole consumer** of all `*Failed` and `*Alert` events — no other agent reacts to another agent's failures.

---

## 1. Ingestion Agent

**Pattern:** Deterministic

**What it does:** Polls the JSearch API via `httpx` and scrapes job postings from configured target URLs via Crawl4AI. For each record it generates a fingerprint (`sha256(source + external_id + title + company + date_posted)`), deduplicates against already-staged records, and writes new records to the `raw_ingested_jobs` staging table with full provenance tags (`source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`, `ingestion_timestamp`). When the same job appears in both JSearch and a scraped source, JSearch wins (Decision #9).

**Events emitted:** `IngestBatch`
**Events consumed:** None (triggered by the Orchestration Agent scheduler)

**Phase 1:** Full implementation — dual-source ingestion (JSearch + Crawl4AI), fingerprint dedup, staging table writes, `IngestBatch` event.
**Phase 2:** No additions planned for this agent.

---

## 2. Normalization Agent

**Pattern:** Deterministic

**What it does:** Consumes `IngestBatch` events and maps raw source fields to the canonical `JobRecord` Pydantic schema via per-source field mappers. It standardizes dates to ISO 8601, salaries to min/max/currency/period, locations, and employment types; strips HTML and cleans whitespace. Records that fail schema validation are quarantined to `data/dead_letter/` and never passed downstream — the batch continues without them.

**Events emitted:** `NormalizationComplete`
**Events consumed:** `IngestBatch`

**Phase 1:** Full implementation — field mappers for JSearch and Crawl4AI sources, Pydantic validation, quarantine path, `normalized_jobs` table writes.
**Phase 2:** No additions planned for this agent.

---

## 3. Skills Extraction Agent

**Pattern:** LLM-required

**What it does:** Consumes `NormalizationComplete` events and uses an LLM to extract skills from job title, description, requirements, and responsibilities fields. Each extracted skill becomes a `SkillRecord` with a label, type, confidence score, source field, and required flag. It attempts to link each skill to the internal watechcoalition taxonomy in this order: exact name match → normalized name match → embedding cosine similarity ≥ 0.92 → O\*NET code match. Skills that cannot be linked are emitted as `raw_skill` records (null `taxonomy_id`). Every LLM call is logged to the `llm_audit_log` table. On LLM timeout the agent retries once, then sets `extraction_status = "failed"` and continues the batch.

**Events emitted:** `SkillsExtracted`
**Events consumed:** `NormalizationComplete`

**Phase 1:** Full implementation — LLM extraction, taxonomy linking (steps 1–4), `raw_skill` fallback, `llm_audit_log` writes.
**Phase 2:** Resolution of `raw_skill` entries against alternative taxonomy sources (moved to Enrichment Agent Phase 2).

---

## 4. Enrichment Agent

**Pattern:** LLM-optional (classifiers may use LLM; spam detection is heuristic)

**What it does:** Consumes `SkillsExtracted` events and adds business-level metadata to each record. In Phase 1 it classifies job role and seniority, calculates a quality score (0–1) based on completeness, linguistic clarity, AI keyword density, and structural coherence, and runs spam detection with a tiered outcome: score < 0.7 → proceed; 0.7–0.9 → flag for operator review (`is_spam = null`); > 0.9 → auto-reject (record never written to `job_postings`). It also resolves `company_id` by matching against the `companies` table — creating a placeholder if no match — and maps `sector_id` to `industry_sectors`. Records are only written to `job_postings` after `company_id` is resolved.

**Events emitted:** `RecordEnriched`
**Events consumed:** `SkillsExtracted`

**Phase 1 (lite):** Role/seniority classification, quality scoring, spam detection, company and sector resolution, `job_postings` writes.
**Phase 2 (full):** Company-level data (industry, size, funding stage), geographic enrichment (region, metro, remote classification), labor-market codes (SOC/NOC), resolution of `raw_skill` entries, prevailing wage bands, composite enrichment quality score.

---

## 5. Analytics Agent

**Pattern:** LLM-optional (deterministic aggregations; LLM for weekly summaries with template fallback)

**What it does:** Consumes `RecordEnriched` events and maintains aggregate tables across six dimensions: skill, role, industry, region, experience level, and company size. It computes salary distributions (median, p25, p75, p95), skill co-occurrence matrices, and posting lifecycle metrics. It generates weekly LLM-written summaries of demand trends with a deterministic template fallback if the LLM is unavailable. It also exposes a `POST /analytics/query` REST endpoint that accepts natural-language questions, converts them to SQL via an LLM, validates the SQL against strict guardrails (SELECT only, allowed tables only, no DDL/DML, 100-row limit, 30s timeout), executes the query, and returns results.

**Events emitted:** `AnalyticsRefreshed`
**Events consumed:** `RecordEnriched`

**Phase 1:** Full implementation — all six aggregation dimensions, salary distributions, co-occurrence matrices, LLM weekly summaries with template fallback, text-to-SQL endpoint with guardrails.
**Phase 2:** Demand signals integration from Demand Analysis Agent output.

---

## 6. Visualization Agent

**Pattern:** Deterministic

**What it does:** Consumes `AnalyticsRefreshed` events and renders the Streamlit dashboard across six pages: Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, and Operations & Alerts. It maintains a TTL cache and always serves the last successful render with a staleness banner rather than a blank page. It generates exports in PDF, CSV, and JSON formats (all standard Phase 1 deliverables). The database connection is read-only.

**Events emitted:** `RenderComplete`
**Events consumed:** `AnalyticsRefreshed`

**Phase 1:** Full implementation — all six dashboard pages, TTL cache with staleness banner, PDF/CSV/JSON exports, read-only DB connection.
**Phase 2:** No additions planned.

---

## 7. Orchestration Agent

**Pattern:** Deterministic

**What it does:** The control plane for the entire pipeline. It schedules all other agents via APScheduler (cron-configurable; default: daily at 2am), monitors event flows, and is the **sole consumer of all `*Failed` and `*Alert` events** — no other agent is permitted to react to another agent's failures. It applies tiered alerting (Warning: log + metric; Critical: page; Fatal: circuit break + escalation) and per-agent retry policies with exponential back-off. It records 100% of all triggers, retries, and alert creations in the `orchestration_audit_log` table. It uses LangGraph `StateGraph` for routing (Decision #13) and LangSmith for tracing (Decision #17).

**Events emitted:** Trigger and retry signals to all agents
**Events consumed:** ALL events from all agents, including all `*Failed` and `*Alert` events

**Phase 1:** Full implementation — LangGraph StateGraph, APScheduler, alerting tiers, retry policies, audit log.
**Phase 2:** Circuit breaker, compensating sagas, admin API (scaffolded in Phase 1, not implemented).

---

## 8. Demand Analysis Agent

**Pattern:** LLM-optional

**What it does:** Analyzes enriched job records over time to identify emerging and declining skills and roles, compute velocity windows (7d, 30d, 90d), and generate 30-day demand forecasts. It emits `DemandSignalsUpdated` and `DemandAnomaly` events to alert on detected spikes or cliffs.

**Events emitted:** `DemandSignalsUpdated`, `DemandAnomaly`
**Events consumed:** `RecordEnriched`

**Phase 1:** Scaffold only — directory structure created, no implementation.
**Phase 2:** Full implementation — time-series analysis, forecasting models, velocity windows, anomaly detection, `demand_signals` table writes.

---

## Event Catalog Summary

| Event | Producer | Consumers |
|-------|----------|-----------|
| `IngestBatch` | Ingestion | Normalization, Orchestration |
| `NormalizationComplete` | Normalization | Skills Extraction, Orchestration |
| `SkillsExtracted` | Skills Extraction | Enrichment, Orchestration |
| `RecordEnriched` | Enrichment | Analytics, Demand Analysis*, Orchestration |
| `AnalyticsRefreshed` | Analytics | Visualization, Orchestration |
| `RenderComplete` | Visualization | Orchestration |
| `DemandSignalsUpdated` | Demand Analysis* | Analytics, Visualization, Orchestration |
| `DemandAnomaly` | Demand Analysis* | Orchestration |
| `*Failed` / `*Alert` | Any agent | **Orchestration only** |

\* Phase 2
