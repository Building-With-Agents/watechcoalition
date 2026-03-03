# Architecture orientation — eight agents at a glance

Short reference derived from `docs/planning/ARCHITECTURE_DEEP.md` (Agent Specifications, Event Catalog, Directory Scaffold). Use it to see what each agent does, how they communicate, and where Phase 1 ends and Phase 2 begins.

---

## How agents communicate

Agents communicate **only via typed, versioned events** on the message bus. There are no direct function calls between agents. Every event uses the `AgentEvent` envelope: `event_id`, `correlation_id`, `agent_id`, `timestamp`, `schema_version`, `payload`. The **Orchestration Agent** is the sole consumer of all `*Failed` and `*Alert` events; no other agent reacts to another agent’s failures.

---

## Phase 1 vs Phase 2 boundary

- **Phase 1:** Implement now. Includes: Ingestion, Normalization, Skills Extraction, Enrichment (lite), Analytics, Visualization, Orchestration (scheduling, retries, audit log, health). No circuit breaker, saga, or admin API; no Demand Analysis implementation; no full enrichment resolvers (company/geo/labor-market); in-process Python pub/sub only.
- **Phase 2:** Scaffold only in Phase 1 — do not implement. Includes: Demand Analysis agent implementation, circuit breaker, saga, admin API, full enrichment resolvers, external message bus, `DemandSignalsUpdated` / `DemandAnomaly` flows.

---

## 1. Ingestion Agent

**What it does:** Polls JSearch via httpx and scrapes job boards via Crawl4AI; deduplicates by fingerprint (`sha256(source + external_id + title + company + date_posted)`); stages records in `raw_ingested_jobs` with provenance (`source`, `external_id`, `raw_payload_hash`, `ingestion_run_id`). JSearch wins over scraped when the same job appears in both. Quarantines schema violations to dead-letter.

**Determinism:** Deterministic (no LLM).

**Consumes:** — (entry point).

**Emits:** `IngestBatch`; on source unreachable after retries, `SourceFailure` (to Orchestrator only).

**Phase 1 vs 2:** Fully Phase 1; no Phase 2 scope called out for Ingestion.

---

## 2. Normalization Agent

**What it does:** Maps source fields to the canonical `JobRecord` via per-source field mappers; standardizes dates (ISO 8601), salaries (min/max/currency/period), locations, employment types; strips HTML and sanitizes free text. Validates with Pydantic; quarantines violations. Writes to `normalized_jobs`.

**Determinism:** Deterministic (no LLM).

**Consumes:** `IngestBatch`.

**Emits:** `NormalizationComplete`; on batch failure, `NormalizationFailed` (to Orchestrator only).

**Phase 1 vs 2:** Fully Phase 1.

---

## 3. Skills Extraction Agent

**What it does:** Runs LLM inference over title, description, requirements, responsibilities to produce `SkillRecord`s (label, type, confidence, field_source, required_flag). Links to taxonomy in order: exact name → normalized name → embedding ≥ 0.92 → O*NET; otherwise emits as raw skill (null taxonomy ID). Logs every LLM call to `llm_audit_log`.

**Determinism:** LLM-required.

**Consumes:** `NormalizationComplete`.

**Emits:** `SkillsExtracted`.

**Phase 1 vs 2:** Phase 1 does extraction and taxonomy linking; Phase 2 resolves raw skills in Enrichment.

---

## 4. Enrichment Agent

**What it does:** Classifies role and seniority; computes quality score and spam score; resolves `company_id` (match or placeholder) and `sector_id`; writes to `job_postings` only after `company_id` is set. Spam: &lt; 0.7 proceed, 0.7–0.9 flag for review, &gt; 0.9 auto-reject (do not write).

**Determinism:** LLM-optional (classifiers and scoring can be rule-based or LLM-assisted in Phase 1).

**Consumes:** `SkillsExtracted`.

**Emits:** `RecordEnriched`.

**Phase 1 vs 2:** Phase 1 = lite (role, seniority, quality, spam, company_id, sector_id). Phase 2 = full resolvers (company/geo/labor-market, SOC/NOC, prevailing wage, raw-skill resolution).

---

## 5. Analytics Agent

**What it does:** Builds aggregates by skill, role, industry, region, experience level, company size; salary distributions (median, p25/p75/p95); co-occurrence matrices; posting lifecycle metrics. Produces weekly insight summaries (LLM with template fallback) and exposes text-to-SQL Q&A with strict guardrails (SELECT only, allowlist, 100-row max, 30s timeout). Exposes `POST /analytics/query`.

**Determinism:** LLM-optional (aggregates deterministic; weekly summaries and natural-language Q&A use LLM with fallback).

