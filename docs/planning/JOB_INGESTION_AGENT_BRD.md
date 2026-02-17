# Job Ingestion & Intelligence Agent — Business Requirements Document (BRD)

## 1. Document Control

| Field | Value |
|-------|--------|
| **Document title** | Job Ingestion & Intelligence Agent — BRD |
| **Version** | 0.1 (Draft) |
| **Owner** | TBD |
| **Status** | Draft — pending approval |
| **Last updated** | 2025-02-11 |
| **Approval** | Pending product/tech lead sign-off |

---

## 2. Executive Summary

**Project name:** Job Ingestion & Intelligence Agent

**Objective:** Build a production-grade agent system that:

- Ingests job postings from external sources (JSearch Web API and web scraping; no paid job-feed services)
- Extracts structured data using LLMs
- Classifies and scores jobs using ML models
- Deduplicates and normalizes postings
- Outputs a validated, high-signal, structured job object
- Surfaces AI-relevant, high-quality jobs
- Operates as an agent-first pipeline with deterministic agents first and LLM agents only where required

**Value to Tech Talent Showcase (watechcoalition):** The system will feed the **same** job-seeker-facing surface (existing job listing APIs and UI). Ingested jobs may live in the same `job_postings` table or a linked store, per resolved design. Benefits include: more job inventory, improved AI relevance signal, reduced noise and spam, and a single source for employer-created and externally ingested jobs.

**System attributes:** Agent-first and robust to noisy or incomplete upstream data; deterministic where possible; observable and measurable; extensible for future intelligence features.

---

## 3. Business Context

**Problem statement:** Current job data from external sources is:

- Inconsistent in structure
- Sparse or missing key fields
- Duplicate across feeds
- Low signal regarding AI relevance
- Unreliable for downstream analytics

**Current state in watechcoalition:** Job postings are **employer-created only**. There is no external job ingestion (no JSearch or scraping pipeline yet). Jobs are created via authenticated employer/admin flows and require existing company and location records.

**Driver:** A hybrid LLM + ML pipeline is required to improve reliability, classification, and trustworthiness of job data when external sources are introduced.

---

## 4. Scope

### In scope (initial phase)

- Multi-source ingestion (JSearch Web API and scraping)
- Deduplication (exact and near-duplicate detection)
- LLM field extraction (title, company, location, salary, skills, seniority, industry, AI relevance indicators)
- ML classification and scoring (job role, seniority, quality, spam)
- Spam detection
- Confidence scoring (field-level and overall)
- Post-processing validation and normalization
- Structured job object output
- AI relevance scoring
- Integration with watechcoalition job listing APIs and UI (same surface as employer-created jobs)
- Operational analysis and alerting for internal review (agent-driven summaries, review queues, thresholds)

### Out of scope (initial phase)

- Real-time search UI changes
- Employer dashboard changes
- User personalization
- Job application tracking
- Resume matching (future integration)
- Compensation prediction modeling

*Traceability: Foundation doc Section 3.*

---

## 5. Stakeholders

| Role | Responsibility |
|------|----------------|
| **Product** | Scope, priorities, success criteria, design decision ownership |
| **Engineering** | Architecture, implementation, observability |
| **Curriculum (Applied Agentic AI)** | Alignment with sprint-based structure and Phase B agent builds |
| **Data/ML** | Evaluation dataset, model training, AI relevance ground truth (if separate from product) |

---

## 6. Goals and Success Criteria

| Component | Metric | Target | Foundation doc ref |
|-----------|--------|--------|--------------------|
| Deduplication | Precision / Recall | ≥ 90% duplicate detection accuracy on test dataset | FR 5.2, Section 8 |
| LLM extraction | Field-level F1 | Measured and tracked | Section 8 |
| Classification | Accuracy / F1 | Per classifier (role, seniority, quality) | Section 8 |
| Spam detection | Precision | High precision to avoid false positives | Section 8 |
| Quality scoring | Correlation with human rating | Measured | Section 8 |
| Performance | Batch ingestion | 1,000 jobs &lt; 5 minutes | NFR Section 7 |
| Performance | Individual scoring | &lt; 2 seconds per job (async acceptable) | NFR Section 7 |

---

## 7. Constraints and Assumptions

