# Prompt iteration log — Skills extraction (Exercise 4.5)

Document prompt changes and before/after metrics when iterating on the skills extraction prompt.

## Version history

| Version | Date | Change | Before metrics | After metrics |
|---------|------|--------|----------------|----------------|
| v1 | (initial) | Initial prompt in `agents/skills_extraction/prompts/skills_extraction_v1.py` | — | — |
| v0-baseline | 2026-03-18 | Placeholder ground truth (8 records, title-only, keyword stub extractor) | — | Skills P=1.00 R=0.12; Tools P=0.00 R=0.00 |
| v1-real-path-baseline | 2026-03-23 | Eval harness uses production-like path: `JobRecord` → `extract_tools` → `extract_skills(..., pass1_tools=tools)` on `extraction_ground_truth.json` (**21** hand-labeled jobs). Aggregate metrics are **MICRO** (pooled counts over all labels), not macro mean of per-job F1. Matching: lower+strip set equality on `SkillRecord.skill_name` / `ToolRecord.tool_name`. | v0-baseline (stub, 8 records) | **Skills** P=0.00 R=0.00 F1=0.00 · **Tools** P=0.49 R=0.24 F1=0.33 — see Changelog for caveats |
| v2-30-record-baseline | 2026-03-23 | Ground truth expanded to **30** records. Strict matching (MICRO). Added taxonomy coverage and GenAI Extension detection rate to eval harness. | v1-real-path-baseline (21 records) | **Skills** P=0.17 R=0.43 F1=0.25 · **Tools** P=0.54 R=0.25 F1=0.34 · See Changelog for caveats and weakest categories |
| v3-issue-84-eval | 2026-03-24 | **Issue #84 — eval harness only** (`agents/eval/extraction_eval.py`): `_normalize_label` for strict comparisons, **fuzzy** MICRO metrics (`rapidfuzz` token_set_ratio ≥ 85, greedy 1:1, `EVAL_EXTRACTION_FUZZY_THRESHOLD`), per-job fuzzy P/R/F1 in stdout. **Same 30-job GT file as v2** (unchanged labels). Extractor prompt/path unchanged. | v2-30-record-baseline | **Strict:** Skills GT=221 pred=516 matched=91 → P=0.18 R=0.41 F1=0.25 · Tools GT=127 pred=59 matched=32 → P=0.54 R=0.25 F1=0.34 · **Fuzzy (≥85):** Skills matched=143 → P=0.28 R=0.65 F1=0.39 · Tools matched=35 → P=0.59 R=0.28 F1=0.38 · **Taxonomy:** 524 preds, 12.02% ESCO, 0.95% GenAI ext. |
| v4-issue-85-gt-labels | 2026-03-24 | **Issue #85 — ground truth only:** normalized `skill_name` / `tool_name` for **gt-014, gt-016, gt-025**; fixed `source_span` typos; updated `labeler_notes`; removed duplicate Algorithms on gt-025 (GT skills 221→220). **Same eval code and extractor as v3.** | v3-issue-84-eval | **Strict:** Skills GT=220 pred=519 matched=108 → P=0.21 R=0.49 F1=0.29 · Tools GT=127 pred=59 matched=32 → P=0.54 R=0.25 F1=0.34 · **Fuzzy (≥85):** Skills matched=146 → P=0.28 R=0.66 F1=0.40 · Tools matched=35 → P=0.59 R=0.28 F1=0.38 · **Taxonomy:** 527 preds, 13.28% ESCO (70), 0.95% GenAI ext. |

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
| Skills extraction| _Verify_                      | _TBD_  |
| _Pair C_         | _Verify_                      | _TBD_  |
| _Other_          | _Verify_                      | _TBD_  |

### Cost before / after prompt iteration

| When   | Avg tokens per record | Avg cost per record | Notes |
|--------|------------------------|---------------------|--------|
| Before | _TBD_                  | _TBD_               | _Baseline_ |
| After  | _TBD_                  | _TBD_               | _Post Pair C changes_ |

