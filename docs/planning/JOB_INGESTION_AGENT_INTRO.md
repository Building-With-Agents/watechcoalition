# Job Ingestion & Intelligence Agent — Introduction

## 1. Purpose and Scope
This document introduces the Job Ingestion & Intelligence Agent and explains how to use the BRD and TRD together to guide architecture and implementation for the watechcoalition codebase. It also aligns the plan to the 12-week internship project plan while preserving BRD/TRD scope, success criteria, and constraints.

## 2. Source of Truth and Alignment
Primary source of truth for delivery cadence and weekly milestones:
- `c:\Users\garyl\Desktop\BWA - Copilot Studio\internship project plan.docx`

Authoritative requirements and constraints:
- `docs/planning/JOB_INGESTION_AGENT_BRD.md`
- `docs/planning/JOB_INGESTION_AGENT_TRD.md`

Alignment rules
- The internship plan defines the schedule, weekly deliverables, and learning outcomes.
- The BRD defines business scope, success criteria, and design decisions.
- The TRD defines architecture, integration points, and non-functional requirements.
- If the internship plan conflicts with BRD/TRD constraints, BRD/TRD wins for implementation details.

## 3. Current Project Environment
- Primary app stack: Node.js/TypeScript with Prisma and MSSQL.
- LLM provider: Azure OpenAI (already integrated via `app/lib/openAiClients.ts`).
- Data model: `job_postings`, `companies`, `company_addresses`, `skills`, `technology_areas`, `industry_sectors`.
- Existing job creation flow: `app/lib/joblistings.ts` and `app/api/joblistings/add/route.ts`.
- Planning artifacts: BRD and TRD in `docs/planning/` define scope, success criteria, and technical requirements.

## 4. How to Use BRD and TRD Together
- Start with BRD to confirm scope, success criteria, and unresolved design decisions.
- Use the TRD to translate BRD choices into concrete architecture, data flow, and integrations.
- Implement iteratively and validate against BRD metrics and TRD NFRs.

## 5. Architecture Overview (High Level)
Pipeline stages: Sources -> Ingestion -> Deduplication -> LLM Extraction -> ML Classification -> Post-Processing and Validation -> Persistence.

Key data artifacts
- Raw job: source payload and metadata, idempotent and replayable.
- Canonical job: structured output with normalized fields and confidence scores.
- Persisted job: mapped to `job_postings` plus new ingestion-specific fields (per TRD decisions).

## 6. Recommended Stack (Pros, Cons, and Feedback)

### 6.1 Orchestration and Runtime
Recommendation: Keep ingestion, dedup, and post-processing in Node/TypeScript. Add a Python service for ML inference only when you need model training or heavier ML workloads.

Pros
- Reuses existing Node/TS, Prisma, and API integration.
- Keeps ingestion and persistence logic in one runtime.
- Supports batch-first workflows aligned with BRD performance targets.

Cons
- Dual-runtime (Node + Python) adds deployment and interface complexity.
- Temporal adds infrastructure and onboarding overhead compared to BullMQ.

Feedback
- Start with BullMQ for batch workflows and retries. If workflows grow more complex, evaluate Temporal later.

### 6.2 LLM Extraction
Recommendation: Use Azure OpenAI for production extraction. Use local open-source models for testing and prompt iteration only.

Pros
- Azure OpenAI already integrated and compliant with current environment.
- Structured output reduces parsing fragility.

Cons
- Cost and vendor dependency at scale.
- OSS models may struggle with noisy job postings.

Feedback
- Keep schema, prompt versions, and retry logic in-repo to enable model swaps later.

### 6.3 ML Classification and Scoring
Recommendation: Start with scikit-learn or LightGBM in Python for role, seniority, quality, and spam. Serve via a minimal FastAPI service or export to ONNX for Node inference.

Pros
- Strong baseline performance with modest effort.
- Clear separation of training and inference concerns.

Cons
- Requires labeled data and an evaluation harness (TBD in BRD).
- Drift monitoring adds ongoing work.

Feedback
- Prioritize building a small, high-quality evaluation dataset before optimizing model complexity.

### 6.4 Deduplication
Recommendation: Use a tiered approach: exact hash -> fuzzy matching -> semantic similarity. Keep this in Node for the initial phase.

Pros
- Fast and cost-effective for most duplicates.
- Semantic layer improves recall.

Cons
- Semantic similarity can produce false positives without strong thresholds.
- Embedding calls add latency and cost.

Feedback
- Log dedup decisions and store thresholds in config to support tuning against BRD metrics.

### 6.5 Vector Store (Optional)
Recommendation: Defer vector DB until scale or product needs justify it.

Pros
- Persistent similarity search and clustering at scale.

Cons
- Adds operational overhead and extra infrastructure.

Feedback
- Start in-process; revisit if dataset size or query patterns demand it.

### 6.6 Observability
Recommendation: Use JSON logging (Pino) and metrics and tracing (OpenTelemetry) aligned with TRD NFRs.

