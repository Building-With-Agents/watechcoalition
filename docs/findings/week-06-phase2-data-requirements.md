# Week 6 — Phase 2 data requirements

## Upstream data gaps

- **Gap analysis / cohort vs market:** needs **candidate or cohort skill profiles** (what graduates can do) to compare against job-posting demand. The pipeline today has demand-side signals (normalized jobs, extracted skills) but no consented learner record store.
- **Candidate–role match:** needs **per-person skill assessments** (and ideally outcomes), not just aggregate posting analytics.
- **Stakeholder reports (Phase 2):** needs **document generation** (PDF/DOCX) and possibly branding templates — largely a presentation layer, but may pull from new aggregates keyed by persona.

## New ingestion sources required

- **LMS / program roster integrations** or CSV uploads with governance workflow.
- **Assessment vendors** or internal rubrics (capstone projects, certification passes) mapped to a stable skill taxonomy (ESCO / internal IDs).
- Optional **employer feedback** on placement quality (high sensitivity; optional Phase 2+).

## Low-cost schema changes (add now) vs later

| Change | Cost | Rationale |
|--------|------|-----------|
| `QueryRequest` + `QueryPersona` on API | Low | Forward-compatible; Phase 1 ignores `persona`. Implemented in `agents/common/types/query_request.py`. |
| Optional `proficiency_level` on `SkillRecord` | Low–medium | See below; additive field with default `unknown` minimizes breakage. |
| `tool_vendor` on `ToolRecord` | Low | Additive; helps Phase 2 vendor-specific analytics. |
| New tables for candidates / cohorts | High | Requires product, consent, retention policy, and access control — defer to Phase 2 program.

## Privacy / consent implications

- **Candidate profiles** are personal data: need purpose limitation (workforce development), retention limits, access roles (instructors vs employers), and opt-in for sharing beyond CFA.
- **Minimize** stored free text (resumes); prefer structured skill assertions and hashed identifiers where possible.
- **Persona-based routing** must not leak restricted fields to wrong audiences (e.g. student PII in a board brief).

## `proficiency_level` recommendation

**Proposal:** add optional `proficiency_level: Literal["beginner", "intermediate", "expert", "unknown"] = "unknown"` to `SkillRecord`.

**Extraction options:**

1. **LLM classification** per skill span — higher token cost; noisy for rare skills.
2. **Heuristics** from posting text (“senior”, “5+ years”, “expert in”) — cheap; partial coverage.
3. **Role-level inference** from seniority only — coarse; many skills stay `unknown`.

**Tradeoff:** expect a large `unknown` rate unless LLM budget is allocated. **Recommendation:** add the field now with default `unknown`; pilot heuristic + optional LLM pass on high-value skills only; measure coverage before mandating proficiency in Phase 2 queries.

## `QueryRequest` model proposal

- Implemented as Pydantic `QueryRequest` with `query`, optional `persona`, optional `intent_hint`, `max_results` (default 10).
- Phase 1 endpoints ignore `persona`; Phase 2 maps `QueryPersona` to prompts, filters, and export templates.
