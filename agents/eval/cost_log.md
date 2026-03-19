# Week 4 — Cost Log (3 Cost Surfaces)

Per Decision #33 and the token-cost memo, this log tracks all three cost surfaces for the extraction pipeline.

---

## 1. Developer generation cost

**Definition:** Cursor / Copilot token usage during coding (development of agents, prompts, and pipeline).

| Source        | Notes                                      | Estimate / actual |
|---------------|--------------------------------------------|-------------------|
| Juan + Enrique | Week 4 guardrails, cost tracking, validation | _TBD — add estimate_ |
| Bryan + Emilio | _Pair C — prompt iteration_                 | _TBD_             |
| Angel + Fabian | _Pair — extraction dimensions_             | _TBD_             |
| _Other pairs_ | _Coordinate with all pairs_                | _TBD_             |

**How to fill:** Each pair reports estimated or actual Cursor/Copilot token usage for the sprint (or leave placeholder until collected).

---

## 2. Runtime inference cost

**Definition:** Extraction pipeline tokens per job posting (LLM calls during extraction runs).

| Metric                    | Source                          | Value |
|---------------------------|----------------------------------|-------|
| Avg tokens per record     | `cost_projection.py` / `llm_audit_log` | _Run cost projection script_ |
| Sonnet vs Haiku split     | Same                             | _TBD_ |
| Cost per 1k / 10k / 100k  | `agents/eval/cost_model_week4.md` | See cost report |

**How to fill:** Run extraction on 5–10 postings, then `python -m agents.eval.cost_projection`; paste summary from `cost_model_week4.md` or update this table.

---

## 3. Context window cost

**Definition:** Tokens in prompt + response per LLM call (from `llm_audit_log`).

| Metric           | Source          | Value |
|------------------|-----------------|-------|
| Input tokens/call | `llm_audit_log` | _Query table_ |
| Output tokens/call| `llm_audit_log` | _Query table_ |
| Cost per call    | `cost_usd` in `llm_audit_log` | _Query table_ |

**How to fill:** After runs, query `dbo.llm_audit_log` for `token_count`, `cost_usd`, and by `model`/`agent_name`; aggregate and paste here.

---

## Changelog

| Date       | Who / what |
|-----------|------------|
| _Week 4_  | Initial template; developer estimates TBD from all pairs. |
