# Cost Audit — Week 5 Phase 4

**Status:** Updated with **actual `llm_audit_log` aggregates** (cohort as measured; not stored in git history). Totals below are **audit-log sums**, not a full reconciliation to `extracted_intelligence` unless you run the SQL in §3 separately.

---

## 1. Scope (what is actually measured)

| In scope | Notes |
|----------|--------|
| Per-job **LLM** token and USD totals persisted by the Skills Extraction Agent | Written to `dbo.extracted_intelligence` as `extraction_tokens_used` and `extraction_cost_usd` when records are saved (`agents/skills_extraction/agent.py`). |
| Per-call LLM audit rows | Written to `dbo.llm_audit_log` via `log_extraction_event` (`agents/common/llm_client.py` and related callers). **Multiple `agent_name` values can appear** (see §3). |
| **Measured** split of tokens/USD by `agent_name` | From DB aggregate (this document §3–5). |

| Out of scope / caveat | Notes |
|----------------------|--------|
| Equating every audit row to one `extracted_intelligence` row | No FK from `llm_audit_log` to `normalized_job_id`. |
| **Main pipeline vs other callers** | The default `agents/skills_extraction/agent.py` path runs Pass 1 tools + Pass 2 **skills** and persists **skills** metadata; **`extract_tasks` / `extract_responsibilities` in-repo are stubs** (`return []`). Rows for **`skills-extraction-tasks`** and **`skills-extraction-responsibilities`** in `llm_audit_log` indicate **other code paths** (scripts, experiments, or future wiring)—**not** the main single-agent persistence design. Interpret §5 accordingly. |

---

## 2. Data sources

### `dbo.extracted_intelligence`

| Column | Use |
|--------|-----|
| `extraction_tokens_used` | Integer; total tokens attributed to the extraction run for that row (from Pass 2 skills metadata when LLM ran). |
| `extraction_cost_usd` | Float; USD estimate from the same metadata path. |
| `extraction_metadata` (JSONB) | May include `model_tier`, `pass1_tool_count`, `pass2_llm_dimensions`, `tokens_used`, `cost_usd` (see `ExtractionMetadata` in `agents/common/types/extraction_types.py`). |
| `extraction_version`, `extracted_at` | Filter to a cohort. |

**Schema:** `agents/common/data_store/models.py` (`ExtractedIntelligence`).

### `dbo.llm_audit_log`

| Column | Use |
|--------|-----|
| `agent_name` | Observed in measurement: **`skills-extraction-agent`**, **`skills-extraction-responsibilities`**, **`skills-extraction-tasks`** (see §3). |
| `model`, `input_tokens`, `output_tokens`, `token_count`, `cost_usd`, `success`, `created_at` | Tier analysis and reconciliation by time window. |

**Limitation:** There is **no** `normalized_job_id` on `llm_audit_log` — you cannot join one audit row to one `extracted_intelligence` row by FK; reconciliation is by **time window** and optional run boundaries only.

---

## 3. Actual extraction cost totals (llm_audit_log)

**Source:** Aggregate query over `dbo.llm_audit_log` (counts and sums as measured).

| Metric | Value |
|--------|--------|
| Total rows | **341** |
| Total tokens (input+output, summed from cohort) | **504,874** |
| Total cost USD | **$2.9147** |

**By `agent_name`:**

| agent_name | Calls | Tokens | Cost USD |
|------------|------:|-------:|---------:|
| `skills-extraction-agent` | 263 | 454,475 | $2.6681 |
| `skills-extraction-responsibilities` | 39 | 23,550 | $0.2241 |
| `skills-extraction-tasks` | 39 | 26,849 | $0.0225 |
| **Total** | **341** | **504,874** | **$2.9147** |

**`extracted_intelligence`:** Not summed in this pass—run the query below if you need DB row totals to compare with audit sums:

```sql
SELECT
    COUNT(*) AS record_count,
    SUM(extraction_tokens_used) AS total_tokens,
    SUM(extraction_cost_usd) AS total_cost_usd
FROM dbo.extracted_intelligence
WHERE extraction_failed = FALSE;
```