- **LLM provider is configurable**. Azure OpenAI is currently integrated, but provider selection is not locked and must be runtime-configurable.
- **MSSQL** is the primary database; no change to primary store for initial phase unless a design decision approves a vector DB for semantic dedup.
- **First phase is batch-first** for ingestion and scoring unless BRD design decisions specify real-time-first.
- **Existing taxonomy** (technology_areas, industry_sectors, pathways, skills) may be used for mapping; SOC or other taxonomy is TBD per design decisions below.
- **Job creation today** requires `company_id` and `location_id`; ingested jobs supply company and location as text and will require resolution strategy (match, placeholder, or staging).

---

## 8. Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM output variability | Structured output schema, per-field confidence, retries and graceful failure |
| ML model unavailable | Fallback behavior (e.g. skip scoring, flag for review) |
| Source changes (JSearch, scraping targets) | Versioned adapters, monitoring, idempotent ingestion |
| Schema drift (upstream vs canonical) | Validation layer, required-field enforcement, low-confidence flagging |
| Duplicate detection accuracy below target | Evaluation dataset, tuning of hash/semantic/fuzzy strategy |

---

## 9. Design Decisions to Resolve (Before/During TRD)

The following decisions must be resolved (with owner and option selected) before or during the Technical Requirements Document phase. The TRD will reference these and state "per BRD decision X" or "TBD in BRD."

| # | Decision | Options | Owner |
|---|-----------|---------|--------|
| 1 | **Taxonomy** for job role, seniority, industry | SOC (Standard Occupational Classification) vs internal watechcoalition (`technology_areas`, `pathways`, `industry_sectors`) | Product / Data |
| 2 | **ML hosting** | In-repo (e.g. Node/Python in app) vs separate service vs Azure ML | Engineering |
| 3 | **Batch vs real-time** | Batch-first vs real-time-first for ingestion and scoring | Product |
| 4 | **Source of truth** for ingested jobs | Same `job_postings` table (with source/origin columns) vs separate "external jobs" store with optional promotion to `job_postings` | Product / Engineering |
| 5 | **Storage** | MSSQL only vs MSSQL + vector DB for semantic dedup/similarity | Engineering |
| 6 | **Evaluation dataset** | None today — who provides; format and size | Data / Product |
| 7 | **AI relevance ground truth** | Who defines "AI relevance"; how to label for training and evaluation | Product / Data |
| 8 | **Spam threshold** | Score threshold and policy: reject vs flag for review | Product |
| 9 | **Deduplication** | Source-agnostic vs source-prioritized (e.g. JSearch over scraped when duplicate) | Product |
| 10 | **Versioning** | Prompts (e.g. in repo + env) and ML models (tags, A/B) | Engineering |
| 11 | **LLM provider policy** | Provider-agnostic adapter vs fixed provider; model selection and fallback rules | Engineering |
| 12 | **Scraping implementation (Ingestion Agent)** | Firecrawl (managed, /agent) vs Crawl4AI (local, adaptive) vs ScrapeGraphAI (NL definitions) vs Browser-use (browser control) vs Spider (Rust, mass URLs). Choice determines how the Ingestion Agent acquires scraped content; agent interface (inputs/outputs) remains fixed. See Appendix A: Scraping Tool Options. | Engineering / Product |

---

## 10. Approval / Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product lead | | | |
| Tech lead | | | |

---

## Appendix A: Scraping Tool Options (Ingestion Agent)

The Ingestion Agent uses one or more of the following as **tools** to fetch and normalize scraped job content. The agent contract (raw job shape, idempotency, source identifier) is independent of tool choice.

| Tool | Core Strength | Primary Use Case |
|------|---------------|------------------|
| **Firecrawl** | Managed infrastructure, /agent endpoint | Rapid, reliable extraction for AI assistants |
| **Crawl4AI** | Local-first, adaptive pattern learning | Privacy-focused or heavy-volume local scraping |
| **ScrapeGraphAI** | Natural language definitions | No-code scraping logic for changing layouts |
| **Browser-use** | Direct browser control | Sites requiring complex interactions or logins |
| **Spider** | Extreme speed (Rust-based) | Mass aggregation across thousands of URLs |

---

*This BRD is the business basis for the Technical Requirements Document (TRD): [JOB_INGESTION_AGENT_TRD.md](JOB_INGESTION_AGENT_TRD.md).*
