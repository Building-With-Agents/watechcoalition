# Week 4 — Cost Log (3 Cost Surfaces)

Per Decision #33 and the token-cost memo, this log tracks all three cost surfaces for the extraction pipeline.

---

## 1. Developer generation cost

**Definition:** Cursor / Copilot token usage during coding (development of agents, prompts, and pipeline).

| Source        | Notes                                      | Estimate / actual |
|---------------|--------------------------------------------|-------------------|
| _All pairs_   | Week 4–5 guardrails, prompts, eval, cost audit | _TBD — add estimate_ |

**How to fill:** Each pair reports estimated or actual Cursor/Copilot token usage for the sprint (or leave placeholder until collected).

---

## 2. Runtime inference cost

**Definition:** Extraction pipeline tokens per job posting (LLM calls during extraction runs).

### Week 5 — measured audit cohort (Phase 4 / Issue #90)

Source: [`agents/eval/cost_audit_week5.md`](cost_audit_week5.md) (`dbo.llm_audit_log` aggregates for the captured window; see audit for caveats on tasks/responsibilities callers).

| Metric | Source | Value |
|--------|--------|------:|
| Total LLM cost (audit window) | `llm_audit_log` | **$2.9147** |
| Total tokens (input+output, summed) | `llm_audit_log` | **504,874** |
| Total API calls (successful rows counted) | `llm_audit_log` | **341** |
| Skills share of cost | `skills-extraction-agent` | **~91.5%** ($2.6681) |
| Responsibilities + tasks | non–main-path `agent_name`s | **~8.5%** (see audit §5) |
| Tools / context LLM cost | Pass 1 pattern + context stub | **$0** (no LLM rows) |

**Exact `extracted_intelligence` sums and env-aware Sonnet/Haiku rollup:** run `python -m agents.eval.cost_audit_week5_report` and paste into the audit §3b / §6 (per successful EI row cost and tier tables).

| Metric | Source | Value |
|--------|--------|-------|
| Avg cost / primary skills call (~263 calls) | §3 cohort | **~$0.01014** |
| Avg cost / job if all audit $ spread over 263 skills jobs | §3 cohort | **~$0.0111** |
| Informal 30-job harness baseline (comparison only) | [`prompt_iteration_log.md`](prompt_iteration_log.md) | **~$0.0114** / job (v2-r2), **~$0.0160** / job (pass1-catalog-v3) |

### Week 4 — template (refresh from DB)

| Metric                    | Source                          | Value |
|---------------------------|----------------------------------|-------|
| Avg tokens per record     | `python -m agents.eval.cost_projection` | _Regenerate `cost_model_week4.md`_ |
| Sonnet vs Haiku split     | `cost_audit_week5_report` or projection | _Prefer week 5 report for Azure deployment names_ |
| Cost per 1k / 10k / 100k  | `agents/eval/cost_model_week4.md` | After running `cost_projection` |

**How to fill:** Run extractions, then `python -m agents.eval.cost_projection`; for Issue #90 tier accuracy use `python -m agents.eval.cost_audit_week5_report`.

---

## 3. Context window cost

**Definition:** Tokens in prompt + response per LLM call (from `llm_audit_log`).

| Metric           | Source          | Value (Week 5 cohort) |
|------------------|-----------------|------------------------|
| Input+output tokens/call (blended) | §3 ÷ 341 calls | ~**1,481** tokens/call |
| Total cost        | §3              | **$2.9147** |

**How to fill:** Query `dbo.llm_audit_log` by `agent_name` / `model` for p50/p95 if needed.

---

## Changelog

| Date       | Who / what |
|-----------|------------|
| _Week 4_  | Initial template; developer estimates TBD from all pairs. |
| 2026-03-26 | **Week 5 Phase 4:** Runtime table filled from `cost_audit_week5.md` (Issue #90); pointers to `cost_audit_week5_report` and `prompt_iteration_log.md`. |
