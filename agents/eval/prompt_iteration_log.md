# Prompt iteration log — Skills extraction (Exercise 4.5)

Document prompt changes and before/after metrics when iterating on the skills extraction prompt. This file also records integration verification after Pair C (and other pairs) perform prompt iteration.

## Version history

| Version | Date | Change | Before metrics | After metrics |
|---------|------|--------|----------------|----------------|
| v1 | (initial) | Initial prompt in `agents/skills_extraction/prompts/skills_extraction_v1.py` | — | — |
| v0-baseline | 2026-03-18 | Placeholder ground truth (8 records, title-only, keyword stub extractor) | — | Skills P=1.00 R=0.12; Tools P=0.00 R=0.00 |
| v1-real-path-baseline | 2026-03-23 | Eval harness uses production-like path: `JobRecord` → `extract_tools` → `extract_skills(..., pass1_tools=tools)` on `extraction_ground_truth.json` (**21** hand-labeled jobs). Aggregate metrics are **MICRO** (pooled counts over all labels), not macro mean of per-job F1. Matching: lower+strip set equality on `SkillRecord.skill_name` / `ToolRecord.tool_name`. | v0-baseline (stub, 8 records) | **Skills** P=0.00 R=0.00 F1=0.00 · **Tools** P=0.49 R=0.24 F1=0.33 — see Changelog for caveats |
| v1-pipeline-30 | 2026-03-23 | **Baseline (no prompt change):** `run_extraction_eval --mode pipeline`, `extraction_ground_truth.json` (30 jobs), prompt `skills_extraction_v1`, git `b7ea71da` | — | **Skills** P=0.17 R=0.41 (91/221 matched); **Tools** P=0.54 R=0.25 (32/127 matched); ~78.6k tokens, ~\$0.62 est., 0 LLM failures |
| v2-30-record-baseline | 2026-03-23 | Ground truth expanded to **30** records. Strict matching (MICRO). Added taxonomy coverage and GenAI Extension detection rate to eval harness. | v1-real-path-baseline (21 records) | **Skills** P=0.17 R=0.43 F1=0.25 · **Tools** P=0.54 R=0.25 F1=0.34 · See Changelog for caveats and weakest categories |
| **pass1-catalog-v2** | 2026-03-24 | **Pass 1 only:** expand `TOOL_CATALOG` in `agents/skills_extraction/extractors/tools.py` (BI stacks, Atlassian, data platforms, security tools, Microsoft Office naming, split `React.js` vs `React`, Azure `Microsoft Windows Azure`, Splunk ES variants, MITRE ATT&CK); **eval:** `normalize_tool_label_for_eval()` in `extraction_eval_core.py` so `Microsoft Excel`/`excel`/`Microsoft PowerPoint`/`powerpoint`/`Microsoft Outlook`/`outlook` align for micro P/R | **Tools (v1-pipeline-30, 30 jobs):** P=0.54 R=0.25 (32/127 matched) | **Pass-1 micro on 30 jobs (same GT, `extract_tools` + eval label equivalence):** **Tools P=0.75 R=0.69** (87/127 matched, 116 pred); *not* full pipeline re-run — see § Exercise 4.5 Pass-1 audit below |
| **pass1-catalog-v3** | 2026-03-23 | **Pass 1 correctness pass + full rerun:** fix `tool_id` collision so `C++` and `C#` no longer collapse, add contextual `R`, add Office-list `Projects` → `Microsoft Projects`, keep eval tool-label equivalence for Office and extend to `Splunk (ES)` / `Fortinet Firewalls`, then re-run full pipeline on all 30 jobs | **v1-pipeline-30:** Skills P=0.17 R=0.41 (91/221 matched); Tools P=0.54 R=0.25 (32/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.16 R=0.38** (84/221 matched); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~68.6k tokens, ~\$0.48 est., 0 LLM failures |
| **v2-softskill-filter** | 2026-03-23 | **Initial v2 prompt:** add generic soft-skill suppression guidance, negative examples, and contextual replacements in `agents/skills_extraction/prompts/skills_extraction_v2.py`; this first pass proved too strict and encouraged empty outputs / over-specific relabeling | **pass1-catalog-v3:** Skills P=0.16 R=0.38 (84/221 matched, 516 pred); Tools P=0.76 R=0.72 (92/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.13 R=0.19** (41/221 matched, 309 pred); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~49.4k tokens, ~\$0.26 est., 0 LLM failures |
| **v2-softskill-filter-r2** | 2026-03-23 | **Refined v2 prompt:** preserve hard-skill extraction, prefer conventional labels, avoid role-title restatements, reduce near-duplicate paraphrases, and require a hard-skill double-check before returning empty skills | **v2-softskill-filter:** Skills P=0.13 R=0.19 (41/221 matched, 309 pred); Tools P=0.76 R=0.72 (92/127 matched) | **Full pipeline (30 jobs):** **Skills P=0.20 R=0.33** (72/221 matched, 365 pred); **Tools P=0.76 R=0.72** (92/127 matched, 121 pred); ~66.3k tokens, ~\$0.34 est., 0 LLM failures |
| v3-issue-84-eval | 2026-03-24 | **Issue #84 — eval harness only** (`agents/eval/extraction_eval.py`): `_normalize_label` for strict comparisons, **fuzzy** MICRO metrics (`rapidfuzz` token_set_ratio ≥ 85, greedy 1:1, `EVAL_EXTRACTION_FUZZY_THRESHOLD`), per-job fuzzy P/R/F1 in stdout. **Same 30-job GT file as v2** (unchanged labels). Extractor prompt/path unchanged. | v2-30-record-baseline | **Strict:** Skills GT=221 pred=516 matched=91 → P=0.18 R=0.41 F1=0.25 · Tools GT=127 pred=59 matched=32 → P=0.54 R=0.25 F1=0.34 · **Fuzzy (≥85):** Skills matched=143 → P=0.28 R=0.65 F1=0.39 · Tools matched=35 → P=0.59 R=0.28 F1=0.38 · **Taxonomy:** 524 preds, 12.02% ESCO, 0.95% GenAI ext. |
| v4-issue-85-gt-labels | 2026-03-24 | **Issue #85 — ground truth only:** normalized `skill_name` / `tool_name` for **gt-014, gt-016, gt-025**; fixed `source_span` typos; updated `labeler_notes`; removed duplicate Algorithms on gt-025 (GT skills 221→220). **Same eval code and extractor as v3.** | v3-issue-84-eval | **Strict:** Skills GT=220 pred=519 matched=108 → P=0.21 R=0.49 F1=0.29 · Tools GT=127 pred=59 matched=32 → P=0.54 R=0.25 F1=0.34 · **Fuzzy (≥85):** Skills matched=146 → P=0.28 R=0.66 F1=0.40 · Tools matched=35 → P=0.59 R=0.28 F1=0.38 · **Taxonomy:** 527 preds, 13.28% ESCO (70), 0.95% GenAI ext. |
| **v5-issue-88-prompt-v3** | 2026-03-24 | **Issue #88 / Week 5 Phase 2:** Active prompt `skills_extraction_v3.py` (`SKILLS_PROMPT_VERSION=v3`) — suppress duties/granular tasks, merge overlapping labels, strict core-only extraction, **5–15** skill cap, reconciled empty-array rule. Full pipeline, 30-job GT (220 skills). | **v4-issue-85-gt-labels:** strict skills pred=519 matched=108 P=0.21 R=0.49; tools pred=59 matched=32 | **Strict:** Skills GT=220 pred=340 matched=88 → P=0.26 R=0.40 F1=0.31 · Tools GT=127 pred=121 matched=88 → P=0.73 R=0.69 F1=0.71 · **Fuzzy (≥85):** Skills matched=118 → P=0.35 R=0.54 F1=0.42 · Tools matched=92 → P=0.76 R=0.72 F1=0.74 · **Taxonomy:** 340 preds, 16.47% ESCO (56), 1.47% GenAI ext. (5) |
| **v6-post-429-fix** | 2026-03-25 | **Post HTTP 429 fix:** rate-limit handling on the skills LLM path (`llm_client` + `extract_skills` backoff / retry-after). Full pipeline re-eval, same 30-job GT. | **v5-issue-88-prompt-v3** (scores above) | **Strict:** Skills GT=220 pred=349 matched=92 → P=0.26 R=0.42 F1=0.32 · Tools GT=127 pred=121 matched=88 → P=0.73 R=0.69 F1=0.71 · **Fuzzy (≥85):** Skills matched=122 → P=0.35 R=0.55 F1=0.43 · Tools matched=92 → P=0.76 R=0.72 F1=0.74 · **Taxonomy:** 349 preds, 38.97% ESCO (136), 1.43% GenAI ext. (5) |

## How to add an entry

1. Update the prompt in `agents/skills_extraction/prompts/skills_extraction_*.py` (or create a new versioned file).
2. Run the eval harness (Pair A) and record precision/recall per skill type.
3. Add a row to the table above with version, date, short description of the change, and before/after metrics.
4. Commit the prompt file and this log together.

---

## Integration verification checklist

- [ ] **llm_audit_log coverage:** Verify `llm_audit_log` contains entries for all LLM calls from all pairs (Bryan/Emilio, Angel/Fabian, Juan/Enrique, etc.).
- [ ] **Cost accuracy:** Verify cost data is accurate after Pair C's prompt iteration changes (compare `cost_usd` and `token_count` before/after).
- [ ] **Cost-per-record impact:** Check whether prompt revisions changed cost per record (more/fewer tokens).
- [ ] **Cost projections:** Update cost projections in `cost_model_week4.md` if per-record cost changed significantly.
- [ ] **End-to-end:** Verify `extracted_intelligence` has correct `extraction_tokens_used`, `extraction_cost_usd`, and `extraction_metadata` populated.

### llm_audit_log coverage

| Agent / pair     | LLM calls go through adapter? | Notes |
|------------------|-------------------------------|--------|
| Skills extraction| Yes (`invoke_skills_llm` → `log_extraction_event`) | Azure deployment from `EXTRACTION_*` / `AZURE_OPENAI_*` |
| _Pair C_         | _Verify_                      | _TBD_  |
| _Other_          | _Verify_                      | _TBD_  |

### Cost before / after prompt iteration

| When   | Avg tokens per record | Avg cost per record | Notes |
|--------|------------------------|---------------------|--------|
| Before | ~2,620 / job (78,603÷30) | ~\$0.0208 / job (\$0.623÷30) | Run `exercise-4-5-baseline` snapshot 2026-03-23 |
| After Pass 1 | ~2,287 / job (68,597÷30) | ~\$0.0160 / job (\$0.47841÷30) | Run `pass1-catalog-v3` snapshot 2026-03-23 |
| After v2 prompt | ~2,209 / job (66,282÷30) | ~\$0.0114 / job (\$0.3414÷30) | Run `v2-softskill-filter-r2` snapshot 2026-03-23 |

### extracted_intelligence columns

| Check                          | Result | Notes |
|--------------------------------|--------|--------|
| `extraction_tokens_used` set   | _TBD_  | _Sample query_ |
| `extraction_cost_usd` set      | _TBD_  | _Sample query_ |
| `extraction_metadata` populated | **Yes (Pass 2)** | `SkillsExtractionAgent` writes `ExtractionMetadata` JSON on LLM path; verify with DB sample |

---

## Changelog

| Date       | Who / what |
|------------|------------|
| _Week 4_   | Template created; fill after prompt iteration and integration runs. |
| 2026-03-18 | Recorded v0-baseline: 8 placeholder records (title-only, no `text` field), keyword-matching stub extractor. Skills Precision 1.00, Recall 0.12 (3/24 matched). Tools Precision 0.00, Recall 0.00 (0/12). Ground truth dataset is WIP — expand to 30-50 records with full `text` descriptions and run against real LLM extractor for meaningful baseline. |
| 2026-03-23 | **v1-real-path-baseline:** GT 21 records, real extractor path. Skills P=0.00 R=0.00; Tools P=0.49 R=0.24. |
| 2026-03-23 | **v1-pipeline-30:** Full pipeline eval on 30 labeled jobs. Artifacts: `agents/eval/runs/20260323T111224-0600_exercise-4-5-baseline.json`. |
| 2026-03-23 | **v2-30-record-baseline:** GT expanded to 30 records. Skills P=0.18 R=0.43 F1=0.25; Tools P=0.54 R=0.25 F1=0.34. Added taxonomy coverage and GenAI detection rate. |
| 2026-03-24 | **Exercise 4.5 — Pass 1 catalog + eval label alignment:** See § below. |
| 2026-03-23 | **pass1-catalog-v3:** Full pipeline rerun after Pass 1 correctness fixes. Tools P=0.76 R=0.72. |
| 2026-03-23 | **v2-softskill-filter:** Initial v2 prompt. Skills P=0.13 R=0.19; Tools P=0.76 R=0.72. |
| 2026-03-23 | **v2-softskill-filter-r2:** Refined v2 prompt. Skills P=0.20 R=0.33; Tools P=0.76 R=0.72. |
| 2026-03-23 | **v3-issue-84-eval:** Issue #84 — fuzzy matching added. Strict skills P=0.18 R=0.41; Fuzzy skills P=0.28 R=0.65. |
| 2026-03-24 | **v4-issue-85-gt-labels:** Issue #85 — GT label normalization for gt-014, gt-016, gt-025. Strict skills P=0.21 R=0.49 F1=0.29; Fuzzy P=0.28 R=0.66 F1=0.40. |
| 2026-03-24 | **v5-issue-88-prompt-v3 (`skills_extraction_v3`):** Issue #88 / Week 5 Phase 2 — full pipeline on 30-job GT. **Strict skills:** pred 340 vs v4’s 519; matched 88 vs 108; P 0.26 (was 0.21), R 0.40 (was 0.49), F1 0.31 (was 0.29). **Fuzzy skills:** P 0.35 / R 0.54 / F1 0.42 (was 0.28 / 0.66 / 0.40). **Tools (sanity):** strict P=0.73 R=0.69 F1=0.71; fuzzy P=0.76 R=0.72. **Taxonomy:** 340 preds, 16.47% ESCO (56), 1.47% GenAI ext. (5). **Readout:** Big drop in predicted skill count and higher strict precision, but strict recall and match count fell (true positives removed with noise). Fuzzy F1 up slightly; remaining gap partly label/normalization. Average ~11.3 skills/job vs ~7.3 GT — 5–15 cap not reliably enforced by the model alone; consider post-parse cap or prompt tuning. |
| 2026-03-25 | **v6-post-429-fix:** Full pipeline re-eval after 429 handling. **Strict skills:** P=0.26 R=0.42 F1=0.32 (92/220); pred=349. **Strict tools:** P=0.73 R=0.69 F1=0.71. **Fuzzy skills:** P=0.35 R=0.55 F1=0.43. **Fuzzy tools:** P=0.76 R=0.72 F1=0.74. **Taxonomy:** 38.97% ESCO (136/349), 1.43% GenAI ext. (5). |

---

## Exercise 4.5 — Pass 1 catalog audit (GT tools vs `extract_tools`)

### Root cause

`TOOL_CATALOG` was missing many **literal vendor / BI / collaboration** strings that appear in `extraction_ground_truth.json` (e.g. Tableau, Looker, Power BI, Jira, Confluence, Databricks, dbt). Pass 1 cannot emit a `ToolRecord` for a name that is not in the catalog, so **tools recall stayed low** even when Pass 2 skills precision was high.

**Additional:** `React` and `React.js` shared one `ToolDefinition`, so matches on `React.js` still emitted `tool_name=”React”`, which did not match GT `react.js`. **GT vs canonical names** for Office (e.g. `excel` vs `Microsoft Excel`) also inflated missed counts.

### After this change

On all 30 `extraction_ground_truth.json` jobs, the current `extract_tools` + `normalize_tool_label_for_eval` yields **92 / 127** GT tool labels matched (micro **P≈0.76, R≈0.72**).
