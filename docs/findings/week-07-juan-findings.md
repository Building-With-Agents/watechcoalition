# Week 7 Findings — Juan Reyes

## What I Built
- **PostingFreshness** (`dbo.posting_freshness`): `posting_id` (Text PK), `first_seen` / `last_seen` (timestamptz), `duration_days` (int), `is_repost`, `repost_count`, `fill_proxy`, `computed_at`; index `ix_posting_freshness_posting_id`. **Posting-age** thresholds for `classify_freshness` / `detect_staleness` remain **`FRESH_THRESHOLD_DAYS`** / **`STALE_THRESHOLD_DAYS`** (defaults **30** / **90**) in `models.py`.
- **TrajectoryMap** (`dbo.trajectory_map`): `role_id` PK, `trajectory_data` JSON, `computed_at` — ORM scaffold only; **no** Phase 2 population yet.
- **Staleness (aggregate):** `check_staleness(table_name, computed_at)` in `guardrails.py` — true when age **strictly exceeds** `STALENESS_THRESHOLD_MINUTES` (default **15**). **`AnalyticsStaleAlert`** payload from `build_stale_alert_payload` (`event_type`, `table_name`, `computed_at`, `queried_at`, `age_minutes`); published via `register_analytics_alert_bus` when bus is set.
- **Cardinality:** `cap_cardinality` with **`CARDINALITY_CAP`** (default **500**); overflow → first N labels + a single **`"Other"`** at the end. **`CardinalityWarning`** from `build_cardinality_warning_payload` (`table`, `column`, `cardinality_count`, `threshold`, `triggered_at`).
- **Pipeline:** `AnalyticsAgent` runs a **13-step** internal order; **step 10** builds in-memory posting-freshness rows, runs `detect_staleness` + aggregate `check_staleness` + skill-label `cap_cardinality`; **step 11** sets `build_trajectory_map([])` (empty scaffold). DB persistence for `PostingFreshness` / `TrajectoryMap` rows is **not** wired in Phase 1.

## Guardrail Behavior
- **Staleness:** `AnalyticsStaleAlert` fires when `check_staleness("posting_freshness", aggregate_computed_at)` is true — i.e. **`now - computed_at` > `STALENESS_THRESHOLD_MINUTES`** (boundary: exactly at threshold → **not** stale). Optional payload key **`analytics_aggregate_computed_at`** (ISO) overrides the default “now” used for the aggregate timestamp in step 10. Configure with **`STALENESS_THRESHOLD_MINUTES`**.
- **Cardinality:** Warning when **unique skill labels** (from enriched `skills` on `RecordEnriched` rows) exceed **`CARDINALITY_CAP`**; emits **`CardinalityWarning`** for table `skill_demand_weekly`, column `skill_label`. **`"Other"`** appears **once** at the end of the capped list; coalesces all overflow labels into that bucket.

## Posting Lifecycle Findings
- **`duration_days`:** Taken from enriched row **`days_since_posted`** (int, default **0**). **`first_seen`** / **`last_seen`** are both set to the batch **`computed_at`** in the current scaffold (no separate publish-date pipeline yet).
- **Repost detection:** **`is_repost`** = `bool(record.get("is_duplicate") or record.get("is_repost"))`. **`repost_count`** = `int(record.get("repost_count", 0))`, bumped to **1** if repost is true but count was **0**.
- **`fill_proxy`:** **`bool(record.get("fill_proxy", False))`** — caller must pass a signal (e.g. posting disappeared / filled); no inference in the agent today.

## Phase 2 Notes
- **`trajectory_map`:** Should hold **per-role** trajectory JSON (`trajectory_data`) aligned with aggregate feeds (**`skill_velocity`**, **`skill_demand_weekly`**, **`sector_summary_weekly`**, **`role_snapshot_weekly`**) and/or the in-memory **`build_trajectory_map`** shape (`rising` / `stable` / `declining`, `delta`, `confidence` per skill or `sector:{name}` key).
- **To populate:** Nightly (or batch) writers inserting **`TrajectoryMap`** rows; wire **`build_trajectory_map`** output from real aggregate queries; optional convergence with ARCHITECTURE_DEEP “expanding/stable/contracting” vocabulary.

## Cursor Rules Notes
- **Update `analytics-guardrails.mdc` §1:** Replace the old **`id` / `checked_at` / `days_since_posted` / `freshness_status`** description with the **runbook** columns actually in `PostingFreshness` (`first_seen`, `last_seen`, `duration_days`, `is_repost`, `repost_count`, `fill_proxy`, `computed_at`). Keep **`FRESH_THRESHOLD_DAYS` / `STALE_THRESHOLD_DAYS`** docs next to **`classify_freshness`** / `detect_staleness`, not as duplicate DB columns unless reintroduced.
- **§2 / trajectory:** Note the **SQLAlchemy** scaffold uses **`role_id` + `trajectory_data` JSON**, while **`trajectory.py`** uses skill/sector **string keys** for the pure **`build_trajectory_map`** helper — cross-link both.

## Data / Evidence
- **Tests:** Last full sweep **`agents/tests/`**: **257 passed**, **6 skipped** (warnings only: LangSmith, SQLAlchemy legacy `Query.get`, pgvector reflect).
- **Sample:** Fixture-driven **`AnalyticsRefreshed`** unchanged for demos; step 10 typically **does not** emit cardinality alerts unless **>500** distinct skill labels appear on the batch (rare in fixtures).
