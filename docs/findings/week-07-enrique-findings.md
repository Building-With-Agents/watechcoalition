# Week 7 Findings — Enrique

## What I Built

- **LLM insight summary generator** (`agents/analytics/insights/llm_summary.py`): For each trajectory key, `_build_prompt` injects the dimension `label`, `TrajectoryEntry` fields (`trend`, `delta`, `confidence`), and the full posting-freshness sample: total count plus per-bucket counts (`fresh` / `stale` / `expired`). The user message is sent to `llm_adapter.complete()` with `agent_name=analytics-agent`, model from `EXTRACTION_MODEL_SKILLS` (default `claude-sonnet-4-5`), a fixed system prompt (3–5 paragraphs, facts only, no markdown headings), and `max_tokens=1200`. `generate_summaries` maps keys to `skill_label` vs `sector_label` (`sector:` prefix strips to sector name).

- **Deterministic fallback**: `FALLBACK_TEMPLATE` is a single sentence: label, trend, integer delta, `len(freshness_records)` as “active postings tracked,” confidence as percent, plus “(Generated from template.).” Same trajectory + freshness inputs as the LLM path; no invented entities.

- **Metadata tracking**: Each `SummaryResult` includes `is_llm_generated`, `model_used` (LLM model id or `None`), `generated_at` (UTC ISO 8601 with `Z`), and `summary_text`. Skill/sector scope fields set in `generate_summaries`.

- **Step 12** (`_pipeline_step_12_disruption_fingerprint`): Runs after step 11; calls `generate_summaries(self._last_trajectory_scaffold, self._freshness_results)` and logs `analytics_step_12_llm_summaries` with `total`, `llm_generated`, `fallback`, `batch_id`.

- **AnalyticsRefreshed** (`agents/analytics/insights/events.py`): Built in step 13 after the pipeline; `process()` returns this envelope. Payload includes `event_type`, `batch_id`, `triggered_by_batch_id` (same as `batch_id`, for downstream compatibility), `refreshed_at`, and counts: `freshness_record_count`, `trajectory_map_count`, `summaries_generated_count`, `llm_generated_count`, `fallback_count`. Fires once per successful `process()` after steps 1–12 complete.

## LLM vs Fallback Comparison

| | **LLM path** | **Fallback path** |
|---|--------------|-------------------|
| **Output** | 3–5 paragraphs of prose from the model | One templated sentence |
| **Reader experience** | Narrative interpretation of trend, delta, confidence, freshness mix | Immediate scan of metrics; clearly marked as template |
| **Triggers fallback** | Any exception from `complete()`, or response with `success` false, `extraction_failed` true, or empty/whitespace `content` | — |

## Guardrail Behavior

- **`is_llm_generated`**: `True` only when `complete()` returns success, not failed extraction, and non-empty stripped `content`. Otherwise `False` (including all fallback outcomes).
- **`model_used`**: Set to the resolved model string (env `EXTRACTION_MODEL_SKILLS` or default) on LLM success; `None` on fallback.

## Cursor Rules Notes

- **analytics-guardrails.mdc** §5 describes the insight summary *record* (`summary_text`, `is_llm_generated`, `generated_at`, `skill_label`, `sector_label`) — still accurate.
- **Additions to document elsewhere**: The **`AnalyticsRefreshed` emission** is now implemented with explicit **aggregate counts** in the payload (`freshness_record_count`, `trajectory_map_count`, summary totals, LLM vs fallback counts). The rule file’s event-catalog line still lists older placeholder keys (`aggregate_types`, `record_count`, `refresh_duration_ms`); consider aligning that row with `events.build_analytics_refreshed_event` or marking the payload as versioned/evolving.
- **`triggered_by_batch_id`** is duplicated alongside **`batch_id`** for consumers that already keyed off the former name.

## Data / Evidence

- **Tests**: `agents/tests/test_llm_summary.py` — 8 cases (LLM success, exceptions, empty content, sector/skill keys, mixed maps, template numeric fidelity, never-raises). `agents/tests/test_analytics_events.py` — 7 cases on `build_analytics_refreshed_event` (payload shape, counts, ISO `refreshed_at`, envelope ids). `agents/tests/test_analytics_agent.py` updated for the new `AnalyticsRefreshed` payload.
- **Sample (fallback shape)**: With label `Python`, rising, delta +12, confidence 0.91, two freshness rows:  
  `Python is rising with a posting delta of +12 and 2 active postings tracked. Confidence: 91%. (Generated from template.)`
- **Sample (current pipeline)**: Step 11 uses `build_trajectory_map([])`, so **zero** trajectory keys → **no** `generate_summary` calls and an empty `summaries` list until real aggregate rows feed the scaffold.
