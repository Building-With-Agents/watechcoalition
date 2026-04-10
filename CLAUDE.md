# CLAUDE.md — watechcoalition (Legacy Frontend)

This is the legacy Next.js frontend for the watechcoalition platform.
The agent pipeline has been extracted to the `job-intelligence-engine` repo.

---

## Status

- **Frontend:** Next.js + TypeScript + Prisma (MSSQL — legacy)
- **Status:** Legacy — being replaced by wfd-os portals
- **Agent pipeline:** Moved to https://github.com/Building-With-Agents/job-intelligence-engine
- **Database:** Next.js uses MSSQL via Prisma (deprecated). Agents use PostgreSQL via SQLAlchemy (separate repo).

## Non-Negotiable Rules

1. Do not create new Prisma migrations — Prisma is being phased out
2. The Next.js API is currently broken from the SQL Server → PostgreSQL switch (expected)
3. Do not add agent-related code — it belongs in job-intelligence-engine
4. See ONBOARDING.md for setup instructions

## Key Files

- `app/` — Next.js pages and API routes
- `prisma/schema.prisma` — Legacy database schema (deprecated)
- `docs/` — Frontend documentation (agent docs moved to JIE repo)
- `agents/` — **DEPRECATED** — code moved to job-intelligence-engine repo. This directory remains for reference only.

## Related Repos

| Repo | Purpose |
|------|---------|
| **job-intelligence-engine** | JIE agent pipeline (extracted from this repo's agents/ directory) |
| **wfd-os** | Phase 2 platform: student portal, WFD OS agents |
| **curriculum-planning** | Instructor curriculum planning |