**Consumes:** `RecordEnriched`.

**Emits:** `AnalyticsRefreshed`.

**Phase 1 vs 2:** Fully Phase 1; Demand Analysis consumes `RecordEnriched` in Phase 2.

---

## 6. Visualization Agent

**What it does:** Serves the Streamlit dashboard (Ingestion Overview, Normalization Quality, Skill Taxonomy Coverage, Weekly Insights, Ask the Data, Operations & Alerts) and exports (PDF, CSV, JSON). Uses read-only SQLAlchemy; TTL cache with staleness banner so the page is never blank. Consumes analytics (and in Phase 2, demand signals) to render pages and exports.

**Determinism:** Deterministic (no LLM in the agent itself; displays LLM-generated content from Analytics).

**Consumes:** `AnalyticsRefreshed`; in Phase 2 also `DemandSignalsUpdated`.

**Emits:** `RenderComplete`; on failure, `RenderFailed` / `VisualizationDegraded` (to Orchestrator).

**Phase 1 vs 2:** Phase 1 = full dashboard and exports; Phase 2 = demand signals integrated into views.

---

## 7. Orchestration Agent

**What it does:** Runs the pipeline on a schedule (APScheduler); uses LangGraph StateGraph for event routing; applies retry policies (exponential back-off + jitter) per agent; consumes all `*Failed` and `*Alert` events; maintains structured audit log with 100% completeness; monitors system health. Alert tiers: Warning (log + metric), Critical (page), Fatal (circuit break + escalation).

**Determinism:** Deterministic (orchestration logic; no LLM).

**Consumes:** All events, including `IngestBatch`, `NormalizationComplete`, `SkillsExtracted`, `RecordEnriched`, `AnalyticsRefreshed`, `RenderComplete`, and all `*Failed` / `*Alert` / `SourceFailure` / (Phase 2) `DemandAnomaly`.

**Emits:** Triggers and retry signals (no domain payload events; it coordinates others).

**Phase 1 vs 2:** Phase 1 = schedule, retries, audit log, health, alerting. Phase 2 = circuit breaker, saga, compensating flows, admin API.

---

## 8. Demand Analysis Agent (Phase 2 only)

**What it does:** Time-series indexing by skill, role, industry, region; velocity windows (7d, 30d, 90d); emerging/declining skills; supply/demand gap estimates; 30-day demand forecasts; emits `DemandAnomaly` on spikes or cliffs. **Phase 1:** scaffold directory only; do not implement.

**Determinism:** LLM-optional (forecasting and trend logic may use models or rules).

**Consumes:** `RecordEnriched`.

**Emits:** `DemandSignalsUpdated`; `DemandAnomaly` (to Orchestrator).

**Phase 1 vs 2:** Entire agent is Phase 2; scaffold only in Phase 1.

---

## Event flow summary

| Event                | Producer      | Consumers                                      |
|----------------------|---------------|-------------------------------------------------|
| `IngestBatch`        | Ingestion     | Normalization, Orchestrator                     |
| `NormalizationComplete` | Normalization | Skills Extraction, Orchestrator              |
| `SkillsExtracted`    | Skills Extraction | Enrichment, Orchestrator                     |
| `RecordEnriched`     | Enrichment    | Analytics, Demand Analysis* (Phase 2), Orchestrator |
| `AnalyticsRefreshed` | Analytics     | Visualization, Orchestrator                    |
| `RenderComplete`     | Visualization | Orchestrator                                   |
| `DemandSignalsUpdated` | Demand Analysis* | Visualization, Orchestrator (Phase 2)       |
| `*Failed` / `*Alert` / `SourceFailure` / `DemandAnomaly`* | Any / Ingestion / Demand Analysis* | **Orchestrator only** |

\* Phase 2

---

## Directory scaffold (agents/)

- `ingestion/` — agent, sources (jsearch_adapter, scraper_adapter), deduplicator, tests  
- `normalization/` — agent, schema, field_mappers, tests  
- `skills_extraction/` — agent, models, taxonomy, tests  
- `enrichment/` — agent, classifiers (Phase 1), resolvers (Phase 2), tests  
- `analytics/` — agent, aggregators, query_engine, tests  
- `visualization/` — agent, renderers, exporters, tests  
- `orchestration/` — agent, scheduler; circuit_breaker, saga, admin_api (Phase 2), tests  
- `demand_analysis/` — Phase 2 scaffold only: agent, time_series, forecasting, tests  
- `common/` — events, message_bus, llm_adapter, data_store, config, observability, errors  
- `dashboard/` — streamlit_app.py  
- `docs/` — architecture, api, adr  
