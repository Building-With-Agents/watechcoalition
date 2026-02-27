# Job Intelligence Engine — Design Decisions Tracker

Use this file to track decisions, who owns them, and when they must be resolved.
Update the **Status** and **Decision Made** columns as decisions are locked.
Copy each resolved decision into `CLAUDE.md` under `## Design Decisions`.

---

## Decision Classification

Every decision in this tracker falls into one of three categories:

| Tier | Label | Meaning | Student Action |
|------|-------|---------|----------------|
| **IC** | Infrastructure Constraint | Fixed by the existing platform, product requirements, or curriculum scope. Not open for student choice. | Document as a constraint with rationale for why it is fixed. |
| **SA** | Student ADR | Open for genuine research and team decision. Multiple viable options exist. | Produce an ADR with alternatives evaluated, rationale, and consequences. |
| **D** | Deferred | Phase 2 decision — genuinely open for future resolution. | Document as a future decision point. |

**SA decisions** include a **Reference Implementation** column. This is not the answer — it is one viable option that downstream exercises use as a default. If your team's ADR selects the reference implementation, the ADR must still explain the evaluation that led to that choice. "The spec said so" is not a rationale.

**Each SA decision must converge before the team implements the agent that depends on it.** If a team has not converged, the reference implementation is adopted so downstream exercises can proceed.

---

## 🔴 Must Resolve Before Week 1

### #12 — Scraping Tool

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | Firecrawl, Crawl4AI, ScrapeGraphAI, Browser-use, Spider |
| **Owner** | Engineering / Product |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | Crawl4AI for web scraping + `httpx` for JSearch API |
| **ADR File** | `docs/adr/ADR-012-scraping-tool.md` |
| **Evaluation Criteria** | Setup complexity (pip-installable vs external service?), JavaScript rendering support, cost (open source vs paid), output completeness, error handling, observability integration. The Week 1 Crawl4AI exercise provides initial evidence for this decision. |

---

### #13 — Multi-Agent Framework

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | LangGraph, CrewAI, AutoGen, Semantic Kernel, Custom |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | LangGraph StateGraph |
| **ADR File** | `docs/adr/ADR-013-multi-agent-framework.md` |
| **Evaluation Criteria** | Does its execution model map to a sequential pipeline with conditional routing? Python-native? LLM tracing integration? Community and documentation maturity? How much of the agent contract (events, health checks, error routing) does the framework handle vs require custom code? |

---

## 🟠 Must Resolve Before Week 3

### #4 — Source of Truth for Ingested Jobs

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Option A: extend `job_postings` / Option B: staging tables + promotion |
| **Owner** | Product / Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Option B — staging tables + promotion (`raw_ingested_jobs` → `normalized_jobs` → `job_postings`) |
| **Rationale** | Ingested jobs arrive without `company_id` and `location_id`, which `job_postings` currently requires. Staging lets you hold records until resolution is complete before they touch the canonical table. The existing database schema dictates this approach. |

---

### #14 — Message Bus Technology

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | In-process Python events (Phase 1 default), Kafka, RabbitMQ, Redis Streams |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | In-process Python events for Phase 1; external bus deferred to Phase 2 |
| **ADR File** | `docs/adr/ADR-014-message-bus.md` |
| **Evaluation Criteria** | Infrastructure overhead (separate service required?), serialization complexity, event envelope compatibility, migration path to external bus in Phase 2, impact on unit testing (can tests run without the bus service?). |

---

### #3 — Batch-First vs Real-Time-First

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Batch-first, Real-time-first |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | Batch-first — APScheduler, daily cron default |
| **Rationale** | Job postings are not time-critical at the minute level. Real-time-first adds significant complexity (streaming connectors, backpressure handling, stateful dedup across a live stream) that isn't justified by the use case. Batch-first aligns naturally with APScheduler and makes evaluation simpler: run a batch, measure results, iterate. This is a product requirement, not a technology choice. |

---

## 🟡 Must Resolve Before Week 4

### #15 — Skill Taxonomy Source

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | ESCO, O*NET, Internal watechcoalition tables, Hybrid |
| **Owner** | Product / Data |
| **Status** | ✅ Resolved |
| **Decision Made** | Internal watechcoalition taxonomy primary (`technology_areas`, `skills`); O*NET fallback |
| **Rationale** | The platform already has `technology_areas`, `skills`, and `pathways` tables with embeddings. Using these as primary means extracted skills map directly to what job seekers and employers already use. The existing platform data dictates this choice. |

