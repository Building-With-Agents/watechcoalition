# Query Agent — Design Context for Week 6

> Week 6 — Background Reading | All Developers (especially Juan + Enrique)

---

## Why This Matters

The CFA director requested standalone Query Agent capabilities for workforce intelligence Q&A. The 8-agent architecture defined in `ARCHITECTURE_DEEP.md` — which you've been building since Week 1 — already handles Q&A as a sub-capability of the Analytics and Visualization agents (Week 8). Adding a ninth standalone agent would break the architectural contracts, event flow, and scope you've invested five weeks building.

The solution: a **phased approach** that meets the director's requirements while preserving the 8-agent architecture. Phase 1 enhances the existing Q&A within scope. Phase 2 extends it post-capstone with new capabilities that require upstream data the pipeline doesn't have yet. Juan + Enrique have explicit Phase 2 research tasks, but the context benefits everyone.

---

## The Phased Approach

The director's request conflicted with the existing 8-agent architecture. A standalone Query Agent as a separate agent would have required restructuring the event pipeline, redefining agent boundaries, and invalidating weeks of work. Instead, the phased approach integrates the requested capabilities into the architecture you've already built.

**Phase 1 (Weeks 1–12, within existing curriculum):**
- Enhance Week 8 Q&A with Comparative Analysis and Trend Narrative output modes
- Adopt 60 example queries as formal evaluation test cases
- Add a `persona` field to the query API schema for forward-compatibility

**Phase 2 (post-capstone, scoped separately):**
- Standalone Query Agent with three new output modes: Gap Analysis, Candidate-Role Match, Stakeholder Reports
- Candidate/cohort profile data ingestion (new data source)
- Persona-based response routing (different outputs for board directors vs students)
- Formatted document generation (PDF/DOCX for board briefs)

Phase 1 delivers value within the 12-week program. Phase 2 extends the system after capstone when the architecture is stable and new data sources can be properly scoped.

---

## How Week 6 Work Feeds Phase 2

| Week 6 Deliverable | Phase 2 Connection |
|--------------------|--------------------|
| **SOC/NAICS classification** (Fatima + Nestor) | Phase 2 Gap Analysis needs SOC codes to match candidate skills against market demand |
| **EmployerProfile** (Fatima + Nestor) | Phase 2 Employer Comparison queries need employer metadata |
| **Temporal periods** (Angel) | Phase 2 Trend Narrative mode needs temporal classification for longitudinal analysis |
| **Borderplex subregions** (Angel) | Phase 2 Geographic Comparison queries need subregion tagging |
| **Fuzzy dedup** (Bryan + Emilio) | Dedup quality directly affects Phase 2 aggregate accuracy |
| **External data adapters** (Juan + Enrique) | Phase 2 replaces mock adapters with live BLS/ONET/Census APIs |
| **Visualization foundations** (Fabian) | Phase 2 dashboards extend the Streamlit skeleton built this week |
| **Phase 2 data requirements doc** (Juan + Enrique) | Defines what upstream data Phase 2 needs that doesn't exist yet |

---

## The Upstream Data Gap

Phase 2 introduces three output modes that require data the pipeline doesn't currently have:

### Gap Analysis
Requires candidate/cohort profile data — what skills do students/graduates have? Without this, you can't compare "what the market wants" (job postings) against "what we produce" (cohort skills). This is an entirely new data ingestion source with privacy/consent implications.

### Candidate-Role Match
Requires individual candidate profiles with skill assessments. Scoring a graduate against an open role needs both the job requirements (we have this) and the candidate's capabilities (we don't have this).

### Stakeholder Reports
Requires formatted document generation — PDF or DOCX board briefs, not just Streamlit pages. This is a rendering concern, not a data concern, but it's outside the current Visualization Agent's scope.

---

## What This Means for Your Work This Week

- **Build for quality, not just completion.** Every enrichment field you build this week (SOC codes, temporal periods, employer profiles) will be queried by the Phase 2 Query Agent. Accuracy matters more than speed.
- **"Unknown" is a valid value.** Phase 2 analytics can filter out unknowns. Phase 2 analytics cannot recover from incorrect values that look correct.
- **Schema stability matters.** The `EnrichedJobProfile` schema Juan + Enrique build this week will be consumed by Phase 2 query infrastructure. Design it for extension, not just for this sprint.

---

## Reference Files

- [`docs/planning/ARCHITECTURE_DEEP.md`](https://github.com/Building-With-Agents/watechcoalition/blob/development/docs/planning/ARCHITECTURE_DEEP.md) (8-agent architecture, Analytics Agent Q&A specification)
- [`lesson-framework/week-08-analytics-agent-qa.md`](https://github.com/Building-With-Agents/curriculum/blob/main/lesson-framework/week-08-analytics-agent-qa.md) (Week 8 Q&A lesson framework)
