# Job Ingestion & Intelligence Agent — Introduction (Agent-First)

## 1. Purpose and Scope
This document reframes the Job Ingestion & Intelligence Agent as an agent-first system. It aligns the internship plan as the delivery cadence while preserving BRD and TRD requirements and constraints. This version supersedes prior stack recommendations and is the finalized planning baseline.

## 2. Source of Truth and Alignment
Primary source of truth for schedule and weekly milestones:
- `c:\Users\garyl\Desktop\BWA - Copilot Studio\internship project plan agent first.docx`

Authoritative requirements and constraints:
- `docs/planning/JOB_INGESTION_AGENT_BRD.md`
- `docs/planning/JOB_INGESTION_AGENT_TRD.md`

Alignment rules
- The internship plan sets delivery cadence, weekly milestones, and build order.
- The BRD sets business scope, success criteria, and design decisions.
- The TRD sets architecture, integration points, and NFRs.
- If the internship plan conflicts with BRD or TRD constraints, BRD and TRD win.

## 3. Current Project Environment
- Primary app stack: Node.js/TypeScript with Prisma and MSSQL.
- Existing LLM integration: Azure OpenAI client in `app/lib/openAiClients.ts`.
- Core schema: `job_postings`, `companies`, `company_addresses`, `skills`, `technology_areas`, `industry_sectors`.
- Existing job creation flow: `app/lib/joblistings.ts` and `app/api/joblistings/add/route.ts`.

## 4. Agent-First Architecture
Agents are bounded services with explicit inputs, outputs, tools, and policies. Deterministic agents are built first. LLM agents are added only where deterministic logic is insufficient.

Core pipeline agents
- Ingestion Agent (deterministic). Pulls from sources, normalizes payloads, writes raw data with idempotency keys and batch IDs.
- Dedup and Normalization Agent (deterministic plus embeddings optional). Exact and fuzzy dedup, canonical record creation.
- Extraction Agent (LLM optional). Produces structured fields with confidence and field-level provenance.
- Classification Agent (ML optional). Role, seniority, quality, and spam scoring with clear fallbacks.
- Validation Agent (deterministic). Enforces required fields and schema mapping to `job_postings`.

Operational agents
- Analysis Agent (LLM optional). Summarizes weekly trends and generates operational insights.
- Q&A Agent (LLM optional). Natural language questions mapped to SQL and verified outputs.
- Alert Agent (deterministic). Triggers alerts for quality issues, spam spikes, or demand changes.

## 5. Stack Refactor (Agent-First)
This plan intentionally revises the stack to optimize for agent development and observability. It does not preserve backward compatibility with the previous stack plan.

Recommended stack for first implementation
- Agent runtime: Python for agent services and dashboards to align with agent frameworks and Streamlit.
- Data access: MSSQL via SQLAlchemy + `pyodbc` for agents; Prisma remains for the main app.
- Orchestration: APScheduler for predictable batch runs; add a queue if required later.
- LLM integration: provider-agnostic adapter layer with runtime selection.
- Observability: LangSmith optional for LLM calls; OpenTelemetry or structured logs for deterministic agents.
- Dashboards: Streamlit as a separate read-only analytics app.

## 6. LLM Provider Strategy (No Lock-In)
LLM usage is limited to agents that require reasoning or language generation. Provider selection must be configuration-based, not hard-coded.

LLM policy
- Provide a single interface for prompts, tools, and structured outputs.
- Allow runtime provider selection (Azure OpenAI, Anthropic, OpenAI, or local models).
- Log prompts, model versions, and outputs for audit and evaluation.
- Use deterministic alternatives when comparable quality is achievable.

## 7. Streamlit for Dashboards and Analysis
Streamlit is a separate Python app that reads from the same data sources for dashboards, evaluation, and operational review. It does not replace the Next.js app.

Where Streamlit fits
- Observability dashboards: LLM latency, extraction failure rates, classification confidence, dedup stats, spam and quality distributions.
- Evaluation and analysis: precision, recall, F1, quality correlation, extraction error analysis.
- Operational review: low-confidence jobs, spam-flagged items, duplicate clusters.
- Ad hoc analysis: source mix, skill coverage, and trend exploration.