---

### #1 — Taxonomy for Job Classification

| Field | Value |
|-------|-------|
| **Options** | SOC, Internal (`technology_areas`, `pathways`, `industry_sectors`), Hybrid |
| **Owner** | Product / Data |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Internal taxonomy primary, SOC codes secondary** — Same logic as #15. Classifying job roles and industries against `technology_areas`, `pathways`, and `industry_sectors` keeps output immediately usable in the existing platform. |

---

### #6 — Evaluation Dataset

| Field | Value |
|-------|-------|
| **Options** | Who provides it, what format, what size |
| **Owner** | Data / Product |
| **Status** | ⬜ Open |
| **Decision Made** | |
| **Recommendation** | **Manually label 30–50 postings by Week 3, intern-led, JSON format** — 30–50 hand-labeled postings is enough to get meaningful precision/recall numbers without a large labeling effort. |

---

## 🟡 Must Resolve Before Week 6

### #8 — Spam Threshold Policy

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Reject immediately, Flag for review; threshold value |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | Tiered — flag at 0.7, auto-reject above 0.9 |
| **Rationale** | Product policy decision. Spam detection models have false positives — a binary threshold risks losing legitimate jobs. Tiered approach: > 0.9 auto-reject, 0.7–0.9 flag for review, < 0.7 proceed. Thresholds may be tuned after Week 4 evaluation data is available. |

---

### #9 — Deduplication Source Priority

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Source-agnostic, JSearch wins over scraped |
| **Owner** | Product |
| **Status** | ✅ Resolved |
| **Decision Made** | JSearch wins over scraped when duplicate |
| **Rationale** | Product policy. JSearch API data is structured by design: field coverage, salary data, and metadata quality are generally higher than scraped HTML. When the same job appears in both sources, keeping the JSearch version is the safer default. |

---

