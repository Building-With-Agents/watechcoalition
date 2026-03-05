# Job Intelligence Engine — Architectural Decisions

**Layer:** System Design (HOW — produced through the DDR process in Sprint Design)
**Audience:** Engineering leads, program staff, Claude Code
**Status:** Living document — updated as decisions are resolved
**Last updated:** 2026-03-03

---

## What This Document Is

This document records **system-level decisions** for the Job Intelligence Engine —
decisions whose consequences cross agent boundaries and affect the pipeline as a
whole. It answers HOW the system is implemented, not WHAT it does.

The architecture (WHAT) is defined in `ARCHITECTURE_DEEP.md`.

**Scope boundary:**
- **In this document:** Decisions that affect multiple agents — framework choices,
  data model shape, communication patterns, cross-cutting system contracts,
  pipeline topology.
- **Not in this document:** Decisions about how a single agent handles a problem
  internally. Those belong in per-agent design documents.

**Per-agent design documents** (in `references/`):

| Agent | Design document | Per-agent decisions it contains |
|---|---|---|
| Ingestion | `ingestion-agent-design.md` | JSearch source priority, dedup fingerprint, Crawl4AI + httpx tool choice |
| Normalization | `normalization-agent-design.md` | Per-source field mappers, quarantine strategy, field normalisation rules |
| Skills Extraction | `skills-extraction-agent-design.md` | Skill taxonomy primary source, 5-step linking cascade, eval dataset, prompt versioning |
| Enrichment | `enrichment-agent-design.md` | Spam detection thresholds, quality scoring, Phase 1 lite scope, company resolution |
| Analytics | `analytics-agent-design.md` | REST query interface, 6 aggregation dimensions, SQL guardrails, AI relevance (deferred) |
| Visualization | `visualization-agent-design.md` | PDF export scope, 6 dashboard pages, TTL cache strategy |
| Orchestration | `orchestration-agent-design.md` | Alerting tiers, per-agent retry policies, circuit breaker, audit log |

**Note on numbering:** Numbers are assigned in the order decisions were first
recorded, not the order they must be resolved. Gaps in the sequence (where
per-agent decisions have been moved out) are intentional. Use the Critical Path
Summary at the bottom to find what must be decided by when.

---

## Decision Types

Each decision is labelled with one of these types so the reader knows how much
weight it carries and who owns it.

| Type | Meaning | Change cost |
|---|---|---|
| **Architectural** | System-shaping; affects multiple agents; hard to reverse | High — requires coordinated changes across agents |
| **Contract** | System-wide interface requirement every agent must honour | High — breaking a contract breaks every agent |
| **Tool** | Specific implementation behind an abstraction; swappable | Low — swap the concrete class, not the agents |
| **Product** | What the system prioritises; driven by user or business needs | Medium — config change or data relabeling |

---

## Decision Status at a Glance

### Resolved

| # | Type | Decision | Resolution |
|---|---|---|---|
| 3 | Architectural | Batch vs real-time | Batch-first — APScheduler, daily cron (`0 2 * * *`) |
| 4 | Architectural | Source of truth for ingested jobs | Staging tables + promotion (`raw_ingested_jobs` → `normalized_jobs` → `job_postings`) |
| 11 | Tool | LLM provider | Provider-agnostic adapter — Azure OpenAI default, switchable via `LLM_PROVIDER` env var |
| 13 | Architectural | Multi-agent framework | LangGraph StateGraph |
| 14 | Architectural | Message bus | In-process Python events (Phase 1); external bus upgrade path for Phase 2 |
| 16 | Architectural | Orchestration engine | LangGraph StateGraph |
| 17 | Tool | Agent tracing | LangSmith — native LangGraph integration |
| 19 | Architectural | Database engine | PostgreSQL — single instance, pgvector-enabled, shared by Next.js app and agent pipeline |
| 25 | Contract | Next.js / Python layer boundary | Prisma is Next.js-only — never imported or invoked from Python. Python agents access PostgreSQL via SQLAlchemy only |
| 26 | Contract | Abstraction layer mandate | All swappable tools sit behind ABCs: `SourceAdapter`, `EventBusBase`, `TracerBase`, `AgentBase` |
| 27 | Contract | Logging library | structlog — JSON format, keyword arguments, no PII in any log line |
| 28 | Contract | Agent health interface | Every agent exposes `health_check() → dict` — returns `{"status": "ok"\|"degraded"\|"down", "agent": str, "last_run": str, "metrics": dict}`, called by Orchestration Agent before scheduling |
| 29 | Contract | Correlation ID propagation | Set once at pipeline entry, propagated unchanged through every downstream event |
| 30 | Contract | Taxonomy store abstraction | `TaxonomyStoreBase` ABC — concrete implementation switchable via `TAXONOMY_STORE` env var. Phase 1: `PostgreSQLTaxonomyStore`. Phase 2: `LightcastTaxonomyStore` |

