# Job Ingestion & Intelligence Agent — Curriculum and 12-Week Plan

This curriculum aligns to the internship project plan while conforming to the BRD and TRD requirements for the watechcoalition environment.

## 1. Source of Truth and Alignment
Primary source of truth for schedule and weekly milestones:
- `c:\Users\garyl\Desktop\BWA - Copilot Studio\internship project plan.docx`

Authoritative requirements and constraints:
- `docs/planning/JOB_INGESTION_AGENT_BRD.md`
- `docs/planning/JOB_INGESTION_AGENT_TRD.md`

Alignment rules
- The internship plan sets weekly goals and deliverables.
- The BRD sets business scope, success criteria, and design decisions.
- The TRD sets architecture, integration points, and NFRs.
- When conflicts occur, BRD and TRD constraints supersede implementation details in the internship plan.

## 2. Audience and Goals
This content is for engineers, data and ML practitioners, and curriculum designers who need a structured path from requirements to a working ingestion pipeline with evaluation and observability.

## 3. Prerequisites
- Familiarity with Node.js/TypeScript and REST APIs.
- Working knowledge of SQL and relational schemas.
- Basic understanding of ML classification and evaluation metrics.
- Basic knowledge of LLM prompting and structured output.

## 4. Program Structure
- Four pods: Backend, NLP, Frontend and Visualization, Data and QA.
- Weekly cadence: kickoff, daily standups, and end-of-week demo and retro.
- Rotation is encouraged between Weeks 4 and 6 to build cross-functional skills.

## 5. Stack Adaptation for watechcoalition
- Ingestion and persistence: Node/TypeScript with Prisma and MSSQL.
- LLM extraction: Azure OpenAI in Node with structured output.
- ML classification: Python service or ONNX inference in Node.
- Dashboards: Streamlit as a separate Python app with read-only data access.

## 6. 12-Week Plan (Aligned to BRD and TRD)

Week 1: Foundations and thin vertical slice, part 1
- Outcomes: dev environment ready, first job posting ingested, Streamlit prototype running.
- Deliverables: working scraper or source adapter, minimal Streamlit page showing raw text.
- BRD and TRD alignment: TRD Sections 4.1 and 5.1.

Week 2: Thin vertical slice, part 2
- Outcomes: end-to-end flow from ingestion to extraction to display.
- Deliverables: structured extraction output, basic filters, initial unit tests.
- BRD and TRD alignment: TRD Sections 4.3 and 5.1.

Week 3: Data collection and storage
- Outcomes: raw storage schema defined and populated, scheduled ingestion runs.
- Deliverables: ingestion run metadata, idempotency strategy, data quality report.
- BRD and TRD alignment: TRD Sections 4.1 and 6.

Week 4: NLP pipeline improvements
- Outcomes: improved extraction or classification accuracy with evaluation harness.
- Deliverables: evaluation dataset, precision and recall report, confidence scoring.
- BRD and TRD alignment: TRD Sections 4.3, 4.4, and 8.

Week 5: Visualization layer
- Outcomes: Streamlit dashboards for top metrics and distributions.
- Deliverables: charts for extraction confidence and classification distributions.
- BRD and TRD alignment: TRD Section 7.

Week 6: Regional and source analysis
- Outcomes: source mix and regional trends visible in dashboards.
- Deliverables: comparison views, data quality insights, stakeholder demo.
- BRD and TRD alignment: BRD Sections 3 and 6.

Week 7: Pipeline hardening
- Outcomes: robust error handling, batching, and retries.
- Deliverables: queue or workflow implementation, run logs, alerts.
- BRD and TRD alignment: TRD Sections 4.1 and 7.

Week 8: Dedup and semantic similarity
- Outcomes: exact and fuzzy dedup live, semantic similarity evaluated.
- Deliverables: dedup thresholds, duplicate cluster review dashboard.
- BRD and TRD alignment: TRD Section 4.2.

Week 9: UX and accessibility
- Outcomes: dashboards polished and usable for review workflows.
- Deliverables: accessibility checklist, exportable reports.
- BRD and TRD alignment: TRD Section 7.

Week 10: Integration, testing, performance
- Outcomes: end-to-end pipeline validated against BRD metrics.
- Deliverables: evaluation results, performance report, staging deployment.
- BRD and TRD alignment: BRD Section 6 and TRD Section 7.

Week 11: Documentation and handoff prep
- Outcomes: documentation complete, demo script prepared.
- Deliverables: architecture diagram, operating guide, model and prompt versioning notes.
- BRD and TRD alignment: BRD Section 10 and TRD Section 10.

Week 12: Capstone demo and retrospective
- Outcomes: live demo delivered and handoff completed.
- Deliverables: final demo, retrospective, handoff package.
- BRD and TRD alignment: BRD Section 10.

## 7. Cross-Cutting Skills and Artifacts
- Evaluation: datasets, harnesses, and metrics reporting.
- Observability: logs, metrics, traces, and dashboards.
- Governance: versioning for prompts and ML models.
- Quality: test coverage, data validation, and schema checks.

## 8. Capstone Outcomes
- End-to-end ingestion pipeline aligned to BRD success criteria.
- Streamlit dashboard for observability and evaluation.
- Documentation, demo assets, and handoff materials.

