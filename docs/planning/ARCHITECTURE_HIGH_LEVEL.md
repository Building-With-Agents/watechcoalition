# Job Intelligence Engine — Architecture Overview
**Audience:** Directors, stakeholders, non-technical leads
**Version:** 1.1 | **Source of truth:** `job_intelligence_engine_architecture.docx`
**Last updated:** 2026-02-18

---

## What This System Does

The Job Intelligence Engine automatically finds, cleans, and enriches job postings from across the web and delivers them — structured, deduplicated, and skill-tagged — to job seekers on the watechcoalition platform.

Today, the platform only shows jobs that employers manually create. This engine adds an automated external feed so job seekers see more opportunities without any changes to how employers post jobs.

---

## How It Works — The Big Picture

Job postings from the web flow through a series of eight specialized agents. Each agent has one job. They hand work to each other through a message system — no agent can interfere with another's work.

```
External Sources (job boards, APIs)
          ↓
   1. Ingestion Agent         — Finds and collects job postings
          ↓
   2. Normalization Agent     — Cleans and standardizes the data
          ↓
   3. Skills Extraction Agent — Identifies and tags skills using AI
          ↓
   4. Enrichment Agent        — Scores quality, flags spam, adds market context
          ↓              ↘
   5. Demand Analysis Agent   — Tracks skill demand trends and forecasts
   6. Analytics Agent         — Computes trends and answers questions
          ↓
   7. Visualization Agent     — Builds dashboards and exports

   Orchestration Agent        — Runs and monitors everything above
```

---

## The Eight Agents

| Agent | What It Does | Phase |
|-------|-------------|-------|
| **Ingestion** | Pulls job postings from external sources (job search APIs, web scraping). Removes exact duplicates before anything else sees the data. Runs on a daily automated schedule. | 1 |
| **Normalization** | Takes messy, inconsistent raw data and maps it to a clean, validated standard format. Quarantines records it can't fix rather than passing bad data downstream. | 1 |
| **Skills Extraction** | Uses AI to read job descriptions and pull out structured skill tags — separating technical skills, tools, certifications, and soft skills. Links them to the platform's existing skill taxonomy. | 1 |
| **Enrichment** | Phase 1: scores each job for quality and completeness, detects spam and fake postings, classifies seniority and job role. Phase 2: adds full company data, geographic context, and labor-market codes. | 1 + 2 |
| **Analytics** | Computes salary distributions, skill co-occurrence patterns, posting lifecycle metrics, and weekly trend reports. Answers plain-English questions about the data. | 1 |
| **Visualization** | Renders the operator dashboard in real time. Generates PDF, CSV, and JSON exports. Shows pipeline health, skill coverage, and alert status. | 1 |
| **Orchestration** | The control plane. Schedules all agents, monitors their health, retries failures automatically, and maintains a full audit log of every decision the system makes. | 1 |
| **Demand Analysis** | Tracks skill and role demand over time. Generates 30-day forecasts, identifies emerging and declining skills, and flags anomalies. | 2 |

---

## What Operators Can See

Platform administrators get a live dashboard that shows:

- **Pipeline health** — how many jobs were ingested, cleaned, and enriched in each run
- **Skill coverage** — what percentage of jobs have structured skill tags
- **Quality and spam rates** — how many postings were flagged or rejected
- **Alerts** — any failures or quality drops, organized by severity (Warning / Critical / Fatal), with the ability to acknowledge and track them
- **"Ask the Data"** — a plain-English chat interface to query job data without writing SQL
- **Weekly summaries** — auto-generated trend reports covering volume, top skills, and notable changes
- **Exports** — download any dataset as PDF, CSV, or JSON in one click

---

## Data Sources (Phase 1)

> The specific tools listed below are the reference implementation. The team evaluates alternatives as part of their Architecture Decision Records (ADRs).

| Source | Reference Tool | Method |
|--------|---------------|--------|
| JSearch Web API | httpx | Structured job search API — high-quality, structured data |
| Web scraping | Crawl4AI | Open source, runs locally, no external service dependency |

---

## Design Principles

**Reliability over speed.** Every agent degrades gracefully. If AI is unavailable, the pipeline continues with lower-fidelity outputs rather than stopping entirely.

**Transparency by default.** Every decision — deduplication, quarantine, spam flag, retry — is logged and visible in the dashboard. Operators are never left guessing why something happened.

**No interference with the existing platform.** The agent pipeline is a separate Python layer. It reads from and writes to the same database but does not touch the employer-facing job creation flow or the existing application code.

**Quality gates at every stage.** Jobs that can't be cleaned or verified are quarantined, not silently dropped or passed downstream.

**Failure is handled, not hidden.** The system has three alert tiers: warnings are logged automatically, critical failures page the on-call operator, and fatal failures stop affected parts of the pipeline and escalate to human review.

---

## Phase 1 vs Phase 2

| Capability | Phase 1 (12-week curriculum) | Phase 2 (post-curriculum) |
|------------|------------------------------|---------------------------|
| Job ingestion from external sources | ✅ | ✅ |
| Deduplication | ✅ exact match | ✅ + semantic near-duplicate |
| Skills extraction with AI | ✅ | ✅ |
| Quality and spam scoring | ✅ | ✅ |
| Job role and seniority classification | ✅ | ✅ |
| Operator dashboard with PDF/CSV/JSON export | ✅ | ✅ |
| Salary distributions and skill trends | ✅ | ✅ |
| Posting lifecycle metrics (time-to-fill, repost rates) | ✅ | ✅ |
| Full company and geographic enrichment | — | ✅ |
| Labor-market codes (SOC/NOC) | — | ✅ |
| Skill demand forecasting | — | ✅ |
| Supply/demand gap analysis | — | ✅ |
| Production-scale message bus | — | ✅ |
| Pipeline circuit-breaking and saga recovery | — | ✅ |

---

## Key Quality Targets

| What We Measure | Target |
|-----------------|--------|
| Jobs successfully ingested per run | ≥ 98% |
| Duplicate jobs reaching downstream | < 0.5% |
| Jobs that pass schema validation | ≥ 99% |
| Extracted skills linked to known taxonomy | ≥ 95% |
| 1,000 jobs processed end-to-end | Under 5 minutes |
| Dashboard data refreshed after a run | Within 5 minutes |
| Automated circuit breaks that are justified | ≥ 90% (Phase 2) |