### Open — Must Resolve Before Build

| # | Type | Decision | Must Resolve By | Owner |
|---|---|---|---|---|
| 1 | Product | Job classification taxonomy | Week 4 | Ritu (product decision) + Gary (technical feasibility) |

### Deferred to Phase 2

| # | Type | Decision | Trigger for revisiting |
|---|---|---|---|
| 2 | Tool | ML hosting | Model size > 2GB or training time > 4 hours per cycle |
| 5 | Architectural | Vector store scaling | Week 9 near-dedup shows PostgreSQL + pgvector queries exceed 500ms p50 at scale |
| 22 | Architectural | Multi-tenancy | Before any Phase 2 work serving a second organisation |
| 23 | Architectural | Feedback loop agent | When prompt versioning resolved AND ground truth source defined AND training pipeline exists |

---

## Resolved Decisions — Full Records

---

### #3 — Batch-First vs Real-Time-First

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | Batch-first / Real-time-first |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | Batch-first — APScheduler, daily cron default (`0 2 * * *`) |

**Rationale:** Job postings are not time-critical at the minute level. A job
posted this morning is still relevant this evening. Real-time-first adds
significant complexity — streaming connectors, backpressure handling, stateful
dedup across a live stream — that is not justified by the use case. Batch-first
aligns naturally with APScheduler and makes evaluation simpler: run a batch,
measure results, iterate. Real-time would only be warranted if job seekers needed
postings within seconds of publication. That is not a stated requirement.

**Phase 2 path:** The event contract (`IngestBatch`) and staging table design
support real-time if it ever becomes a product requirement. Source adapters would
need streaming variants; no structural change to the pipeline.

---

### #4 — Source of Truth for Ingested Jobs

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | Extend `job_postings` directly / Staging tables + promotion |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | Staging tables + promotion: `raw_ingested_jobs` → `normalized_jobs` → `job_postings` |

**Rationale:** Ingested jobs arrive without `company_id` and `location_id`, which
`job_postings` requires as foreign keys. Staging lets records be held until
downstream agents resolve these references before touching the canonical table.
It also makes the pipeline fully replayable — normalization or skills extraction
can be re-run from `raw_ingested_jobs` without affecting production data. Writing
directly to `job_postings` would pollute it with partially-resolved records and
remove the ability to distinguish employer-created from agent-ingested jobs at
the schema level.

---

### #11 — LLM Provider Policy

| Field | Value |
|---|---|
| **Type** | Tool |
| **Options** | Fixed provider / Provider-agnostic adapter |
| **Status** | ✅ Resolved — Must resolve before Week 2 |
| **Decision** | Provider-agnostic adapter — Azure OpenAI default, switchable via `LLM_PROVIDER` env var |

**Rationale:** The adapter is scaffolded in Week 2. Azure OpenAI is the default
(already integrated via `app/lib/openAiClients.ts`). Switchable to Anthropic or
OpenAI via a single env var change — no code changes required. Fallback rule: if
the configured provider fails after 2 retries, log the failure, skip LLM
processing for that record, and flag it for re-processing. This future-proofs
against provider outages without additional architecture work.

---