### extracted_intelligence columns

| Check                          | Result | Notes |
|--------------------------------|--------|--------|
| `extraction_tokens_used` set   | _TBD_  | _Sample query_ |
| `extraction_cost_usd` set      | _TBD_  | _Sample query_ |
| `extraction_metadata` populated | _TBD_  | _JSON shape_ |

---

## Changelog

| Date       | Who / what |
|------------|------------|
| _Week 4_   | Template created; fill after prompt iteration and integration runs. |
| 2026-03-18 | Recorded v0-baseline: 8 placeholder records (title-only, no `text` field), keyword-matching stub extractor. Skills Precision 1.00, Recall 0.12 (3/24 matched). Tools Precision 0.00, Recall 0.00 (0/12). Ground truth dataset is WIP — expand to 30-50 records with full `text` descriptions and run against real LLM extractor for meaningful baseline. |
| 2026-03-23 | **v1-real-path-baseline — baseline before prompt iteration:** Ground truth file `agents/eval/extraction_ground_truth.json` contains **21** records (issue copy that says 25 is outdated). Eval harness (`agents/eval/extraction_eval.py`) now uses the **real extractor path** only: build `JobRecord` from GT → `extract_tools(job_record)` → `extract_skills(job_record, pass1_tools=tools)`; no keyword stub. **Aggregate metrics (MICRO):** over 21 jobs, totals were GT skills=149 / pred skills=0 / matched=0 → Skills P=0.00, R=0.00, F1=0.00; GT tools=82 / pred tools=41 / matched=20 → Tools P=0.49, R=0.24, F1=0.33. **Caveats:** (1) **Skills** depend on Azure OpenAI (`AZURE_OPENAI_*`, deployment vars in `agents/common/llm_client.py`) and `langchain-openai` in the active venv; the reference run had Pass 2 yield no skills (`extraction_failed`), so **re-run `python -m agents.eval.extraction_eval` with a working LLM setup and paste updated skills P/R/F1 before/after prompt edits.** (2) Taxonomy may call Azure embeddings (`agents/skills_extraction/extractors/taxonomy.py`). (3) Eval uses strict normalized string equality, not fuzzy synonyms. **Tools** figures above reflect real Pass 1 only. |
| 2026-03-23 | **v2-30-record-baseline:** Ground truth expanded to **30** records. Strict matching (MICRO). **Aggregate metrics:** GT skills=221 / pred=538 / matched=95 → Skills P=0.18, R=0.43, F1=0.25; GT tools=127 / pred=59 / matched=32 → Tools P=0.54, R=0.25, F1=0.34. Eval harness now reports taxonomy coverage and GenAI Extension detection rate (see `--- TAXONOMY (skills) ---` section). **Note:** Embedding 429 (rate-limit) warnings occurred during the run; evaluation completed. **Weakest extraction categories:** (1) Skills: long-form composite analyst/product labels; (2) Skills: AI product management / roadmap terminology; (3) Tools: BI/analytics, PM/collaboration, and GenAI/platform tools are under-detected. |
| 2026-03-23 | **v3-issue-84-eval:** **Issue #84** updates `extraction_eval.py`: normalized strict label sets, fuzzy matching (token_set_ratio ≥ 85), env `EVAL_EXTRACTION_FUZZY_THRESHOLD`. Same 30-job GT as v2. **Reference v3 baseline run (pre–Issue #85):** strict skills matched=91 / GT=221 / pred=516; fuzzy skills matched=143; tools strict 32 / fuzzy 35; taxonomy 524 preds, 12.02% ESCO (63). |
| 2026-03-24 | **v4-issue-85-gt-labels:** **Issue #85** addresses GT-only normalization for gt-014, gt-016, gt-025; **v3** harness unchanged. Metrics in version table row **issue-85-gt-labels**. |
