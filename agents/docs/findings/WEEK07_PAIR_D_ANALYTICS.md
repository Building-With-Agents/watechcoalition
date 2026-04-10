# Week 7 — Pair D analytics findings (Epic #175)

**Scope:** Posting freshness, trajectory scaffold, LLM insight summaries, operational guardrails, `AnalyticsRefreshed` (internal pipeline steps 10–13).

**Sub-issues:** #184 (10–11), #185 (12), #186 (guardrails + 13). Schema alignment: #187.

---

## What shipped (code)

| Area | Location |
|------|-----------|
| ORM | `PostingFreshness`, `TrajectoryMap` in `agents/common/data_store/models.py` |
| Migrations | `agents/common/data_store/migrations.py` — `dbo.posting_freshness`, `dbo.trajectory_map` |
| Step 10 | `agents/analytics/agent.py` + `agents/analytics/insights/posting_freshness_store.py` |
| Enrichment → analytics | `freshness_records` on batch `RecordEnriched`; `agents/enrichment/resolvers/freshness_slice.py` |
| Step 11 | In-memory `build_trajectory_map([])`; trajectory table exists, rows optional in Phase 1 |
| Step 12 | `agents/analytics/insights/llm_summary.py` — LLM + template fallback |
| Step 13 | `agents/analytics/insights/events.py` — `AnalyticsRefreshed` counts |
| Guardrails | `agents/analytics/insights/guardrails.py` — aggregate staleness, cardinality cap |
| Cursor rule | `.cursor/rules/analytics-guardrails.mdc` |

---

## Environment variables

| Variable | Role | Default (typical) |
|----------|------|-------------------|
| `PYTHON_DATABASE_URL` | Required for posting_freshness **persistence** | unset → skip DB writes |
| `FRESH_THRESHOLD_DAYS` | In-memory fresh bucket | 30 |
| `STALE_THRESHOLD_DAYS` | In-memory stale vs expired | 90 |
| `STALENESS_THRESHOLD_MINUTES` | Aggregate staleness alert | 15 |
| `CARDINALITY_CAP` | Skill-label cap before warning | 500 |
| `EXTRACTION_MODEL_SKILLS` | LLM model name for summaries | project default |

---

## How to verify

1. **Lint / tests** (from `agents/`):

   ```bash
   python -m ruff check .
   python -m pytest tests/test_analytics_agent.py tests/test_analytics_events.py tests/test_trajectory.py tests/test_guardrails.py tests/test_llm_summary.py tests/test_posting_freshness_store.py enrichment/tests/test_record_enriched_contract.py enrichment/tests/test_events.py
   ```

2. **Database** (dev): run migrations, then read-only SQL:

   `agents/scripts/verification_posting_freshness.sql`

3. **Demo pipeline:** `python agents/pipeline_runner.py` — order includes Enrichment → Analytics; batch path should populate `freshness_records` so Step 10 is not empty-skipped.

---

## Dashboard / contracts (#189)

`AnalyticsRefreshed` payload keys are listed in `.cursor/rules/analytics-guardrails.mdc`. Avoid adding fields without updating consumers and integration docs.

---

## Open / Phase 2

- Populate `dbo.trajectory_map` from aggregate tables when those feeds exist.
- Per-posting `AnalyticsStaleAlert` (runbook variant with `posting_id`) vs current **aggregate** stale payload — align with orchestration product expectations if both are required.