### #13 — Multi-Agent Framework

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | LangGraph, CrewAI, AutoGen, Semantic Kernel, Custom |
| **Status** | ✅ Resolved — Must resolve before Week 1 |
| **Decision** | LangGraph StateGraph |

**Rationale:** LangGraph's StateGraph maps directly to the eight-agent pipeline —
agents are nodes, events are edges, the Orchestration Agent controls routing.
Python-native — and because LangGraph requires Python, this decision also
determines the agent runtime language. There was no genuine deliberation between
Python and Node.js; the framework choice made the language choice. Integrates
with LangChain (needed for #11) and pairs with LangSmith (#17) — one
instrumentation setup covers everything. The architecture is framework-agnostic
at the event-contract level, so switching later is possible without rewriting
event definitions or agent interfaces (see #26 — abstraction layer mandate).

CrewAI: optimised for role-based agent collaboration, not a sequential data
pipeline. AutoGen: conversation-oriented, poor fit for a structured ETL-style
pipeline. Semantic Kernel: .NET-native. Custom: adds significant build overhead
with no upside at this scale.

*Validated by EXP-007 (framework spike) — findings in `references/ingestion-agent-design.md`.*

---

### #14 — Message Bus Technology

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | In-process Python events, Kafka, RabbitMQ, Redis Streams |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | In-process Python events for Phase 1; external bus upgrade path for Phase 2 |

**Rationale:** Kafka and RabbitMQ add infrastructure overhead — separate services,
connection management, serialisation — that slows down Weeks 1–9 without
meaningful benefit at current scale. The event envelope contracts are bus-agnostic:
migrating to an external bus in Phase 2 requires replacing only the `EventBusBase`
implementation, not event definitions or agent logic. Phase 2 trigger: multi-process
or multi-machine agent deployment.

**Enforcement rule:** Only the Orchestration Agent subscribes to `*Failed` and
`*Alert` events. No other agent reacts to another agent's failures. This rule is
enforced at the event bus subscription layer — `*Failed` and `*Alert` topics are
reserved for the Orchestration Agent only.

*Validated by EXP-004 (event bus spike) — findings in `references/ingestion-agent-design.md`.*

---

### #16 — Orchestration Engine

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | LangGraph StateGraph, Temporal, Prefect, Airflow, Custom |
| **Status** | ✅ Resolved — Must resolve before Week 6 |
| **Decision** | LangGraph StateGraph |

**Rationale:** Using LangGraph for both agent graphs (#13) and orchestration keeps
the stack unified — one framework to learn, one tracing integration, one set of
concepts for the entire program. A student building the Orchestration Agent in
Week 6 works in the same mental model as the student who built the Ingestion
Agent in Week 3. The `StateGraph` model expresses scheduling, retry routing, and
alert escalation paths as conditional edges — the same pattern used in every
other agent.

Temporal and Prefect are excellent workflow orchestrators but are separate
services adding infrastructure overhead not justified at this scale. Airflow:
better suited for data pipelines than agent orchestration. Custom: adds
significant build overhead with no upside.

---

### #17 — Agent Tracing

| Field | Value |
|---|---|
| **Type** | Tool |
| **Options** | LangSmith, OpenTelemetry + custom spans, Langfuse, Arize Phoenix |
| **Status** | ✅ Resolved — Must resolve before Week 1 |
| **Decision** | LangSmith — native LangGraph integration |

**Rationale:** Purpose-built for LLM agent tracing. Integrates directly with
LangGraph — every node execution, state transition, and LLM call is captured
automatically with no custom span instrumentation. For a program where visibility
into agent behaviour is a core learning outcome, LangSmith's trace UI is
significantly more useful than raw log lines or generic telemetry spans. Free
tier available.

Sits behind `TracerBase` (#26) — if self-hosting is required, Langfuse is the
drop-in alternative. OpenTelemetry is the fallback for fully offline environments.

*Validated by EXP-006 (observability spike) — findings in `references/ingestion-agent-design.md`.*

---

### #19 — Database Engine

| Field | Value |
|---|---|
| **Type** | Architectural |
| **Options** | MSSQL / PostgreSQL |
| **Status** | ✅ Resolved — Phase 1 |
| **Decision** | PostgreSQL — single instance shared by the Next.js app (via Prisma) and the agent pipeline (via SQLAlchemy) |

**Rationale:** PostgreSQL is chosen on technical merit, unconstrained by any prior
platform choice.

**The decisive reason — pgvector:** The Skills Extraction Agent's taxonomy cascade
(step 3) and the Week 9 near-dedup work both require embedding cosine similarity
search. PostgreSQL's `pgvector` extension handles this natively with an ANN index —
one SQL query. Without it, the agent must load the entire embedding matrix into
Python memory at startup and compute similarity in-process — acceptable for a
small `skills` table, but not scalable for near-dedup across tens of thousands of
job descriptions.

**Python ecosystem fit:** PostgreSQL is the standard database in the Python and
data engineering world. `psycopg2`/`asyncpg` are pip-installable with no system
dependencies. `docker run postgres:16` is a one-line setup. MSSQL requires
system-level ODBC drivers, a larger Docker image, and accepted licensing terms —
friction that costs curriculum time and adds no learning value.

**Simpler type system:** PostgreSQL's `TEXT`, `TIMESTAMPTZ`, and `BOOLEAN` map
directly to Python types with no special handling. MSSQL required explicit
choices at every column (NVARCHAR vs VARCHAR, DATETIME2 vs DATETIME, BIT vs
BOOLEAN) — all eliminated.

**Single instance:** The Next.js app migrates its Prisma connection string from
MSSQL to PostgreSQL. Both layers share one PostgreSQL instance. Direct joins
between agent tables and platform tables (`skills`, `companies`, `job_postings`)
work natively. No cross-database bridging needed.

*Validated by EXP-002 (database spike) — findings in `references/ingestion-agent-design.md`.*

---

### #25 — Next.js / Python Layer Boundary

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | Shared access across layers / Hard layer separation |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | Prisma is Next.js-only — never imported or invoked from Python. Python agents access PostgreSQL via SQLAlchemy only |

**Rationale:** The Job Intelligence Engine is two separate layers running
alongside each other: a Next.js application and a Python agent pipeline. These
layers must not reach into each other's internals. Prisma is the Next.js
application's database interface — its schema, migration history, and client
are owned by that layer. Any Python import of Prisma would couple the agent
layer to the application layer in a way that breaks when either is updated
independently.

SQLAlchemy is the consequence of this boundary, not the decision itself. Once
Prisma is off-limits, SQLAlchemy is the natural Python ORM for PostgreSQL access —
it provides sessions, connection pooling, and testable mock interfaces that raw
psycopg2 does not.

**Hard rule enforced across all agents:** No file in `agents/` ever imports
Prisma or calls the Prisma CLI. No Python file ever modifies `prisma/schema.prisma`.
Any agent that needs database access uses SQLAlchemy models defined in its own
`models.py`.

---

### #26 — Abstraction Layer Mandate

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | Direct tool usage throughout / Tools behind ABCs |
| **Status** | ✅ Resolved — Must resolve before Week 1 |
| **Decision** | All swappable tools sit behind abstract base classes: `SourceAdapter`, `EventBusBase`, `TracerBase`, `AgentBase`, `TaxonomyStoreBase` |

**Rationale:** The highest-risk decisions in the system — framework (#13), event
bus (#14), tracing tool (#17), source tools (Ingestion Agent), taxonomy store (#30)
— are also the most likely to be swapped as real experiments reveal what works.
If tools are called directly throughout the codebase, swapping one requires
touching every agent. If tools sit behind ABCs, swapping requires replacing one
concrete class.

Concretely: LangGraph is implemented via `AgentBase`. LangSmith is implemented
via `TracerBase`. In-process events are implemented via `EventBusBase`. The
taxonomy store is implemented via `TaxonomyStoreBase`. Each can be swapped by
providing a new concrete class — no agent logic changes required.

This is the single most important architectural constraint in the system.
Violating it means technical debt compounds with every new agent added.

---

### #27 — Logging Library

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | structlog / Standard Python `logging` / print statements |
| **Status** | ✅ Resolved — Must resolve before Week 1 |
| **Decision** | structlog across all agents — JSON format, keyword arguments |

**Rationale:** structlog produces machine-readable JSON log events. Every field
(`run_id`, `source`, `record_count`, `error_code`) is a queryable key-value pair —
no regex parsing required. Standard `logging` produces free-text lines. `print`
statements are untraceable in production.

**Hard rule enforced across all agents:** No PII in any log line. Job
descriptions, company contact information, applicant data, and tracking URLs
are never logged, by any agent.

---

### #28 — Agent Health Interface

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | No standard interface / `health_check()` on every agent |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | Every agent exposes `health_check() → dict`. Returns `{"status": "ok"\|"degraded"\|"down", "agent": str, "last_run": str, "metrics": dict}`. The Orchestration Agent calls it before scheduling any run and aborts if any Phase 1 agent returns `status != "ok"` |

**Rationale:** Without a standard health check, the Orchestration Agent has no
way to know if a downstream agent is ready before committing resources to a run.
A downed DB connection, unreachable API, or misconfigured adapter would only
surface as a failed run — after time and API quota were already consumed.

`health_check()` must never raise. It catches all exceptions internally and
reflects them in the returned status dict. The dict always includes
`status: "healthy" | "degraded" | "unhealthy"`. Returns `"degraded"` if some
dependencies are reachable but not all. Returns `"unhealthy"` only if the agent
cannot perform its core function.

---

### #29 — Correlation ID Propagation

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | No correlation ID / Per-agent IDs / Single ID across full pipeline |
| **Status** | ✅ Resolved — Must resolve before Week 3 |
| **Decision** | `correlation_id` is set once at pipeline entry (Ingestion Agent, one per batch) and propagated unchanged through every downstream event |

**Rationale:** Without a shared correlation ID, tracing a single job posting
through the full pipeline requires joining on record IDs across multiple tables
and log files — archaeology, not debugging. With a `correlation_id` on every
event, any log aggregation or tracing tool can filter to one ID and show the
complete lifecycle of a batch.

**Hard rule:** Never generate a new `correlation_id` mid-pipeline. Never strip
it from an event before emitting. The Normalization Agent copies it from
`IngestBatch` into `NormalizationComplete`. Every subsequent agent does the same.

---

### #30 — Taxonomy Store Abstraction

| Field | Value |
|---|---|
| **Type** | Contract |
| **Options** | Direct DB queries in agent / `TaxonomyStoreBase` ABC |
| **Status** | ✅ Resolved — Must resolve before Week 4 |
| **Decision** | `TaxonomyStoreBase` ABC — concrete implementation switchable via `TAXONOMY_STORE` env var |

**Rationale:** The taxonomy data source is a natural variation point. Phase 1
seeds the local PostgreSQL instance from a configurable external source (Lightcast,
O\*NET, or manual curation). Phase 2 may query Lightcast's Skills API live instead
of relying on a seeded local copy. If the Skills Extraction Agent queries the
database directly, switching the source requires changes in agent code. The ABC
isolates this.

**The four methods map directly to the taxonomy cascade steps:**

```python
class TaxonomyStoreBase(ABC):
    def lookup_exact(self, name: str) -> Optional[TaxonomySkill]: ...
    def lookup_normalized(self, name: str) -> Optional[TaxonomySkill]: ...
    def lookup_by_embedding(self, embedding: list[float], threshold: float) -> Optional[TaxonomySkill]: ...
    def lookup_by_onet(self, occupation_code: str, skill_name: str) -> Optional[TaxonomySkill]: ...
```

**Phase 1 concrete implementation:** `PostgreSQLTaxonomyStore` — queries the
`skills` table and pgvector index in the local PostgreSQL instance. The taxonomy
data is seeded at setup time from a configurable source (Lightcast API default;
see `agents/setup/seed_taxonomy.py`).

**Phase 2 option:** `LightcastTaxonomyStore` — queries the Lightcast Skills API
live, bypassing the local seed. Switch via `TAXONOMY_STORE=lightcast` env var.
Requires `LIGHTCAST_API_KEY`.

**Mock for testing:** `MockTaxonomyStore` — returns deterministic fixture data.
No database connection required. Used in all unit tests.

---

## Open Decisions

---

### #1 — Job Classification Taxonomy

| Field | Value |
|---|---|
| **Type** | Product |
| **Options** | SOC codes / Internal taxonomy (`technology_areas`, `pathways`, `industry_sectors`) / Hybrid |
| **Status** | ⬜ Open — must resolve before Week 4 |
| **Owner** | Ritu (product decision) + Gary (technical feasibility check) |

**Why this is system-level:** The job classification taxonomy is not just a
Skills Extraction decision. It determines what the `role` and `seniority` fields
in `job_postings` mean (Enrichment Agent), what dimensions Analytics aggregates
across (Analytics Agent), and what labels appear in the Visualization Agent
dashboards. All four agents must agree on the same classification scheme.

**Recommendation:** Internal taxonomy primary (`technology_areas`, `pathways`,
`industry_sectors`), SOC codes secondary. Classifying against the internal
taxonomy keeps output immediately usable in the existing platform. SOC codes are
already partially supported via `occupation_code` on `job_postings`, so appending
a SOC code alongside the internal classification costs little and adds
labour-market interoperability for Phase 2 (Demand Analysis uses SOC codes).

---

## Deferred Decisions

---

### #2 — ML Hosting

**Type:** Tool

**Recommendation:** Stay in-repo (`agents/`). Trigger for revisiting: model size
exceeds 2GB or training time exceeds 4 hours per cycle. Until then, in-repo keeps
setup friction low. Migrate to Azure ML only if those thresholds are crossed.

---

### #5 — Vector Store Scaling

**Type:** Architectural

**Recommendation:** PostgreSQL + pgvector for Phase 1. Trigger for revisiting:
Week 9 near-dedup work shows pgvector similarity queries exceed 500ms p50 at
production scale after HNSW index tuning. If triggered, evaluate a dedicated
vector database (Pinecone, Weaviate, or Qdrant) as a sidecar for similarity
workloads only — not a full migration. The `TaxonomyStoreBase` ABC (#30) means
swapping the vector backend requires one concrete class swap with no changes to
agent logic.

---

### #22 — Multi-Tenancy

**Type:** Architectural

**Recommendation:** Single shared pipeline for Phase 1. Trigger for revisiting:
before any Phase 2 work serving a second organisation. The event envelope already
supports a `tenant_id` field in the payload — it just isn't populated. Pipeline
table schemas will need partitioning by tenant before multi-tenancy is viable.

---

### #23 — Feedback Loop Agent

**Type:** Architectural

**Recommendation:** Defer to Phase 2. All three prerequisites must be met before
this is viable: (1) prompt versioning resolved (see `skills-extraction-agent-design.md`),
(2) a defined ground truth source (who provides corrections, in what format),
(3) a working training pipeline. The evaluation harness built in Week 4 produces
labeled data that could seed a feedback loop — that is the Phase 1 foundation.

---

## Critical Path Summary

| By | Decisions | Why |
|---|---|---|
| Week 1 | #13 ✅, #26 ✅, #27 ✅, #17 ✅ | Framework (which also determines runtime language), abstraction mandate, logging, and tracing must be chosen before any agent code is written |
| Week 2 | #11 ✅ | LLM adapter is scaffolded in Week 2 — provider policy must be locked |
| Week 3 | #3 ✅, #4 ✅, #14 ✅, #19 ✅, #25 ✅, #28 ✅, #29 ✅ | PostgreSQL schema, message bus, data access layer, health interface, and correlation ID must all be established before agents hand off to each other |
| Week 4 | #1 ⬜, #30 ✅ | Classification taxonomy and taxonomy store ABC must be locked before Skills Extraction Agent is built |
| Week 6 | #16 ✅ | Orchestration Agent is built — orchestration engine must be locked |
