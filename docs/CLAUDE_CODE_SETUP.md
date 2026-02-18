# AI-Assisted Development Guide — Job Intelligence Engine

> **Important:** `CLAUDE.md` is the single source of truth for project rules, stack, agent specs, and resolved design decisions. `docs/planning/ARCHITECTURE_DEEP.md` is the canonical implementation spec (per-agent details, JobRecord schema, event catalog, DB migrations, error handling). This guide is a companion walkthrough for using AI assistants effectively — not a replacement for either document.

## How AI Assistants Use CLAUDE.md

All AI models available through Cursor (and Claude Code for leads) read `CLAUDE.md` automatically for project context. This file tells the AI how the project works, what stack to use, what rules to follow, and where to find detailed specs.

The file is named `CLAUDE.md` by convention (it originated as a Claude Code context file), but **all Cursor models read it** — Sonnet, GPT, Gemini, or any other model available through your Cursor Teams plan.

---

## Step 1: Verify the Documentation Structure

Your repo should have this documentation structure:

```
your-repo/
├── CLAUDE.md                              ← AI reads this FIRST on every session
└── docs/planning/
    ├── ARCHITECTURE_DEEP.md               ← Canonical implementation spec
    ├── ARCHITECTURAL_DECISIONS.md          ← Full decision log (all 21 decisions)
    └── curriculum/                         ← Weekly deliverable files
```

**CLAUDE.md** is the most important file. It is the AI's source of truth for how the project works, what stack to use, what rules to follow, and where to find detailed specs. **ARCHITECTURE_DEEP.md** provides the deep implementation reference (per-agent specs, JobRecord schema, event catalog, DB migrations, error handling). Everything else flows from these two documents.

---

## Step 2: Review the Resolved Design Decisions

All 21 design decisions have been resolved. See the **Resolved Design Decisions** table in `CLAUDE.md` (lines 416–437) and the full decision log in `docs/planning/ARCHITECTURAL_DECISIONS.md`.

Key decisions that shape implementation:

| # | Decision | Resolution |
|---|----------|------------|
| 4 | Source of truth for ingested jobs | Staging tables → promote to `job_postings` |
| 12 | Scraping tool | Crawl4AI + httpx for JSearch |
| 13 | Multi-agent framework | LangGraph StateGraph |
| 15 | Skill taxonomy source | Internal watechcoalition primary; O\*NET fallback |
| 17 | Agent tracing | LangSmith |

If new decisions arise during development, add them to both `CLAUDE.md` (Resolved Design Decisions table) and `docs/planning/ARCHITECTURAL_DECISIONS.md`.

---

## Step 3: Using AI Assistants Week by Week

### Starting a Cursor session

Open the repo in Cursor and use the AI chat or agent mode. The AI reads `CLAUDE.md` and loads your project context automatically.

For leads using Claude Code directly:

```bash
cd your-repo
claude
```

### Week 1 example prompt

```
Create the Python environment scaffold for the agents/ directory following the 
Repository Structure section in CLAUDE.md. Then write the first scrape script 
using Crawl4AI that fetches 10 job postings and saves them to 
agents/data/staging/raw_scrape_sample.json.
```

### Week 3 example prompt

```
Implement the Ingestion Agent per the Ingestion Agent spec in 
docs/planning/ARCHITECTURE_DEEP.md. It should use SQLAlchemy to write to MSSQL, 
emit IngestBatch events using the typed event envelope in agents/common/events/, 
and deduplicate using the hash-based idempotency key (source + external_id). 
Write unit tests in agents/ingestion/tests/.
```

### General prompting tips

**Be specific about the spec section:**
> "Implement the Normalization Agent per the Normalization Agent spec in docs/planning/ARCHITECTURE_DEEP.md" is better than "build the normalization agent"

**Reference the evaluation targets:**
> "The success rate must be ≥ 98% per the Evaluation Targets table in CLAUDE.md — add a test that verifies this"

**Tell it what NOT to do:**
> "Do not modify prisma/schema.prisma. Create SQLAlchemy models in agents/normalization/models.py instead"

**Request tests alongside code:**
> "Write the agent and its pytest tests in the same task"

**Use iteration:**
> After the AI writes code, ask: "Now run the tests and fix any failures"

---

## Step 4: Recommended Workflow Per Week

```
1. Open the repo in Cursor (or start a Claude Code session for leads)
2. Tell the AI which week you're on and which deliverables to build
3. The AI reads CLAUDE.md + relevant section of docs/planning/ARCHITECTURE_DEEP.md
4. Review the code it writes before letting it run
5. Ask it to run tests: "Run pytest agents/tests/ and fix failures"
6. Commit working code before moving to next deliverable
7. Update CLAUDE.md if any architectural decisions changed
```

---

## Step 5: Keep CLAUDE.md Updated

As you build the system, keep `CLAUDE.md` current. AI assistants re-read it on every new session. Key things to maintain:

- Keep the **Resolved Design Decisions** table current as new decisions are made
- Any conventions you've established (e.g., how you name events, logging format)
- Tables that now exist in the DB
- Any rules you want the AI to always follow
- Update the **Full Specification Reference** section if new spec documents are added

Also keep `docs/planning/ARCHITECTURAL_DECISIONS.md` in sync with the CLAUDE.md table for the full decision rationale.

---

## Prompts for Common Tasks

### Scaffold the full agents/ directory structure
```
Create the full agents/ directory scaffold from the Repository Structure section in CLAUDE.md. 
Create __init__.py files and placeholder agent.py files with a health_check() method stub in each agent directory.
```

### Add a new data source to the Ingestion Agent
```
Add a new source adapter for [SOURCE_NAME] to agents/ingestion/sources/. 
It should implement the same interface as the existing adapters and emit IngestBatch events with the correct provenance metadata.
```

### Debug a failing evaluation metric
```
The taxonomy coverage metric is at 87%, below the 95% target. 
Review agents/skills_extraction/agent.py and the prompt in agents/skills_extraction/models/, 
identify why skills aren't being mapped, and propose a fix.
```

### Add a new Streamlit dashboard page
```
Add a "Normalization Quality" page to agents/dashboard/ following the pattern 
of the existing pages. It should show quarantine count by error type, 
field mapping accuracy, and salary normalization coverage. 
Query from MSSQL via SQLAlchemy read-only connection.
```

---

## Troubleshooting AI Assistants

**The AI is modifying the wrong files**
→ Check CLAUDE.md — add an explicit "Do NOT modify X" rule at the top. All Cursor models read this file for project context.

**The AI ignores the spec and makes up its own structure**
→ Be more explicit: "Follow the Ingestion Agent spec in docs/planning/ARCHITECTURE_DEEP.md exactly. Here is the relevant section: [paste it]"

**The AI creates a new agent for every helper function**
→ Add to CLAUDE.md: "Helper logic (dedup, field mapping, validation) stays inside the owning agent. Do not create new agent classes for these."

**The AI uses Prisma from Python**
→ Remind it: "Agents use SQLAlchemy only. Prisma is Next.js only. Never import or reference Prisma from Python."