**Approximate job count:** **~263** jobs if the main skills path uses **one LLM call per job** (`263` calls for `skills-extraction-agent`). The **39** calls each for tasks and responsibilities do not line up 1:1 with 263—treat those as a **separate batch or parallel experiment**, not as 263 additional full-job passes.

---

## 4. Cost per record (approximate)

Assumptions: **one audit row ≈ one LLM call**; **263** calls ≈ **263** primary skills extractions.

| Metric | Formula | Approximate value |
|--------|---------|-------------------|
| Avg cost / skills call (main agent) | $2.6681 ÷ 263 | **~$0.01014** |
| Avg tokens / skills call | 454,475 ÷ 263 | **~1,728** |
| Avg cost / job if **all** audit cost is attributed to the same **263** jobs | $2.9147 ÷ 263 | **~$0.0111** (includes tasks + responsibilities overhead from the same window) |

**Per audit row (341 rows):** ~$0.00855 USD/row and ~1,481 tokens/row—**not** equivalent to “per job,” since call patterns differ by `agent_name`.

---

## 5. Breakdown by dimension (measured LLM cost shares)

**Shares use total measured LLM cost $2.9147** (100% = all audit-log USD in §3).

| Dimension / caller (`agent_name`) | Share of cost | Share of tokens | Notes |
|-----------------------------------|---------------|-----------------|--------|
| **Skills** (`skills-extraction-agent`) | **91.53%** ($2.6681) | **90.05%** (454,475) | Dominant; aligns with main Pass 2 skills path. |
| **Responsibilities** (`skills-extraction-responsibilities`) | **7.69%** ($0.2241) | **4.66%** (23,550) | Appears in audit log; **not** wired through default `agent.py` stub extractor—treat as **separate / experimental** unless your deployment documents otherwise. |
| **Tasks** (`skills-extraction-tasks`) | **0.78%** ($0.0225) | **5.32%** (26,849) | Same caveat as responsibilities. |
| **Tools** (Pass 1 pattern) | **0%** | **0%** | No `llm_audit_log` rows from tool pattern matching (`extract_tools`). |
| **Context** | **0%** | **0%** | Stub / no LLM in `extract_context` (see §7). |

**Non-cost volume:** Tool and context rows are not LLM-backed in the measured sense above; optional **count** metrics remain separate from USD.

---

## 6. Breakdown by model tier (if possible)

**From `llm_audit_log` (same pattern as `agents/eval/cost_projection.py`):**

```sql
SELECT
    model,
    CASE
        WHEN model ILIKE '%haiku%' THEN 'haiku'
        WHEN model ILIKE '%sonnet%' THEN 'sonnet'
        ELSE 'other'
    END AS model_tier,
    COUNT(*) AS call_count,
    SUM(COALESCE(cost_usd, 0)) AS total_cost_usd
FROM dbo.llm_audit_log
WHERE success = TRUE
GROUP BY model, model_tier
ORDER BY total_cost_usd DESC;
```

**Caveat:** Azure OpenAI **deployment names** often do not contain the substrings `haiku` or `sonnet`. Tier for **pricing** in code uses `EXTRACTION_MODEL_TIER` (`sonnet` | `haiku`) in `agents/common/llm_client.py` (`_model_tier_for_skills_extraction`). Compare `extraction_metadata->>'model_tier'` on `extracted_intelligence` to the CASE bucket above.

| Tier (CASE label) | Calls | Total USD | Notes |
|-------------------|------:|----------:|--------|
| _Run query above_ | _TBD_ | _TBD_ | Not filled from the summary rows provided. |

**Zero-cost tier:** Pattern-based Pass 1 tools — **not** represented as rows in `llm_audit_log`; report as a **logical** category (§5), not a third row in the SQL above.

---

## 7. Context extraction verification (zero LLM — code-based)

- **`extract_context`** (`agents/skills_extraction/extractors/context.py`) returns an empty list and logs `context_extraction_stub`; it does **not** import or call `llm_client` / `llm_adapter`.
- The main skills extraction persistence path in `agents/skills_extraction/agent.py` does not attach a separate LLM call for context; context JSON is not populated from an LLM in the current integration.

**Conclusion:** For the code revision present in this repository, **context extraction consumes zero LLM tokens.**

---

## 8. Tools verification analysis — **NOT IMPLEMENTED**

