# Job Intelligence Engine — Design Decisions Tracker

Use this file to track open decisions, who owns them, and when they must be resolved.
Update the **Status** and **Decision Made** columns as decisions are locked.
Copy each resolved decision into `CLAUDE.md` under `## Resolved Design Decisions`.

---

## 🔴 Must Resolve Before Week 1

### #12 — Scraping Tool

| Field | Value |
|-------|-------|
| **Options** | Firecrawl, Crawl4AI, ScrapeGraphAI, Browser-use, Spider |
| **Owner** | Engineering / Product |
| **Status** | ✅ Resolved |
| **Decision Made** | Crawl4AI for web scraping + `httpx` for JSearch API |
| **Recommendation** | **Crawl4AI + httpx** — Crawl4AI is open source, pip-installable, and runs entirely locally, matching the top priorities of fast setup and no external service dependency. For JSearch, a plain HTTP client is all that's needed. The Ingestion Agent's source adapter pattern keeps the tool encapsulated — a second adapter (e.g. Firecrawl) can be added later without touching the rest of the pipeline. Browser-use was eliminated (targets login-required sites). Spider was eliminated (optimises for speed/volume, lowest priority). ScrapeGraphAI solves changing layouts but adds LLM overhead not justified yet. Firecrawl is strong but external/paid. |

---

### #13 — Multi-Agent Framework

