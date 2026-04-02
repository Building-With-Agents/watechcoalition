# Week 6 Fuzzy Dedup TODO

Verified baseline as of 2026-04-02:
- Fuzzy dedup is implemented and wired through enrichment promotion.
- Shared Azure embedding audit logging is active for dedup calls, including success/failure attempts and embedding cost estimates in `dbo.llm_audit_log`.
- Local environment blocker fixed: company resolution now prefers `rapidfuzz` with `thefuzz` fallback.
- `./agents/.venv/bin/python -m pytest agents/tests/ -v` -> `217 passed, 5 skipped, 2 warnings`.

Current issue-alignment gaps:
- Strict `similarity > threshold` behavior still needs to be enforced explicitly.
- Survivor selection still uses weighted scoring, not a simple field completeness count.
- `duplicate_cluster_id` is still persisted as `TEXT`, not `UUID`.
- False-positive / false-negative rate tracking is still pending.
- The referenced Week 6 runbook / reading artifacts are still missing from this branch.

## Guardrails

- [ ] Keep changes small, reviewable, and production safe.
- [ ] Update code, tests, schema, and docs in the same pass for each behavior change.
- [ ] Reuse the existing `_embed_texts_azure()` pattern from `agents/skills_extraction/extractors/taxonomy.py`.
- [ ] Keep embedding audit logging aligned with Pair D Issue #108.
- [ ] Do not mark work complete until the matching tests and repo regression pass.

## 1. Core fuzzy dedup pipeline

- [x] Ensure embedding computation for each posting uses:
- `job title + company name + key requirements` concatenated into one dedup text payload.
- [x] Ensure each new posting queries existing postings from the same company within the last 30 days.
- [x] Ensure pairwise cosine similarity is computed between the current posting embedding and candidate embeddings.
- [ ] Change duplicate detection to follow the issue exactly:
- if `similarity > threshold`, mark `is_duplicate = TRUE` and assign `duplicate_cluster_id`.
- [x] Keep the cosine threshold configurable through `DEDUP_COSINE_THRESHOLD`, with default `0.92`.
- [ ] Align survivor selection with the issue exactly:
- keep the posting with the highest field completeness count.

## 2. Schema and persistence

- [x] Ensure `job_postings.is_duplicate` is stored as `BOOLEAN DEFAULT FALSE`.
- [ ] Change `job_postings.duplicate_cluster_id` to `UUID`.
- [ ] Add or update the migration path so existing environments can move safely to the required schema.
- [ ] Update all dedup persistence code paths to read and write the `UUID` cluster id correctly.
- [x] Verify persistence updates both the current row and the survivor row consistently.

## 3. Embeddings and audit logging

- [x] Reuse the shared Azure embedding helper pattern from taxonomy instead of introducing a new embedding client path.
- [x] Log every embedding API call to `dbo.llm_audit_log` via `log_extraction_event()` from `agents/common/llm_adapter.py`, including success/failure attempts, `agent_name`, token usage when available, and `cost_usd`.
- [x] Keep the dedup embedding audit agent name aligned with the shared embedding cost tracking pattern.
- [ ] Coordinate implementation details with Juan and Enrique for Issue #108 shared embedding cost tracking.
- [x] Verify both current-row embedding and candidate/survivor backfill embedding calls are audited.

## 4. Required test scenarios

- [x] Test: identical repost, same company, same title, 2 days apart -> current coverage exists and deduplicates.
- [x] Test: similar but different roles, same company, different title -> should NOT deduplicate.
- [x] Test: same role at different companies -> should NOT deduplicate.
- [x] Test: day 29 vs day 31 relative to the 30-day window -> boundary behavior matches the issue.
- [ ] Add or update tests for strict `>` threshold behavior at the edge.
- [ ] Add or update tests for survivor selection by field completeness count.

## 5. Regression and environment readiness

- [x] Fix local environment and dependency issues that block `pytest agents/tests/ -v`.
- [x] Ensure declared agent dependencies are installed in the active environment.
- [x] Remove import-time failures before treating regressions as complete.
- [x] Run `pytest agents/tests/ -v` and confirm no regressions.
- Verified on 2026-04-02: `217 passed, 5 skipped, 2 warnings`.

## 6. Calibration evidence

- [ ] Track false positive and false negative rates for threshold calibration.
- [ ] Build or run the replay/evaluation path needed to measure FP/FN rates on realistic data.
- [ ] Summarize threshold calibration evidence for the default `0.92` recommendation.

## 7. Findings document

- [ ] Refresh the one-page findings document for the Week 6 deliverable using the current verified baseline.
- [ ] Include:
- What I Tested
- What I Found
- Recommendation
- Tradeoffs
- Data / Evidence
- [ ] Make sure the findings doc reflects the final tested behavior, not intermediate assumptions.

## 8. Runbook and issue references

- [ ] Align implementation notes and validation steps to `WEEK-06-fuzzy-dedup-bryan-emilio-runbook.md`.
- [ ] Verify the branch contains or restores the expected Week 6 runbook/reference artifacts needed for handoff.
- [ ] Keep references consistent with:
- `ARCHITECTURE_DEEP.md`
- `ARCHITECTURAL_DECISIONS.md`
- `agents/skills_extraction/extractors/taxonomy.py`

## 9. Recommended execution order

- [x] Step 1: fix environment readiness so the full test suite can run.
- [ ] Step 2: align schema with the issue, including `duplicate_cluster_id UUID`.
- [ ] Step 3: align dedup behavior with the issue, especially strict `>` threshold and completeness-count survivor selection.
- [x] Step 4: align audit logging with Issue #108 shared embedding cost tracking. Shared `_embed_texts_azure()` now writes one audit row per HTTP attempt and records embedding cost estimates.
- [ ] Step 5: finish the remaining issue-alignment scenario updates and re-run `pytest agents/tests/ -v`.
- [ ] Step 6: write the final one-page findings document and update runbook references.