- The module docstring for `agents/skills_extraction/extractors/tools.py` describes optional **Haiku-class LLM verification** for ambiguous matches.
- **There is no implementation** that invokes the LLM or writes to `llm_audit_log` for tool verification (no `invoke_skills_llm`, `complete`, or `log_extraction_event` in that file).

**Report handling:** Do **not** claim measured “reduction” in Haiku verification calls. State **N/A — feature not implemented** until code paths exist and emit auditable rows.

---

## 9. Most expensive dimension

**Skills** (`skills-extraction-agent`) — **~91.5%** of total LLM cost in the measured audit cohort. **Responsibilities** is second at **~7.7%**; **tasks** third at **~0.8%**. This ranking is **by `agent_name` in `llm_audit_log`**, not by a five-way product rollout where every dimension is on the main `agent.py` path.

---

## 10. Comparison vs Week 4

| Item | Repository fact |
|------|------------------|
| [`agents/eval/cost_model_week4.md`](cost_model_week4.md) | Placeholder: *“No data yet — llm_audit_log is empty.”* **No numeric Week 4 baseline is checked into git.** |
| Generator | `python -m agents.eval.cost_projection` writes that file from `dbo.llm_audit_log` (`agents/eval/cost_projection.py`). |

**Comparison:** **Not possible** as an apples-to-apples “repo vs repo” numeric diff until you (1) populate `cost_model_week4.md` from a defined DB state and date, and (2) run the same aggregates for Week 5 with the same `EXTRACTION_MODEL_TIER` and deployment. Document both runs’ filters when you do.

---

## 11. Optimization opportunities (using §3–5 numbers)

1. **Skills dominate spend (~91.5% of $2.9147).** The highest-impact lever is still **Pass 2 skills**: prompt size, `EXTRACTION_MODEL_TIER`, caching, and deduplicating repeated extractions—any **1%** cut in skills cost saves **~$0.0267** on this cohort scale ($2.6681 × 0.01).
2. **Tasks + responsibilities together ~8.5% of cost** (~**$0.2466** = $0.2241 + $0.0225) across **78** calls vs **263** skills calls. **Average cost per call** is still highest for **skills** (~**$0.01014**/call); responsibilities ~**$0.00575**/call; tasks ~**$0.00058**/call. Before tuning prompts there, **confirm whether those `agent_name`s belong in production**; if they are experimental, **gating or removing** them avoids **~$0.2466** of this cohort’s spend without changing the **91.5%** skills block.

---

## 12. Limitations (very important)

1. **Measurements are point-in-time audit aggregates** embedded in this doc—they are **not** reproducible from git alone; re-query your DB to verify.
2. **`skills-extraction-tasks` / `skills-extraction-responsibilities`** appear in `llm_audit_log` but the **default `agents/skills_extraction/agent.py` pipeline uses stubs** for tasks/responsibilities extractors; **attribute those rows to the callers that set `agent_name`**, not to the main persistence path, unless your deployment doc says otherwise.
3. **`llm_audit_log` ↔ `extracted_intelligence`** cannot be joined by job id; cohort alignment is approximate.
4. **Week 4 baseline** in-repo is an **empty template** — comparisons are **N/A** or **post-hoc** once both baselines are generated with documented filters.
5. **Tools Haiku verification** is **not implemented** in `extract_tools` — no empirical savings or call counts for that feature.
6. **`cost_projection.py` Pass 1 vs Pass 2 split** uses `avg_cost_per_call == 0` on grouped rows — do not over-interpret as “pattern match” rows without reading that script (`agents/eval/cost_projection.py`).
7. **Eval harness** (`agents/eval/extraction_eval_core.py`, `pipeline` mode) aggregates tokens/cost from `extract_skills` metadata for **eval runs**; it does not replace DB actuals for deployed extractions unless you explicitly scope the same runs.
8. **Percentages** in §5 are **of total measured LLM USD/tokens**; they do **not** imply all dimensions are implemented in the main agent.

---

## Appendix — cohort filters

Document here when filling the audit:

- Database / environment: _e.g. dev, staging_
- `extraction_version` or git hash: _TBD_
- Time range for `extracted_at` and `llm_audit_log.created_at`: _TBD_
- `EXTRACTION_MODEL_TIER` and deployment names in use: _TBD_