Data access options
| Option | Pros | Cons |
|--------|------|------|
| Direct MSSQL from Python | One source of truth, real-time. | Requires DB credentials and network access for Streamlit; schema coupling. |
| `pyodbc` / `sqlalchemy` | Standard, works with Pandas. | Must maintain connection string and auth. |
| Read-only DB user | Safe for dashboards. | Another user to manage. |
| Export to file (CSV/Parquet) | No DB access from Streamlit; good for eval datasets. | Not real-time; needs export job. |
| REST API from Next.js | Reuse auth and business logic. | Requires new internal API routes. |

## 8. Internship Plan Alignment (12 Weeks)
Phase 1 (Weeks 1-2): Thin vertical slice
- Deliver a working end-to-end pipeline with one source, basic extraction, and Streamlit display.

Phase 2 (Weeks 3-6): Deterministic agents and NLP upgrades
- Build the Ingestion Agent and Alert Agent without LLMs.
- Improve extraction and taxonomy mapping.

Phase 3 (Weeks 7-10): LLM agents and scale
- Add Analysis and Q&A agents with provider-agnostic LLM integration.
- Harden pipelines, improve dedup accuracy, and scale data volume.

Phase 4 (Weeks 11-12): Documentation and demo
- Complete documentation, finalize dashboards, and deliver capstone demo.

Build order
- Ingestion Agent -> Alert Agent -> Analysis Agent -> Q&A Agent.

## 9. Integration Points in the Codebase
- Azure OpenAI client: `app/lib/openAiClients.ts`.
- Job creation flow: `app/lib/joblistings.ts` and `app/api/joblistings/add/route.ts`.
- Schema references: `prisma/schema.prisma`.
- Planning docs: `docs/planning/JOB_INGESTION_AGENT_BRD.md`, `docs/planning/JOB_INGESTION_AGENT_TRD.md`.

## 10. Key Design Decisions and Open Questions
- Taxonomy (SOC vs internal taxonomy).
- ML hosting (in-repo vs separate service).
- Batch-first vs real-time-first.
- Source of truth for ingested jobs (same table vs separate staging tables).
- Storage (MSSQL only vs vector DB for semantic dedup).
- Evaluation dataset ownership and format.
- AI relevance ground truth definition.
- Spam threshold policy (reject vs flag).
- Deduplication source priority.
- Versioning strategy for prompts and models.
- LLM provider selection and fallback policy.
- Scraping implementation for the Ingestion Agent (Firecrawl, Crawl4AI, ScrapeGraphAI, Browser-use, Spider).

## 11. Risks and Constraints
- LLM variability requires schema, retries, and confidence scoring.
- Model availability requires fallbacks if LLM services are unavailable.
- Source changes (JSearch, scraping targets) require versioned adapters and monitoring.
- Schema drift requires validation and enforcement of required fields.
- Performance constraints: batch 1,000 jobs < 5 minutes; individual scoring < 2 seconds.

## 12. Evaluation and Observability
- Metrics: dedup precision and recall, extraction F1, classification accuracy, spam precision, quality correlation.
- Logging: LLM latency, extraction failures, retry counts, dedup decisions.
- Dashboards: Streamlit provides visibility into model performance and operational queues.
- Feedback loop: evaluation results adjust prompts, thresholds, and models.

## 13. First Implementation Approach (Based on Current State)
- Stand up agent services in Python that read and write MSSQL.
- Add ingestion and staging tables as needed to preserve existing `job_postings` usage.
- Keep Next.js as the primary user-facing surface; agents populate data behind it.
- Defer vector DB until scale requires persistent semantic search.
- Keep LLM provider selection in environment config.

## 14. Appendix: Suggested Streamlit Views
- Ingestion overview by source and run.
- Extraction confidence distributions and failures.
- Classification distributions and score histograms.
- Dedup clusters and merge counts.
- Review queue for low-confidence or spam-flagged jobs.
- Evaluation summary (precision, recall, and F1 trends).

## 15. Appendix: Scraping Tool Options (Ingestion Agent)

These tools are candidate implementations for the Ingestion Agent's scraping capability. The agent contract (raw job shape, idempotency, source identifier) is independent of tool choice.

| Tool | Core Strength | Primary Use Case |
|------|---------------|------------------|
| **Firecrawl** | Managed infrastructure, /agent endpoint | Rapid, reliable extraction for AI assistants |
| **Crawl4AI** | Local-first, adaptive pattern learning | Privacy-focused or heavy-volume local scraping |
| **ScrapeGraphAI** | Natural language definitions | No-code scraping logic for changing layouts |
| **Browser-use** | Direct browser control | Sites requiring complex interactions or logins |
| **Spider** | Extreme speed (Rust-based) | Mass aggregation across thousands of URLs |

