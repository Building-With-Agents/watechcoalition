# Prompt iteration log — Skills extraction (Exercise 4.5)

Document prompt changes and before/after metrics when iterating on the skills extraction prompt. This file also records integration verification after Pair C (and other pairs) perform prompt iteration.

## Version history

| Version | Date | Change | Before metrics | After metrics |
|---------|------|--------|----------------|----------------|
| v1 | (initial) | Initial prompt in `agents/skills_extraction/prompts/skills_extraction_v1.py` | — | — |
| v0-baseline | 2026-03-18 | Placeholder ground truth (8 records, title-only, keyword stub extractor) | — | Skills P=1.00 R=0.12; Tools P=0.00 R=0.00 |

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
