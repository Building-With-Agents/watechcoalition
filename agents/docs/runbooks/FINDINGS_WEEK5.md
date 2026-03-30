# Week 5 — Tasks, Responsibilities & Context Extraction — Code Audit Findings

**Branch context:** `week-05/tasks-responsibilities-context` (and merged development patterns).  
**Scope:** `agents/skills_extraction/extractors/{tasks,responsibilities,context}.py`, `agents/skills_extraction/agent.py`.  
**Template:** Aligned with the findings structure used in `agents/docs/EXP-004_FINDINGS_AND_ASSETS.md` (What we tested / What we found / Recommendation / Tradeoffs / Evidence / Conclusion).

---

## 1. What We Audited

| Area | Question |
|------|----------|
| **Model tier routing** | Do Tasks use Haiku-class routing, Responsibilities Sonnet-class, Context regex-only? |
| **Persistence** | Does the agent persist all JSONB dimensions in one transactional `save()` without leaving rows half-written? |
| **Events** | Does the `SkillsExtracted` payload expose `tasks_count`, `responsibilities_count`, and `context_signals_count` (and per-record summaries)? |
| **Pass 1 → Pass 2** | How are context signals fed into LLM prompts to avoid redundant full-document context calls? |

---

## 2. What We Found

### 2.1 Model tier routing (PASS with operational caveat)

| Dimension | Implementation | Evidence |
|-----------|------------------|----------|
| **Tasks (Pass 2)** | Documented as Haiku-class; `invoke_structured_extraction_llm(..., model_tier_for_cost="haiku")`; deployment resolution order `EXTRACTION_DEPLOYMENT_TASKS` → `EXTRACTION_MODEL_TASKS` → `AZURE_OPENAI_DEPLOYMENT_NAME`. | `agents/skills_extraction/extractors/tasks.py` |
| **Responsibilities (Pass 2)** | Documented as Sonnet-class; `model_tier_for_cost="sonnet"`; keys `EXTRACTION_DEPLOYMENT_RESPONSIBILITIES` → `EXTRACTION_MODEL_RESPONSIBILITIES` → fallback deployment. | `agents/skills_extraction/extractors/responsibilities.py` |
| **Context (Pass 1)** | Regex/keyword only; metadata sets `tokens_used: 0`, `provider: "pattern-matching"`, `model: "none"`, no LLM invoke. | `agents/skills_extraction/extractors/context.py` |

**Caveat:** “Haiku” and “Sonnet” here are **tier labels for cost estimation** (`compute_extraction_cost`) and **separate Azure deployment env slots**. The runtime model is whatever deployment name those env vars point to. Operators must map deployments consistently with intended capability/cost (Haiku-like for tasks, Sonnet-like for responsibilities).

**Out of scope but adjacent:** Skills Pass 2 uses `invoke_skills_llm` / skills-specific deployments (typically Sonnet-tier cost in `llm_client`); that path is unchanged by Week 5 task/responsibility extractors.

### 2.2 Transaction / JSONB persistence (PASS — one commit per `save()` call)

`SQLAlchemyExtractionStore.save()` wraps **all** `ExtractionResult` rows in a **single** `session_scope()` context manager (`agents/common/data_store/database.py`: commit on success, rollback on exception).

For each result with a non-null `normalized_job_id`, the same ORM row is updated with **all** of:

- `skills`
- `tools` (from `ToolRecord.model_dump()`)
- `tasks`
- `responsibilities`
- `context`

plus scalar metadata (`extraction_version`, `extraction_model`, tokens, cost, warnings, `extraction_failed`, `extraction_metadata`, etc.) **before** the session commits.

**Implications:**

- **No partial JSONB columns per row:** Within one iteration of the loop, every listed column on that `ExtractedIntelligence` instance is assigned; SQLAlchemy persists them together when the transaction commits.
- **Batch atomicity:** For a given `save(results)` call, either **all** mutations in that loop commit or **none** (rollback on error).
- **Skipped rows:** Items with `normalized_job_id is None` are not written (intentional); they do not create half-filled rows.

### 2.3 `SkillsExtracted` event payload (PASS)

`_build_payload` always includes:

- `tasks_count` — sum of task list lengths across results (batch) or single-record length when `len(results) == 1` (re-stated in the single-record `payload.update` block).
- `responsibilities_count` — same pattern for responsibilities.
- `context_signals_count` — same for context; **`context_count`** duplicates the same total for backward compatibility.

Per-record summaries in `records[]` from `_result_summary` include `tasks`, `responsibilities`, `context`, and per-record `tasks_count`, `responsibilities_count`, `context_signals_count`.

The legacy fixture path (`_legacy_fixture_response`) sets these counts to `0` with empty lists — consistent for stub mode.

