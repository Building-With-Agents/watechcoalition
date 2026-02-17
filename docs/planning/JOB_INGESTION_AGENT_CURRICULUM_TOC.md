# Job Ingestion & Intelligence Agent — Agent-First Curriculum and 12-Week Plan

This curriculum aligns to the agent-first internship plan while conforming to BRD and TRD requirements for the watechcoalition environment. It is final and replaces prior stack assumptions.

## 1. Source of Truth and Alignment
Primary source of truth for schedule and weekly milestones:
- `c:\Users\garyl\Desktop\BWA - Copilot Studio\internship project plan agent first.docx`

Authoritative requirements and constraints:
- `docs/planning/JOB_INGESTION_AGENT_BRD.md`
- `docs/planning/JOB_INGESTION_AGENT_TRD.md`

Alignment rules
- The internship plan sets weekly deliverables and build order.
- The BRD sets business scope, success criteria, and design decisions.
- The TRD sets architecture, integration points, and NFRs.
- Conflicts are resolved in favor of BRD and TRD.

## 2. Agent-First Principles
- Build deterministic agents before any LLM agents.
- Use LLMs only where deterministic logic is insufficient.
- Keep LLM providers configurable and swappable.
- Enforce explicit inputs, outputs, and evaluation for each agent.

## 3. Stack Adaptation for watechcoalition
- Agent runtime: Python services for agent workflows and Streamlit dashboards.
- Data access: MSSQL via SQLAlchemy + `pyodbc` for agents; Prisma remains for the app.
- LLM integration: provider-agnostic adapter with runtime selection.
- Scheduling: APScheduler for batch runs; queue later if needed.
- Dashboards: Streamlit as separate read-only analytics surface.

## 3.1 Scraping options (Ingestion Agent)

These tools are candidate implementations for the Ingestion Agent's scraping capability. Week 1 delivers a thin slice using one chosen option per BRD/TRD.

| Tool | Core Strength | Primary Use Case |
|------|---------------|------------------|
| **Firecrawl** | Managed infrastructure, /agent endpoint | Rapid, reliable extraction for AI assistants |
| **Crawl4AI** | Local-first, adaptive pattern learning | Privacy-focused or heavy-volume local scraping |
| **ScrapeGraphAI** | Natural language definitions | No-code scraping logic for changing layouts |
| **Browser-use** | Direct browser control | Sites requiring complex interactions or logins |
| **Spider** | Extreme speed (Rust-based) | Mass aggregation across thousands of URLs |

## 4. 12-Week Plan (Agent-First Build Order)

Week 1: Foundations and toolchain
Outcomes
- Environment ready, first scrape working, Streamlit prototype running.
Deliverables
- Basic scraper output and Streamlit raw text display.
- Scraping tool selection for the Ingestion Agent per BRD/TRD (options: Firecrawl, Crawl4AI, ScrapeGraphAI, Browser-use, Spider).
Alignment
- TRD Sections 4.1, 4.1.1, and 5.1.

Week 2: End-to-end thin slice
Outcomes
- Scrape -> extract -> display flow works on a small sample.
Deliverables
- Initial extraction output and basic UI filters.
Alignment
- TRD Sections 4.3 and 5.1.

Week 3: Ingestion Agent (deterministic)
Outcomes
- MSSQL schema for raw ingestion and batch tracking.
- Ingestion Agent runs on a schedule and writes data reliably.
Deliverables
- Ingestion Agent, idempotency rules, batch IDs, error logging.
Alignment
- TRD Sections 4.1 and 6.

Week 4: Extraction upgrades and evaluation
Outcomes
- Improved extraction quality and an evaluation harness.
Deliverables
- Evaluation dataset, precision and recall report, confidence scoring.
Alignment
- TRD Sections 4.3 and 8.

Week 5: Visualization layer
Outcomes
- Streamlit dashboards for core pipeline metrics.
Deliverables
- Charts for extraction confidence and classification distributions.
Alignment
- TRD Section 7.

Week 6: Alert Agent (deterministic)
Outcomes
- Alerts for spikes, quality drops, or spam thresholds.
Deliverables
- Alert Agent and operational review dashboards.
Alignment
- TRD Sections 4.5 and 7.

Week 7: Analysis Agent (LLM optional)
Outcomes
- Weekly insight summaries generated from structured data.
Deliverables
- Analysis Agent with provider-agnostic LLM adapter and audit logs.
Alignment
- TRD Sections 4.3 and 7.

Week 8: Q&A Agent (LLM optional)
Outcomes
- Natural language questions over the database with SQL verification.
Deliverables
- Q&A Agent and Streamlit chat interface with guardrails.
Alignment
- TRD Sections 7 and 9.

Week 9: Pipeline hardening and scale
Outcomes
- Dedup accuracy improved and pipeline reliability increased.
Deliverables
- Dedup thresholds, retry policies, and performance monitoring.
Alignment
- TRD Sections 4.2 and 7.

Week 10: Testing, security, performance
Outcomes
- End-to-end evaluation and load testing complete.
Deliverables
- Test suite, security review, and staging deployment.
Alignment
- BRD Section 6 and TRD Section 7.

Week 11: Documentation and handoff prep
Outcomes
- Documentation, agent diagrams, and operational guides complete.
Deliverables
- README updates, agent docs, and demo script.
Alignment
- BRD Section 10 and TRD Section 10.

Week 12: Capstone demo and retrospective
Outcomes
- Live demo, final handoff, and retrospective.
Deliverables
- Final demo, release tag, and handoff package.
Alignment
- BRD Section 10.

## 5. Agent Build Order and Dependencies
Build order
- Ingestion Agent -> Alert Agent -> Analysis Agent -> Q&A Agent.

Dependencies
- Analysis and Q&A require clean, structured, and deduplicated data.
- Alerting requires stable batch tracking and quality metrics.

## 6. Cross-Cutting Skills and Artifacts
- Evaluation datasets and harnesses.
- Observability dashboards and logs.
- Prompt and model versioning with provider-agnostic adapters.
- Security and PII-safe logging.

## 7. Capstone Outcomes
- End-to-end ingestion pipeline aligned to BRD success criteria.
- Streamlit dashboards for observability and analysis.
- Agent documentation, demo assets, and handoff materials.