Pros
- Enables SLO tracking and model quality monitoring.

Cons
- Instrumentation adds initial setup and ongoing tuning.

Feedback
- Track a small, high-signal set of metrics first: throughput, LLM failures, dedup rates, model confidence distributions.

## 7. Streamlit for Dashboards and Analysis
Streamlit is a separate Python app that reads from the same data sources for dashboards, evaluation, and operational review. It does not replace the Next.js app and should be treated as a read-only analytics surface.

Where Streamlit fits
- Observability dashboards: LLM latency, extraction failure rates, classification confidence, dedup stats, spam and quality distributions.
- Evaluation and analysis: precision and recall, F1, quality vs human rating correlation, extraction error analysis.
- Operational review: low-confidence jobs, spam-flagged items, duplicate clusters for manual review.
- Ad hoc analysis: one-off queries on ingested jobs, skill coverage, source mix.

Data access options
| Option | Pros | Cons |
|--------|------|------|
| Direct MSSQL from Python | One source of truth, real-time. | Requires DB credentials and network access for Streamlit; schema coupling. |
| `pyodbc` / `pymssql` / `sqlalchemy` | Standard, works with Pandas. | Must maintain connection string and auth. |
| Read-only DB user | Safe for dashboards. | Another user to manage. |
| Export to file (CSV/Parquet) | No DB access from Streamlit; good for eval datasets. | Not real-time; needs export job. |
| REST API from Next.js | Reuse auth and business logic. | Requires new internal API routes. |

Practical approach
- Use SQLAlchemy + `pyodbc` (or `pymssql`) with a read-only connection string in Streamlit env.
- Use Pandas for transformations and Plotly or Altair for charts.
- Keep evaluation datasets in CSV or Parquet for offline analysis.
- If restricted access is required, add a reverse proxy with auth or use Streamlit authentication.

## 8. Internship Plan Alignment (12 Weeks)
The internship plan provides the delivery cadence and milestones. The BRD and TRD define what must be built and how it integrates with the existing application.

Phase 1 (Weeks 1-2): Thin vertical slice
- Deliver a working end-to-end pipeline that ingests a small sample, extracts structured fields, and displays results.
- Aligns to TRD Sections 4.1, 4.3, and 5.1.

Phase 2 (Weeks 3-6): Data expansion, NLP improvements, and dashboards
- Scale ingestion sources, add structured extraction quality checks, and build Streamlit dashboards for observability.
- Aligns to TRD Sections 4.1 through 4.5 and Section 7.

Phase 3 (Weeks 7-10): Hardening, evaluation, and advanced features
- Improve reliability, add evaluation harnesses, and refine classification and dedup performance.
- Aligns to TRD Sections 7 and 8.

Phase 4 (Weeks 11-12): Documentation and demo
- Produce documentation, conduct stakeholder reviews, and complete a final demo.
- Aligns to BRD Section 10 and TRD Section 10.

## 9. Integration Points in the Codebase
- Azure OpenAI clients: `app/lib/openAiClients.ts`.
- Job creation flow: `app/lib/joblistings.ts` and `app/api/joblistings/add/route.ts`.
- Schema references: `prisma/schema.prisma`.
- Planning docs: `docs/planning/JOB_INGESTION_AGENT_BRD.md`, `docs/planning/JOB_INGESTION_AGENT_TRD.md`.

## 10. Key Design Decisions and Open Questions
These are required per BRD Section 9 and must be resolved before final implementation details:
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

## 11. Risks and Constraints
- LLM variability requires schema, retries, and confidence scoring.
- Model availability requires fallbacks if ML service is unavailable.
- Source API changes require versioned adapters and monitoring.
- Schema drift requires validation and enforcement of required fields.
- Performance constraints: batch 1,000 jobs < 5 minutes; individual scoring < 2 seconds.

## 12. Evaluation and Observability
- Metrics: dedup precision and recall, extraction F1, classification accuracy, spam precision, quality correlation.
- Logging: LLM latency, extraction failures, retry counts, dedup decisions.
- Dashboards: Streamlit provides visibility into model performance and operational queues.
- Feedback loop: use evaluation results to adjust prompts, thresholds, and models.

## 13. Roadmap and Next Steps
1. Resolve BRD design decisions.
2. Build ingestion adapters and raw storage with idempotency.
3. Implement dedup (exact + fuzzy) and LLM extraction.
4. Add scoring models and evaluation harness.
5. Map canonical output to `job_postings` and related tables.
6. Instrument observability and stand up Streamlit dashboards.
7. Iterate based on evaluation metrics and stakeholder review.

## 14. Appendix: Suggested Streamlit Views
- Ingestion overview by source and run.
- Extraction confidence distributions and failures.
- Classification distributions and score histograms.
- Dedup clusters and merge counts.
- Review queue for low-confidence or spam-flagged jobs.
- Evaluation summary (precision, recall, and F1 trends).