### 2.4 Pass 1 context → Pass 2 LLM (token design)

1. **`extract_context(job)`** runs first in `_extract_work_item_no_taxonomy`, producing `context_signals` and metadata with **zero LLM tokens**.
2. **`_format_pass1_context_for_prompt`** (`context.py`) serializes each signal to a **short line**: `signal_type`, `value`, and `confidence` — not a second full-text paste of the job posting.
3. That block is injected into **`extract_tasks`** and **`extract_responsibilities`** prompts as “Pass 1 context signals” so the model can disambiguate (e.g. seniority, scope) **without** an extra LLM call over the raw posting for “context understanding.”
4. The job body is still included once per Pass 2 call (tasks vs responsibilities each have their own prompt with title/description/requirements/responsibilities sections) — Week 5 does **not** deduplicate those body sections across the two LLM calls; the **token savings** are specifically from **not** using an LLM for context extraction and from **compressing** Pass 1 output to a compact signal list instead of re-embedding full narrative context.

---

## 3. Recommendation

- **Keep** the env-var split for tasks vs responsibilities deployments so operators can map Haiku-class vs Sonnet-class (or equivalent) endpoints explicitly.
- **Document in ops runbooks** the exact Azure deployment names bound to `EXTRACTION_DEPLOYMENT_TASKS` and `EXTRACTION_DEPLOYMENT_RESPONSIBILITIES` so audits match intent.
- **Rely on** the existing single `session_scope()` in `save()` for training and demos that need “all five JSONB blobs or nothing” per batch commit.

---

## 4. Tradeoffs — Regex (Context) vs LLM nuance

| Regex / Pass 1 (Context) | LLM / Pass 2 (Tasks, Responsibilities) |
|--------------------------|------------------------------------------|
| **Fast, deterministic, zero token cost.** | **Slower, stochastic, billed per token.** |
| **Coverage limited** to enumerated patterns (`remote_policy`, `team_size`, `reporting_structure`, `work_methodology`, `ai_adoption_signal`). Paraphrases, implicit cues, or novel phrasing may be missed. | **Interpretive** — can capture nuanced ownership, scope, and task structure when the model follows instructions. |
| **High precision** when patterns match literal keywords (e.g. “hybrid”, “Scrum”). | **Risk of hallucination or bad spans** (mitigated elsewhere with span coercion / optional spans). |
| Signals are **short** when injected into Pass 2 prompts → small marginal token cost vs re-summarizing the posting with an LLM. | Full job text still sent per extractor call → main token spend remains the body sections + instructions. |

**Acknowledged tradeoff:** We accept **recall limits** on context dimensions in exchange for **predictable cost and latency** on Pass 1. Richer “context understanding” would require LLM-based Pass 1 (higher cost) or expanded pattern catalogs (maintenance burden).

---

## 5. Evidence (file pointers)

| File | Relevant symbols / behavior |
|------|-----------------------------|
| `agents/skills_extraction/extractors/tasks.py` | `model_tier_for_cost="haiku"`, `_TASKS_DEPLOYMENT_KEYS`, `_format_pass1_context_for_prompt` in prompt |
| `agents/skills_extraction/extractors/responsibilities.py` | `model_tier_for_cost="sonnet"`, `_RESP_DEPLOYMENT_KEYS`, Pass 1 block in prompt |
| `agents/skills_extraction/extractors/context.py` | `_CONTEXT_PATTERNS`, `extract_context`, `_format_pass1_context_for_prompt` |
| `agents/skills_extraction/agent.py` | `_extract_work_item_no_taxonomy` (order: context → tools → tasks → responsibilities → skills no-taxonomy), `SQLAlchemyExtractionStore.save`, `_build_payload`, `_result_summary` |
| `agents/common/data_store/database.py` | `session_scope()` transaction semantics |
| `agents/common/data_store/models.py` | `ExtractedIntelligence` JSONB columns: `skills`, `tools`, `tasks`, `responsibilities`, `context` |

---

## 6. Conclusion

The Week 5 extractors **conform to the intended tier routing** (Haiku cost tier + task deployments for tasks, Sonnet cost tier + responsibility deployments for responsibilities, regex-only for context). The agent **writes all five JSONB extraction columns** on each persisted row and does so inside **one database transaction per `save()` invocation**, avoiding partial commits for that call. The **`SkillsExtracted` payload** includes **`tasks_count`**, **`responsibilities_count`**, and **`context_signals_count`** (plus **`context_count`** and per-record mirrors). Pass 1 signals are **injected as a compact text block** into Pass 2 prompts to add disambiguation **without** an LLM-based context pass; the main tradeoff is **regex recall vs LLM nuance** on context dimensions.
