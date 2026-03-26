# Cost Audit — Week 5 Phase 4

**Status:** Week 5 Phase 4 / **Issue #90**. §3–§5 capture a **point-in-time `llm_audit_log` cohort** (not reproducible from git alone). **`extracted_intelligence` totals**, **env-aware model-tier rollup**, and **exact cost per successful EI row** are produced by `python -m agents.eval.cost_audit_week5_report` — paste its Markdown into **§3b** and **§6** when you refresh against your DB.

---

## Week 5 Actuals (30-Record Cohort)

Team Summary; numeric totals match the `llm_audit_log` aggregates in §3–§5.

* **Total cost:** $2.9147
* **Total tokens:** 504,874
* **Total API Calls:** 341

**Cost Breakdown by Dimension:**

* **Skills:** $2.6681 (~91.5%) — *Sonnet-class extraction*
* **Responsibilities:** $0.2241 (~7.7%) — *Unexpected LLM usage*
* **Tasks:** $0.0225 (~0.8%) — *Unexpected LLM usage*
* **Tools:** $0.00 (0%) — *Pass 1 Pattern Matching successfully eliminated LLM calls*
* **Context:** $0.00 (0%) — *Pattern matching only*

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

**Persisted row totals:** See **§3b** for `SUM(extraction_tokens_used)`, `SUM(extraction_cost_usd)`, and row counts on `dbo.extracted_intelligence` (Issue #90: query EI).

**Approximate job count:** **~263** jobs if the main skills path uses **one LLM call per job** (`263` calls for `skills-extraction-agent`). The **39** calls each for tasks and responsibilities do not line up 1:1 with 263—treat those as a **separate batch or parallel experiment**, not as 263 additional full-job passes.

---

## 3b. `extracted_intelligence` totals (Issue #90 — reproducible)

Run against the same database that populated §3 (venv + `PYTHON_DATABASE_URL` from repo root):

```bash
python -m agents.eval.cost_audit_week5_report
# Optional: limit audit log to a time window; compare to informal eval baseline (USD / successful EI row)
python -m agents.eval.cost_audit_week5_report --since 2026-03-01 --baseline-per-record 0.0114
```

The command prints Markdown tables: EI aggregates (success vs failed rows), `extraction_metadata->>'model_tier'` distribution, `llm_audit_log` totals for comparison, and **resolved model tier** rollup using `agents/eval/cost_tier.py` (Azure deployment name + `EXTRACTION_MODEL_TIER`).

**Ad-hoc SQL** (subset of what the report runs):

```sql
SELECT
    COUNT(*) FILTER (WHERE NOT extraction_failed) AS success_rows,
    COUNT(*) FILTER (WHERE extraction_failed) AS failed_rows,
    SUM(extraction_tokens_used) FILTER (WHERE NOT extraction_failed) AS total_tokens,
    SUM(extraction_cost_usd) FILTER (WHERE NOT extraction_failed) AS total_cost_usd
FROM dbo.extracted_intelligence;
```

_Paste the report output below when closing Issue #90 against a specific environment._

<!-- Paste: cost_audit_week5_report output → extracted_intelligence aggregates -->

---

## 4. Cost per record (definitions + measured cohort)

Use **one definition consistently** when comparing to baselines:

| Definition | Meaning | Use when |
|------------|---------|----------|
| **A — Successful EI row** | `NOT extraction_failed`; one row per `normalized_job_id` extraction persisted | Issue #90 “per record”; exact **N** and **SUM/SUM÷N** from §3b report |
| **B — Primary skills LLM call** | Rows where `agent_name = 'skills-extraction-agent'` | Avg cost/tokens **per Pass 2 skills call** (~263 calls in §3 cohort) |
| **C — All LLM audit rows** | Every successful row in `llm_audit_log` in the window | Blended **$/call** across skills + tasks + responsibilities (341 rows) |

**Cohort B (from §3 `llm_audit_log`):**

| Metric | Formula | Approximate value |
|--------|---------|-------------------|
| Avg cost / skills call (main agent) | $2.6681 ÷ 263 | **~$0.01014** |
| Avg tokens / skills call | 454,475 ÷ 263 | **~1,728** |
| Avg cost / job if **all** audit cost is attributed to the same **263** jobs | $2.9147 ÷ 263 | **~$0.0111** (includes tasks + responsibilities overhead from the same window) |

**C:** ~**$0.00855** / row and ~**1,481** tokens/row across 341 audit rows—not equivalent to definition **A** or **B**.

**Definition A (exact):** Run `cost_audit_week5_report`; use **Avg cost / successful EI row** from the printed table (depends on how many rows exist in `extracted_intelligence`, not only the 30-record eval set).

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

## 6. Breakdown by model tier (Sonnet vs Haiku vs zero-cost)

**Recommended (Issue #90):** Run `python -m agents.eval.cost_audit_week5_report` and paste the sections **“resolved model tier (env-aware)”** and **“Per deployment name (`model` column)”** here. Resolver: `agents/eval/cost_tier.py` (`resolve_llm_audit_model_tier`) — substring `haiku`/`sonnet` → `MODEL_TIER_MAP` → exact match to `EXTRACTION_DEPLOYMENT_SKILLS` / `EXTRACTION_MODEL_SKILLS` / `AZURE_OPENAI_DEPLOYMENT_NAME` + `EXTRACTION_MODEL_TIER` (same intent as `agents/common/llm_client.py`).

**Raw SQL** (deployment names often land in `other` without the resolver):

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

Also compare `extraction_metadata->>'model_tier'` on successful `extracted_intelligence` rows (included in the report output).

_Paste env-aware tier tables from `cost_audit_week5_report` below._

<!-- Paste: cost_audit_week5_report → llm_audit_log resolved model tier -->

**Zero-cost tier:** Pass 1 **tools** pattern matching — **no** `llm_audit_log` rows; **logical** zero-cost alongside paid LLM tiers (§5).

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

**Issue #90 closure (Tools / Pass 1):** Pass 1 `extract_tools` is **pattern-only** in this revision; there is **no** Haiku verification branch, so there are **no** Haiku calls to reduce. **Measured** effect: **zero** `llm_audit_log` cost from tools (§5). Acceptance criterion is satisfied as **verified by architecture + absence of audit rows**, not as a before/after A/B on Haiku usage.

---

## 9. Most expensive dimension

**Skills** (`skills-extraction-agent`) — **~91.5%** of total LLM cost in the measured audit cohort. **Responsibilities** is second at **~7.7%**; **tasks** third at **~0.8%**. This ranking is **by `agent_name` in `llm_audit_log`**, not by a five-way product rollout where every dimension is on the main `agent.py` path.

---

## 10. Comparison vs Week 4 / informal baselines

| Item | Repository fact |
|------|------------------|
| [`agents/eval/cost_model_week4.md`](cost_model_week4.md) | Often still a placeholder until someone runs `python -m agents.eval.cost_projection` against a defined DB window and commits the output. |
| Generator | `python -m agents.eval.cost_projection` reads `dbo.llm_audit_log` (`agents/eval/cost_projection.py`). Tier labels there still use SQL `ILIKE`; prefer **`cost_audit_week5_report`** for Azure deployment–aware tiers. |

**Informal eval baselines** (30-job harness, not identical to DB cohort N): see [`agents/eval/prompt_iteration_log.md`](prompt_iteration_log.md) — e.g. **~$0.0114** / job after v2 prompt iteration, **~$0.0160** / job after Pass 1 catalog work (tokens and USD per job documented there).

**§3 cohort (definition B/C):** **~$0.01014** / primary skills call; **~$0.0111** / job if all **$2.9147** is spread over **263** skills-aligned jobs (includes extra task/responsibility LLM spend in the same audit window).

**>20% variance flag (Issue #90):** After you have **definition A** from `cost_audit_week5_report` (avg cost / successful EI row), compare to your chosen baseline (e.g. `0.0114`) using:

`python -m agents.eval.cost_audit_week5_report --baseline-per-record 0.0114`

The script prints **delta %** and flags if **|delta| > 20%**. Document the baseline source in the Issue #90 comment.

---

## 11. Optimization opportunities (using §3–5 numbers)

1. **Skills dominate spend (~91.5% of $2.9147).** The highest-impact lever is still **Pass 2 skills**: prompt size, `EXTRACTION_MODEL_TIER`, caching, and deduplicating repeated extractions—any **1%** cut in skills cost saves **~$0.0267** on this cohort scale ($2.6681 × 0.01).
2. **Tasks + responsibilities together ~8.5% of cost** (~**$0.2466** = $0.2241 + $0.0225) across **78** calls vs **263** skills calls. **Average cost per call** is still highest for **skills** (~**$0.01014**/call); responsibilities ~**$0.00575**/call; tasks ~**$0.00058**/call. Before tuning prompts there, **confirm whether those `agent_name`s belong in production**; if they are experimental, **gating or removing** them avoids **~$0.2466** of this cohort’s spend without changing the **91.5%** skills block.

---

## 12. Limitations (very important)

1. **Measurements are point-in-time audit aggregates** embedded in this doc—they are **not** reproducible from git alone; re-query your DB to verify.
2. **`skills-extraction-tasks` / `skills-extraction-responsibilities`** appear in `llm_audit_log` but the **default `agents/skills_extraction/agent.py` pipeline uses stubs** for tasks/responsibilities extractors; **attribute those rows to the callers that set `agent_name`**, not to the main persistence path, unless your deployment doc says otherwise.
3. **`llm_audit_log` ↔ `extracted_intelligence`** cannot be joined by job id; cohort alignment is approximate.
4. **`cost_model_week4.md`** may still be empty until `cost_projection` is run and committed; informal harness baselines live in **`prompt_iteration_log.md`** (§10).
5. **Tools Haiku verification** is **not implemented** in `extract_tools` — no empirical savings or call counts for that feature.
6. **`cost_projection.py` Pass 1 vs Pass 2 split** uses `avg_cost_per_call == 0` on grouped rows — do not over-interpret as “pattern match” rows without reading that script (`agents/eval/cost_projection.py`).
7. **Eval harness** (`agents/eval/extraction_eval_core.py`, `pipeline` mode) aggregates tokens/cost from `extract_skills` metadata for **eval runs**; it does not replace DB actuals for deployed extractions unless you explicitly scope the same runs.
8. **Percentages** in §5 are **of total measured LLM USD/tokens**; they do **not** imply all dimensions are implemented in the main agent.

---

## 13. Issue #90 acceptance — Phase 4 checklist

| Criterion | Status | Where |
|-----------|--------|--------|
| Query `extracted_intelligence` for `extraction_tokens_used` / `extraction_cost_usd` | **Reproducible** | `python -m agents.eval.cost_audit_week5_report`, §3b SQL; optional paste under §3b |
| Actual cost per record vs projections | **§4 + §10 + report** (`--baseline-per-record`) | Compare definition **A** to baseline; §3 cohort approximations for B/C |
| Cost by model tier (Sonnet / Haiku / zero-cost pattern) | **Reproducible** | `cost_tier.py` + report; optional paste under §6 |
| Cost by dimension (skills, tools, tasks, responsibilities, context) | Done | §5 + executive summary |
| Context = zero LLM | Done | §7 |
| Tools Pass 1 reduced Haiku calls | **N/A (verified)** | §8 — no Haiku path in `extract_tools`; zero LLM cost for tools |
| Most expensive dimension | Done | §9 |
| ≥1 optimization with data | Done | §11 |
| This audit doc | Done | Full file |
| Update `agents/eval/cost_log.md` with Week 5 actuals | Done | [`cost_log.md`](cost_log.md) §2 |

---

## Appendix — cohort filters

Document here when filling the audit:

- **Labeled / eval cohort:** 30-record Week 5 set; headline actuals above are tied to the same audit window as §3.
- Database / environment: _e.g. dev, staging_
- `extraction_version` or git hash: _TBD_
- Time range for `extracted_at` and `llm_audit_log.created_at`: _TBD_
- `EXTRACTION_MODEL_TIER` and deployment names in use: _TBD_
- **Refresh metrics:** `python -m agents.eval.cost_audit_week5_report` (optional `--since`, `--baseline-per-record`)