### #16 — Orchestration Engine

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | LangGraph StateGraph, Temporal, Prefect, Airflow, Custom |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | LangGraph StateGraph (consistent with #13) |
| **ADR File** | `docs/adr/ADR-016-orchestration-engine.md` |
| **Evaluation Criteria** | Consistency with multi-agent framework choice (#13), infrastructure overhead, retry/scheduling capabilities, tracing integration, learning curve. If #13 and #16 use the same framework, the team learns one tool instead of two — but that may not always be the best fit. |

---

### #17 — Agent Tracing

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | LangSmith, OpenTelemetry + custom spans, Arize Phoenix |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | LangSmith — native LangGraph integration |
| **ADR File** | `docs/adr/ADR-017-agent-tracing.md` |
| **Evaluation Criteria** | LLM-specific trace capture (prompts, token counts, latency) vs generic spans, integration with chosen multi-agent framework (#13), UI quality for debugging agent decisions, cost and hosting model (SaaS vs self-hosted), offline capability. |

---

## 🟡 Must Resolve Before Week 8

### #18 — Analytics Query Interface

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | REST, GraphQL, SQL-over-wire (e.g. Trino) |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | REST — `POST /analytics/query` |
| **ADR File** | `docs/adr/ADR-018-analytics-query-interface.md` |
| **Evaluation Criteria** | Number of consumers (Streamlit dashboard + Orchestration Agent), query complexity needs, implementation speed, security (SQL guardrail enforcement), testability, documentation generation. |

---

### #11 — LLM Provider Policy

| Field | Value |
|-------|-------|
| **Classification** | SA — Student ADR |
| **Options** | Provider-agnostic adapter, Fixed provider |
| **Owner** | Engineering |
| **Status** | ⬜ Student ADR Required |
| **Reference Implementation** | Provider-agnostic adapter — Azure OpenAI default, switchable via env var |
| **ADR File** | `docs/adr/ADR-011-llm-provider-strategy.md` |
| **Evaluation Criteria** | Vendor lock-in risk, abstraction overhead, fallback behavior on provider failure, testing strategy (can tests run without a live API key?), cost management across providers. |

---

## 🟡 Resolved — Infrastructure Constraints (context only)

These IC decisions are resolved and included for context. They are not open for student choice.

### #19 — Database Engine (MSSQL vs PostgreSQL)

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Stay on MSSQL, Migrate to PostgreSQL, Run both in parallel |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Stay on MSSQL for Phase 1 |
| **Rationale** | The existing watechcoalition app, Prisma schema, and all platform data already run on MSSQL. The agent pipeline reads from and writes to the same database. Switching to PostgreSQL would require either migrating the entire existing app or running two separate databases. This is an infrastructure constraint, not a technology preference. |

---

### #20 — Enrichment Agent Phase Split

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Option A: Single full Enrichment Agent / Option B: Lite (Phase 1) + Full (Phase 2) |
| **Owner** | Product / Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Option B — Enrichment-lite in Phase 1; full enrichment in Phase 2 |
| **Rationale** | Curriculum scope constraint. The full Enrichment responsibilities (company DB lookups, geo APIs, labor-market data, SOC/NOC codes) require external data sources not available in the 12-week curriculum environment. |

---

### #21 — PDF Export Scope

| Field | Value |
|-------|-------|
| **Classification** | IC — Infrastructure Constraint |
| **Options** | Standard Phase 1 deliverable / Stretch goal |
| **Owner** | Engineering |
| **Status** | ✅ Resolved |
| **Decision Made** | Standard Phase 1 deliverable |
| **Rationale** | Scope decision. The canonical architecture doc lists PDF summaries, CSV extracts, and JSON payloads as standard Visualization Agent output. |

---

## 🟢 D — Deferred to Phase 2

| # | Decision | Recommendation | Owner |
|---|----------|----------------|-------|
| 2 | **ML hosting** | Start in-repo (Python in `agents/`). Migrate to Azure ML only if model size or training requirements demand it. | Engineering |
| 5 | **Storage** | MSSQL-only for Phase 1. Add vector DB (pgvector or Azure AI Search) only if semantic dedup in Week 9 shows MSSQL similarity queries are too slow. | Engineering |
| 7 | **AI relevance ground truth** | Define scoring criteria with Product before Phase 2. No labeling work needed in Phase 1. | Product / Data |
| 10 | **Prompt and model versioning** | Store prompts as versioned files in `agents/skills_extraction/models/prompts/`. Add formal A/B versioning before Week 10 security review. | Engineering |

### #22 — Multi-Tenancy

| Field | Value |
|-------|-------|
| **Classification** | D — Deferred |
| **Options** | Single shared pipeline / Per-tenant agent instances |
| **Owner** | Product / Engineering |
| **Status** | ⬜ Open |
| **Recommendation** | Single shared pipeline for Phase 1. Revisit before any Phase 2 work that involves serving multiple organizations. |

---

### #23 — Feedback Loop Agent

| Field | Value |
|-------|-------|
| **Classification** | D — Deferred |
| **Options** | Build a dedicated Feedback Agent / Integrate feedback into existing agents / Defer entirely |
| **Owner** | Product / Engineering |
| **Status** | ⬜ Open |
| **Recommendation** | Defer to Phase 2. Requires: defined ground truth source, training pipeline, model versioning strategy (#10). The Week 4 evaluation harness is the closest Phase 1 analogue. |

---

## Critical Path Summary

| When | Decision(s) | Classification | Why |
|------|-------------|----------------|-----|
| **Before Week 1** | #12, #13 | SA | Week 1 uses reference implementation tools directly. ADR research begins immediately. |
| **Before Week 3** | #4, #14, #3 | IC, SA, IC | #4 determines DB schema for Week 3. #14 ADR must converge before Ingestion/Normalization agents. |
| **Before Week 4** | #15, #1, #6 | IC, Open, Open | Taxonomy is IC (fixed). #1 and #6 remain open. |
| **Before Week 6** | #8, #9, #16, #17 | IC, IC, SA, SA | Orchestration Agent is built in Week 6 — #16/#17 ADRs must converge. |
| **Before Week 8** | #18, #11 | SA, SA | Analytics Q&A interface and LLM policy ADRs must converge. |

---

## How to Use This File

1. Read the Decision Classification section first. Understand the difference between IC, SA, and D.
2. Work through decisions in **deadline order** (Week 1 first).
3. **For SA decisions:** Research alternatives, evaluate tradeoffs, and produce ADR files in `docs/adr/`. Each ADR must converge before the team implements the agent that depends on that decision. The Reference Implementation column shows what downstream exercises assume if your team does not converge on a different choice.
4. **For IC decisions:** Understand why they are fixed. You do not write ADRs for these — they are constraints to work within.
5. **For D decisions:** Note them as future decision points. No action required in Phase 1.
6. When an SA decision converges, update **Status** to ✅ Resolved and fill in **Decision Made**.
7. Copy each resolved decision into `CLAUDE.md` under `## Design Decisions` so Claude Code always has the latest context.
8. Bring any unresolved SA decisions approaching their deadline to the next planning session.
