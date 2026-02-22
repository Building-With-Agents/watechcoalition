# Project Overview

The **Washington Tech Workforce Coalition** (WaTech Coalition) platform connects employers and job seekers in the tech industry. It provides job listings, employer workflows, jobseeker profiles, and career-prep tools. A planned extension -- the **Job Intelligence Engine** -- will add an eight-agent Python pipeline that ingests, normalizes, enriches, and analyzes external job postings.

This document describes the **current state** (the production Next.js application) and the **future state** (the agent pipeline). For environment setup see [ONBOARDING.md](../ONBOARDING.md); for the full agent specification see [CLAUDE.md](../CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](planning/ARCHITECTURE_DEEP.md).

---

## Current State

### Tech Stack

| Layer     | Technology                     | Notes                         |
|-----------|--------------------------------|-------------------------------|
| Framework | Next.js 15 (App Router)        | TypeScript 5, React 19        |
| ORM       | Prisma 6                       | Code-first schema             |
| Database  | MSSQL (SQL Server)             | Local via Docker              |
| Styling   | TailwindCSS v4 + Material-UI 7 |                               |
| Auth      | Auth.js (NextAuth v5 beta)     | GitHub, Google, MS Entra ID   |
| State     | Redux Toolkit                  |                               |
| Storage   | Azure Blob Storage             | Avatars, uploads              |
| Email     | Resend + React Email           |                               |
| Testing   | Vitest + React Testing Library |                               |

### Architecture

```
                        ┌─────────────────────────────────────────────┐
                        │            Auth Providers                   │
                        │   (GitHub, Google, MS Entra ID)             │
                        └────────────────────┬────────────────────────┘
                                             │
┌──────────┐   HTTPS    ┌────────────────────▼────────────────────┐
│          │ ────────>  │          Next.js App Router             │
│ Browser  │            │                                         │
│          │ <────────  │  middleware.ts ── Auth.js (role-based)  │
└──────────┘            │                                         │
                        │  ┌─────────────┐    ┌────────────────┐  │
                        │  │ React Pages │    │  API Routes    │  │
                        │  │ (SSR + CSC) │    │ (app/api/...)  │  │
                        │  └─────────────┘    └───────┬────────┘  │
                        └─────────────────────────────┼───────────┘
                                                      │
                              ┌───────────────────────┤
                              │                       │
                     ┌────────▼─────────┐    ┌────────▼─────────┐
                     │   Prisma ORM     │    │  Azure Blob      │
                     │                  │    │  Storage         │
                     └────────┬─────────┘    └──────────────────┘
                              │
                     ┌────────▼─────────┐
                     │     MSSQL        │
                     │  (Docker local)  │
                     └──────────────────┘
```

### Application Workflows

**Jobseeker** -- Create a profile, search and filter job listings, bookmark positions, submit applications, and complete career-prep assessments.

**Employer** -- Register a company, post job listings, review applicants, and manage company details.

**Admin** -- Manage users and roles, view platform analytics dashboards, generate skill embeddings, and perform data-quality checks.

---

## Future State -- Job Intelligence Engine

The Job Intelligence Engine is an eight-agent Python pipeline that will run alongside the Next.js app. It ingests external job postings (JSearch API, web scraping via Crawl4AI), normalizes them, extracts skills, enriches records, computes analytics, and renders dashboards -- all orchestrated by a central Orchestration Agent. The pipeline is scaffolded in `agents/` but **not yet implemented**; it will be built over a 12-week curriculum (see the Build Order table in [CLAUDE.md](../CLAUDE.md)).

### Agent Pipeline Tech Stack

| Layer                 | Technology                     |
|-----------------------|--------------------------------|
| Agent runtime         | Python 3.11+                   |
| Multi-agent framework | LangGraph (StateGraph)         |
| LLM                   | LangChain + Azure OpenAI       |
| Tracing               | LangSmith                      |
| DB access             | SQLAlchemy + pyodbc --> MSSQL  |
| Scraping              | Crawl4AI + httpx               |
| Dashboards            | Streamlit (read-only)          |
| Scheduling            | APScheduler                    |

### Agent Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                     External Sources                             │
│            (JSearch API via httpx / Crawl4AI scraping)           │
└───────────────────────────┬──────────────────────────────────────┘
                            │  daily cron
                            ▼
                 ┌─────────────────────┐
                 │  Ingestion Agent    │──> IngestBatch
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Normalization Agent │──> NormalizationComplete
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Skills Extraction   │──> SkillsExtracted
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │  Enrichment Agent   │──> RecordEnriched
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │  Analytics Agent    │──> AnalyticsRefreshed
                 └──────────┬──────────┘
                            ▼
                 ┌─────────────────────┐
                 │ Visualization Agent │──> RenderComplete
                 └─────────────────────┘

     ┌────────────────────────────────────────────────┐
     │           Orchestration Agent                  │
     │  (schedules, monitors, retries all agents;     │
     │   sole consumer of *Failed / *Alert events)    │
     └────────────────────────────────────────────────┘
```

---

## Combined Architecture

The Next.js app and the agent pipeline are separate runtimes that share one MSSQL database. The agents write through SQLAlchemy; the app reads and writes through Prisma. Neither runtime calls the other directly.

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│        Next.js App              │     │     Agent Pipeline (Python)     │
│                                 │     │                                 │
│  App Router + API Routes        │     │  Ingestion ─> Normalization     │
│  Auth.js (role-based)           │     │  ─> Skills ─> Enrichment        │
│  React pages (SSR + CSC)        │     │  ─> Analytics ─> Visualization  │
│                                 │     │                                 │
│  Prisma ORM (read/write)        │     │  SQLAlchemy + pyodbc (r/w)      │
│  Azure Blob Storage             │     │  Streamlit dashboards (read)    │
└───────────────┬─────────────────┘     └───────────────┬─────────────────┘
                │                                       │
                └──────────────┐   ┌────────────────────┘
                               │   │
                          ┌────▼───▼────┐
                          │    MSSQL    │
                          │  (shared)   │
                          └─────────────┘
```

---

## Further Reading

- [CLAUDE.md](../CLAUDE.md) -- Agent architecture, rules, build order, evaluation targets
- [docs/planning/ARCHITECTURE_DEEP.md](planning/ARCHITECTURE_DEEP.md) -- Per-agent implementation spec, JobRecord schema, event catalog
- [docs/planning/ARCHITECTURAL_DECISIONS.md](planning/ARCHITECTURAL_DECISIONS.md) -- Full design decision log
- [ONBOARDING.md](../ONBOARDING.md) -- Environment setup (Node, Docker, database seed)