| Field | Value |
|-------|-------|
| **Options** | LangGraph (recommended), CrewAI, AutoGen, Semantic Kernel, Custom |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | LangGraph StateGraph |
| **Recommendation** | **LangGraph** — Its StateGraph model maps directly to the eight-agent pipeline: each agent is a node, events are edges, and the Orchestrator controls routing. Python-native, integrates with LangChain (already needed for the LLM adapter), and pairs with LangSmith for tracing (decision #17). CrewAI is simpler but optimised for role-based collaboration, not a sequential pipeline. AutoGen is conversation-oriented and heavier. Semantic Kernel fits .NET environments better. Custom adds build overhead with no upside at this scale. The BRD explicitly recommends LangGraph, and the architecture is framework-agnostic at the agent-contract level so switching later is possible. |

---

## 🟠 Must Resolve Before Week 3

### #4 — Source of Truth for Ingested Jobs

| Field | Value |
|-------|-------|
| **Options** | Option A: extend `job_postings` / Option B: staging tables + promotion |
| **Owner** | Product / Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Option B — staging tables + promotion (`raw_ingested_jobs` → `normalized_jobs` → `job_postings`) |
| **Recommendation** | **Option B (staging tables + promotion)** — Ingested jobs arrive without `company_id` and `location_id`, which `job_postings` currently requires. Staging lets you hold records until resolution is complete before they touch the canonical table. It also makes the pipeline fully replayable — you can re-run normalization or skills extraction without affecting production data. Option A is simpler but risks polluting `job_postings` with partially-resolved records and makes it harder to distinguish employer-created from ingested jobs at the schema level. The extra Week 3 effort pays off in every subsequent week. |

---

### #14 — Message Bus Technology

| Field | Value |
|-------|-------|
| **Options** | In-process Python events (Phase 1 default), Kafka, RabbitMQ, Redis Streams |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | In-process Python events for Phase 1; external bus deferred to Phase 2 |
| **Recommendation** | **In-process Python events for Phase 1** — Kafka and RabbitMQ add infrastructure overhead (separate services, connection management, serialisation) that slows down Weeks 1–9 without meaningful benefit at current scale. The event envelope contracts are bus-agnostic — swapping to an external bus in Phase 2 only requires changing the transport layer, not the event definitions or agent logic. Only reconsider if multi-process or multi-machine agent deployment is needed before Week 12. |

---

### #3 — Batch-First vs Real-Time-First

| Field | Value |
|-------|-------|
| **Options** | Batch-first, Real-time-first |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | Batch-first — APScheduler, daily cron default |
| **Recommendation** | **Batch-first** — Job postings are not time-critical at the minute level. Real-time-first adds significant complexity (streaming connectors, backpressure handling, stateful dedup across a live stream) that isn't justified by the use case. Batch-first aligns naturally with APScheduler (already chosen for the Orchestration Agent) and makes evaluation simpler: run a batch, measure results, iterate. Real-time would only be warranted if job seekers needed postings within seconds of publication, which is not a stated requirement. |

---

## 🟡 Must Resolve Before Week 4

### #15 — Skill Taxonomy Source

| Field | Value |
|-------|-------|
| **Options** | ESCO, O*NET, Internal watechcoalition tables, Hybrid |
| **Owner** | Product / Data |
| **Status** | ✅ Resolved |
| **Decision Made** | Internal watechcoalition taxonomy primary (`technology_areas`, `skills`); O*NET fallback |
| **Recommendation** | **Internal watechcoalition taxonomy as primary, O\*NET as fallback** — The platform already has `technology_areas`, `skills`, and `pathways` tables with embeddings. Using these as primary means extracted skills map directly to what job seekers and employers already use — no translation layer needed. Skills that don't match the internal taxonomy fall back to O*NET (which already appears as `occupation_code` on `job_postings`). ESCO is comprehensive but European-focused and heavy to integrate. O*NET alone adds a mapping step before anything is useful in the existing UI. |

---

### #1 — Taxonomy for Job Classification

| Field | Value |
|-------|-------|
| **Options** | SOC, Internal (`technology_areas`, `pathways`, `industry_sectors`), Hybrid |
| **Owner** | Product / Data |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Internal taxonomy primary, SOC codes secondary** — Same logic as #15. Classifying job roles and industries against `technology_areas`, `pathways`, and `industry_sectors` keeps output immediately usable in the existing platform. SOC codes are already partially supported via `occupation_code` on `job_postings`, so appending a SOC code alongside the internal classification costs little and adds labour-market interoperability for Phase 2 (Demand Analysis uses SOC codes). |

---

### #6 — Evaluation Dataset

| Field | Value |
|-------|-------|
| **Options** | Who provides it, what format, what size |
| **Owner** | Data / Product |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Manually label 30–50 postings by Week 3, intern-led, JSON format** — 30–50 hand-labeled postings is enough to get meaningful precision/recall numbers without a large labeling effort. Format: JSON, one record per posting, with expected skills (label + type + required/preferred flag). The intern building the Skills Extraction Agent should label at least half the dataset — it builds intuition for what good extraction looks like and surfaces edge cases early. |

---

## 🟡 Must Resolve Before Week 6

### #8 — Spam Threshold Policy

| Field | Value |
|-------|-------|
| **Options** | Reject immediately, Flag for review; threshold value |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | Tiered — flag at 0.7, auto-reject above 0.9 |
| **Recommendation** | **Tiered: flag at 0.7, auto-reject above 0.9** — A binary reject/keep threshold is too blunt. Spam detection models have false positives, and auto-rejecting everything above a single threshold risks losing legitimate jobs. Tiered approach: scores above 0.9 are auto-rejected (high confidence spam), 0.7–0.9 are flagged for operator review in the dashboard, below 0.7 proceed normally. Thresholds should be tuned after Week 4's evaluation data is available. |

---

### #9 — Deduplication Source Priority

| Field | Value |
|-------|-------|
| **Options** | Source-agnostic, JSearch wins over scraped |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | JSearch wins over scraped when duplicate |
| **Recommendation** | **JSearch wins over scraped when duplicate** — JSearch API data is structured by design: field coverage, salary data, and metadata quality are generally higher than scraped HTML. When the same job appears in both sources, keeping the JSearch version is the safer default. Easy to implement as a source priority config in the Ingestion Agent, and overridable per-source later. |

---

### #16 — Orchestration Engine

| Field | Value |
|-------|-------|
| **Options** | LangGraph StateGraph, Temporal, Prefect, Airflow, Custom |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | LangGraph StateGraph (consistent with #13) |
| **Recommendation** | **LangGraph StateGraph (consistent with #13)** — If LangGraph is chosen for #13, using it for orchestration keeps the stack consistent: one framework for both agent routing and orchestration, one set of concepts to learn, one tracing integration. Temporal and Prefect are excellent but are separate services adding infrastructure overhead not justified at this scale. Airflow is better suited for data pipelines than agent orchestration. Custom adds build time with no upside. If #13 resolves to a different framework, revisit this decision. |

---

### #17 — Agent Tracing

| Field | Value |
|-------|-------|
| **Options** | LangSmith, OpenTelemetry + custom spans, Arize Phoenix |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | LangSmith — native LangGraph integration |
| **Recommendation** | **LangSmith** — Purpose-built for LLM agent tracing; integrates directly with LangChain and LangGraph (consistent with #13 and #16). Captures prompts, model responses, latency, token counts, and agent decision traces out of the box with no custom span instrumentation. For an internship project where visibility into LLM behaviour is a key learning outcome, LangSmith's UI is significantly more useful than raw OpenTelemetry spans. Free tier available. If a fully offline setup is required, OpenTelemetry is the fallback. |

---

## 🟡 Must Resolve Before Week 8

### #18 — Analytics Query Interface

| Field | Value |
|-------|-------|
| **Options** | REST, GraphQL, SQL-over-wire (e.g. Trino) |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | REST — `POST /analytics/query` |
| **Recommendation** | **REST** — The Analytics Agent's query interface is consumed by two internal clients: the Streamlit dashboard and the Orchestration Agent. Neither needs GraphQL's flexibility or Trino's scale. A simple REST endpoint (`POST /analytics/query`) is the fastest to implement, easiest to secure with the SQL guardrails already specified in the TRD, and straightforward to test. GraphQL adds schema overhead with no real benefit at this scale. Trino is production data warehouse tooling — significant overkill for a 12-week curriculum project. |

---

### #11 — LLM Provider Policy

| Field | Value |
|-------|-------|
| **Options** | Provider-agnostic adapter, Fixed provider |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Provider-agnostic adapter — Azure OpenAI default, switchable via env var |
| **Recommendation** | **Provider-agnostic adapter, Azure OpenAI as default** — The adapter is already scaffolded in Week 2. The policy: Azure OpenAI as default (already integrated via `app/lib/openAiClients.ts`), switchable to Anthropic or OpenAI via a single env var change. Fallback rule: if the configured provider fails after 2 retries, log the failure, skip LLM enrichment for that record, and flag it for re-processing. This future-proofs against Azure outages and keeps model selection flexible without any additional architecture work. |

---

## 🟢 Can Defer to Phase 2

| # | Decision | Recommendation | Owner |
|---|----------|----------------|-------|
| 2 | **ML hosting** | Start in-repo (Python in `agents/`). Migrate to Azure ML only if model size or training requirements demand it. | Engineering |
| 5 | **Storage** | MSSQL-only for Phase 1. Add vector DB (pgvector or Azure AI Search) only if semantic dedup in Week 9 shows MSSQL similarity queries are too slow. | Engineering |
| 7 | **AI relevance ground truth** | Define scoring criteria with Product before Phase 2. No labeling work needed in Phase 1. | Product / Data |
| 10 | **Prompt and model versioning** | Store prompts as versioned files in `agents/skills_extraction/models/prompts/`. Add formal A/B versioning before Week 10 security review. | Engineering |
| 19 | **Database engine (MSSQL vs PostgreSQL)** | Stay on MSSQL for Phase 1. See full reasoning below. | Engineering |

### #19 — Database Engine (MSSQL vs PostgreSQL)

| Field | Value |
|-------|-------|
| **Options** | Stay on MSSQL, Migrate to PostgreSQL, Run both in parallel |
| **Owner** | Engineering |
| **Status** | ✅ Resolved (deferred to Phase 2) |
| **Decision Made** | Stay on MSSQL for Phase 1 |
| **Recommendation** | **Stay on MSSQL for Phase 1** — The existing watechcoalition app, Prisma schema, and all platform data already run on MSSQL. The agent pipeline reads from and writes to the same database, which means agents can join directly against `job_postings`, `skills`, `companies`, and `technology_areas` — joins that are central to how the pipeline works. Switching to PostgreSQL would require either migrating the entire existing app (a large, risky side project) or running two separate databases, which removes the ability to do cross-database joins cleanly. PostgreSQL is genuinely better for this workload — `pgvector` for near-dedup, better full-text search, richer JSON querying — but the right time to make that choice was before the app was built. The one exception to monitor: if Week 9 near-duplicate detection needs vector similarity at scale, adding `pgvector` as a sidecar for just that use case is worth revisiting in Phase 2. |

---

## 🟡 New Decisions Surfaced from Canonical Architecture Doc

These decisions were identified as open questions in `job_intelligence_engine_architecture.docx` (Section 6) and were not previously captured in planning documents. They must be resolved before the relevant phase begins.

---

### #20 — Enrichment Agent Phase Split

| Field | Value |
|-------|-------|
| **Options** | Option A: Single full Enrichment Agent (per docx) / Option B: Lite (Phase 1) + Full (Phase 2) |
| **Owner** | Product / Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Option B — Enrichment-lite in Phase 1; full enrichment in Phase 2 |
| **Recommendation** | **Option B** — The docx defines Enrichment as a single complete agent, but the full responsibilities (company DB lookups, geo APIs, labor-market data, SOC/NOC codes) require external data sources and integrations that are not available in the 12-week curriculum environment. Phase 1 delivers the classification, quality scoring, and spam detection work that is immediately valuable to the job-seeker surface. All Phase 1 code is written to be extended — the Phase 2 responsibilities slot into the same agent without architectural changes. |

---

### #21 — PDF Export Scope

| Field | Value |
|-------|-------|
| **Options** | Standard Phase 1 deliverable / Stretch goal |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Standard Phase 1 deliverable |
| **Recommendation** | **Standard** — The canonical architecture doc lists PDF summaries, CSV extracts, and JSON payloads as standard Visualization Agent output with no qualification. PRD/TRD had incorrectly downgraded PDF to a stretch goal parenthetical. Restored to standard. Streamlit's built-in export capabilities or a lightweight PDF library (e.g. `weasyprint`, `fpdf2`) are sufficient — no external service needed. |

---

### #22 — Multi-Tenancy

| Field | Value |
|-------|-------|
| **Options** | Single shared pipeline / Per-tenant agent instances |
| **Owner** | Product / Engineering |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Single shared pipeline for Phase 1** — The watechcoalition platform is a single-tenant application today. Per-tenant agent instances add significant infrastructure complexity (separate schedulers, separate DB namespacing, separate LLM quota management) with no current business need. If multi-tenancy becomes a requirement in Phase 2, the agent contract and event envelope design already supports a `tenant_id` field in the payload — it just hasn't been populated. Revisit before any Phase 2 work that involves serving multiple organizations. |

---

### #23 — Feedback Loop Agent

| Field | Value |
|-------|-------|
| **Options** | Build a dedicated Feedback Agent / Integrate feedback into existing agents / Defer entirely |
| **Owner** | Product / Engineering |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Defer to Phase 2** — A feedback loop for accepting user corrections and training signal is architecturally valid and important for long-term model quality. However, it requires: a defined source of ground truth (who provides corrections and in what format), a training pipeline, and a model versioning strategy (decision #10). None of these are in place for Phase 1. The evaluation harness built in Week 4 is the closest Phase 1 analogue — it produces labeled data that could seed a feedback loop in Phase 2. Log this as a Phase 2 requirement and revisit after the Week 10 security review establishes what data can be retained and used for training. |

---

## Critical Path Summary

| When | Decision(s) | Why |
|------|-------------|-----|
| **Before Week 1** | #12 ✅, #13 ✅ | Week 1 deliverable is a working scrape — can't start without tool and framework chosen |
| **Before Week 3** | #4 ✅, #14 ✅, #3 ✅ | #4 determines the entire DB schema for Week 3 |
| **Before Week 4** | #15 ✅, #1, #6 | Taxonomy decisions shape the core intelligence of the system |
| **Before Week 6** | #8 ✅, #9 ✅, #16 ✅, #17 ✅ | Orchestration Agent is built in Week 6 — framework and thresholds must be set |
| **Before Week 8** | #18 ✅, #11 ✅ | Analytics Q&A interface and LLM policy must be locked |

---

## How to Use This File

1. Work through decisions in deadline order (Week 1 first).
2. When a decision is made, update **Status** to ✅ Resolved and fill in **Decision Made**.
3. Copy the resolved decision into `CLAUDE.md` under a `## Resolved Design Decisions` section so Claude Code always has the latest context.
4. Bring any unresolved decisions approaching their deadline to the next planning session.
