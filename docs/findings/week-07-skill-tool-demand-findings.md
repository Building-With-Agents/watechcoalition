# Week 7 — Skill & tool demand (Pair A) — findings

## Sync status (keep current when contracts change)

**Implementation alignment:** Aggregate tables and refresh functions match across:

| Artifact | Role |
|----------|------|
| `agents/common/data_store/models.py` | ORM: `SkillDemandWeekly`, `ToolDemandWeekly`, `SkillVelocity`, `SkillCoOccurrence` |
| `agents/analytics/aggregators/demand_weekly.py` | Steps **2–3** (`refresh_skill_demand_weekly`, `refresh_tool_demand_weekly`; exports `_SKILLS_EXPANDED` for step 9) |
| `agents/analytics/aggregators/velocity.py` | Step **8** (`refresh_skill_velocity`) |
| `agents/analytics/aggregators/co_occurrence.py` | Step **9** (`refresh_skill_co_occurrence`) |
| `agents/analytics/aggregators/__init__.py` | Public exports for all four refresh functions |
| `.cursor/rules/skill-tool-demand.mdc` | **Frozen IMP-021** column contract + DAG (supersedes stale `ARCHITECTURE_DEEP` names like `growth_rate`) |

**Done in this track:** Steps 2, 3, 8, 9 aggregators + unit/DB-smoke tests under `agents/tests/test_{demand_weekly,velocity,co_occurrence}.py`; **IMP-021 / cross-check automation:** [agents/scripts/verify_aggregates.py](../../agents/scripts/verify_aggregates.py) (step 2 global sum) and [agents/scripts/verify_analytics_aggregates.py](../../agents/scripts/verify_analytics_aggregates.py) (steps 2–3 drift + per-row checks, step 8 `demand_count`/`esco_uri`, step 9 lex + top-200 parity vs manual SQL with `COLLATE "C"` to match Python `sorted()`).

**Still Week 7 / Pair A (typical next tasks):** Weekly Insights Streamlit (see `.cursor/rules/streamlit-dashboard.mdc`), `AnalyticsRefreshed` payload extensions per `event-contracts.mdc`.

**Runbook alignment:** Pair A verification and example SQL live in [agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md](../../agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md) — **§0 Step 2** (quick aggregate spot-checks), **§5 Layer 6** Tables 1–2 and 6–7 (Pair A tables). The runbook’s **Table 6** sample query still names `current_week_count` / `velocity_pct`; this implementation uses **`week`**, **`demand_count`**, **`week_over_week_change`**, **`four_week_trend`** (see §5 “Data / Evidence” query below).

**Analytics agent wiring:** [agents/analytics/agent.py](../../agents/analytics/agent.py) runs aggregators **2 → 3 → (8, 9 if 2 ok)** inside `process()`, each step in its own `session_scope()` (no single wrapping transaction). `default_analytics_target_week()` uses the **prior ISO week’s Monday** (PostgreSQL week anchor); override with payload keys `analytics_target_week`, `week_start`, or `aggregate_week_start` (ISO date). Outbound `AnalyticsRefreshed` includes `aggregate_refresh` (row counts / skip flags) plus the legacy fixture JSON overlay. Health: `ok` if DB reachable; `degraded` if URL missing, or URL set but DB unreachable **and** analytics fixture exists (walking skeleton); `down` if unreachable and no fixture. Tests: [agents/tests/test_analytics_agent.py](../../agents/tests/test_analytics_agent.py) (patches all four `refresh_*`). [agents/pipeline_runner.py](../../agents/pipeline_runner.py) documents that **13-step** internal items **2, 3, 8, 9** execute inside the Analytics agent’s `process()`.

---

## What I Built

- **File:** [agents/common/data_store/models.py](../../agents/common/data_store/models.py)
- **ORM models (Week 7 Exercise 7.1):**
  - `SkillDemandWeekly` → `dbo.skill_demand_weekly` — `skill_label`, `esco_uri`, `week_start`, `posting_count`, `employer_count` (distinct employers per skill/week per IMP-021), `computed_at`
  - `ToolDemandWeekly` → `dbo.tool_demand_weekly` — `tool_label`, `week_start`, `posting_count`, `computed_at`
  - `SkillVelocity` → `dbo.skill_velocity` — `skill_label`, `esco_uri`, `week`, `demand_count`, `week_over_week_change`, `four_week_trend`, `trend_confidence` (Python attribute `velocity_week` maps to DB column `week`)
  - `SkillCoOccurrence` → `dbo.skill_co_occurrence` — `skill_a`, `skill_b`, `co_occurrence_count`, `week_start`, `computed_at`
- **Surrogate `id` (SERIAL PK)** on each table — not listed in the runbook checklist but required for consistent ORM/Postgres usage (same pattern as `ExtractedIntelligence`, `EmployerProfile`).
- **Uniqueness + indexes:** Each aggregate table has a `UniqueConstraint` on its natural key (e.g. `skill_label` + `week_start`) plus indexes on `week_start` and label columns for dashboard / refresh queries. `skill_velocity` uses DB column name `week` in constraints.
- **`employer_count`:** Added on `SkillDemandWeekly` to match IMP-021’s `func.count(func.distinct(...))` teaching pattern (Exercise 7.1 checklist focused on `posting_count` only; reading still defines the metric). Default `0` via `server_default`; existing DBs get column via `migrations.py` `ALTER ... ADD COLUMN IF NOT EXISTS`.
- **Table creation:** `run_migrations(get_engine())` → `Base.metadata.create_all` picks up the new models (no separate DDL block in `migrations.py`).

**Steps 2–3 (aggregate refresh):** [agents/analytics/aggregators/demand_weekly.py](../../agents/analytics/aggregators/demand_weekly.py) — `refresh_skill_demand_weekly(session, week_start)` and `refresh_tool_demand_weekly(session, week_start)`.

- **Join path:** `extracted_intelligence` → `normalized_jobs` (`normalized_job_id`) → `job_postings` (`source` + `external_id`) → `companies` (`company_id` text match).
- **Unnest:** `jsonb_array_elements` on `skills` / `tools`; labels via `COALESCE(...->>'skill_name', ...->>'label')` (and tool analog).
- **Spam / reject:** `get_spam_thresholds()` reject bound; exclude `jp.is_spam IS TRUE` and `spam_score > reject_threshold`.
- **Dedup:** rows with `jp.is_duplicate IS TRUE` are excluded from counts.
- **Aggregation:** outer query uses `func.count(func.distinct(...))` + `GROUP BY`; `employer_count` = distinct `company_id` per skill/week.
- **Idempotency:** `DELETE` for `week_start`, then `insert().from_select(...)`; `computed_at` = single UTC timestamp for the batch.
- **Agent wiring:** [agents/analytics/agent.py](../../agents/analytics/agent.py) runs steps **2 → 3 → 8 → 9** (8–9 only if step 2 completes) in `process()`, each in its own `session_scope()`.

**Step 8 (`skill_velocity`):** [agents/analytics/aggregators/velocity.py](../../agents/analytics/aggregators/velocity.py) — `refresh_skill_velocity(session, target_week)`.

- **Input:** Last five `week_start` values from `dbo.skill_demand_weekly` ending at `target_week` (Monday anchor, same contract as step 2 / `date_trunc('week', ...)`).
- **Pipeline (Pandas):** Pivot `posting_count` by `skill_label` × week → sort columns chronologically → **`ROLLING_WINDOW_WEEKS` (4)** rolling mean on transposed frame → `pct_change(axis=1, fill_method=None)`; last column is week-over-week change on the **smoothed** series (not raw single-week spikes).
- **Thresholds:** `ACCELERATING_THRESHOLD = 0.15`, `DECLINING_THRESHOLD = -0.15`, `STABLE_THRESHOLD = 0.05`; `TREND_CONFIDENCE_DEFAULT = 0.8`.
- **Numeric hygiene:** `pct_change` can produce `inf` when the prior rolling mean is zero. **Classification** uses the raw value (`inf` → `accelerating`, `-inf` → `declining`) so growth is never mislabeled as `stable`. **`week_over_week_change`** stored in Postgres is always finite: `NaN` / `inf` / `-inf` → `0.0`.
- **Row fields:** `demand_count` and `esco_uri` come from the **target** week’s demand rows. Bulk insert uses DB column name **`week`** (ORM attribute `velocity_week`).
- **Idempotency:** `DELETE` from `skill_velocity` where `week = target_week`, then `INSERT` one row per skill in the pivot. Empty history still runs `DELETE` and returns `0` inserted.
- **Export:** `from agents.analytics.aggregators import refresh_skill_velocity` (re-exported in `aggregators/__init__.py`). Tests: [agents/tests/test_velocity.py](../../agents/tests/test_velocity.py).

**Step 9 (`skill_co_occurrence`):** [agents/analytics/aggregators/co_occurrence.py](../../agents/analytics/aggregators/co_occurrence.py) — `refresh_skill_co_occurrence(session, week_start)`.

- **Data fetch:** Reuses `_SKILLS_EXPANDED` from `demand_weekly.py` so filters match step 2 exactly (spam, reject threshold, `is_duplicate`, `extraction_failed`, week filter). `SELECT job_posting_id, skill_label` from that subquery; Python groups rows into `list[list[str]]` per posting.
- **Pair counting:** `sorted(set(skills))[:20]` per posting, then `itertools.combinations` with `skill_a, skill_b = sorted((a, b))` (lexicographic `skill_a` < `skill_b`); aggregate counts in a dict; keep **top 200** pairs by **`(-count, skill_a, skill_b)`** so ties match SQL verification (`verify_analytics_aggregates.py` uses `ORDER BY manual_cnt DESC, skill_a COLLATE "C", skill_b COLLATE "C"`).
- **Persistence:** `DELETE` `skill_co_occurrence` where `week_start == target_week`; bulk `INSERT` with one shared `computed_at` (`datetime.now(timezone.utc)`). Empty week: delete only, return `0`.
- **Export:** `from agents.analytics.aggregators import refresh_skill_co_occurrence`. Tests: [agents/tests/test_co_occurrence.py](../../agents/tests/test_co_occurrence.py).

**Package exports:** [agents/analytics/aggregators/__init__.py](../../agents/analytics/aggregators/__init__.py) re-exports `refresh_skill_demand_weekly`, `refresh_tool_demand_weekly`, `refresh_skill_velocity`, `refresh_skill_co_occurrence` (alphabetical in `__all__`).

## Verification Results

**Local run (2026-04-08)** — repo root, venv `agents/.venv`, `.env` with `PYTHON_DATABASE_URL` → `localhost:5432/talent_finder`; aggregates refreshed for Monday **`2026-03-30`** before checks.

### Week 07 runbook — skill demand spot-check (§0 Step 2)

Command from [WEEK07_TESTING_RUNBOOK.md](../../agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md) (top skills by `posting_count`):

```bash
python agents/scripts/db_check.py query "SELECT skill_label, posting_count FROM dbo.skill_demand_weekly ORDER BY posting_count DESC LIMIT 10"
```

**Captured output (2026-04-08):**

```
skill_label     posting_count
------------------------------------------------------------
Cross-functional Collaboration  37
Machine Learning        28
REST APIs       24
Software Engineering    20
Python  16
Code Review     14
Artificial Intelligence 14
Cloud Computing 13
Continuous Integration  13
Software Development    13
```

Also use runbook **§5 Table 1** for `week_start` in the result set:

```bash
python agents/scripts/db_check.py query "SELECT skill_label, posting_count, week_start FROM dbo.skill_demand_weekly ORDER BY posting_count DESC LIMIT 15"
```

**§5 Table 6 (`skill_velocity`) — implementation columns** (runbook snippet is schema-ahead; use this repo’s columns):

```bash
python agents/scripts/db_check.py query "SELECT skill_label, week, demand_count, week_over_week_change, four_week_trend FROM dbo.skill_velocity ORDER BY ABS(week_over_week_change) DESC NULLS LAST LIMIT 10"
```

**§5 Table 7** — co-occurrence sample:

```bash
python agents/scripts/db_check.py query "SELECT skill_a, skill_b, co_occurrence_count FROM dbo.skill_co_occurrence ORDER BY co_occurrence_count DESC LIMIT 10"
```

---

### Schema snapshot and tests (includes 2026-04-04 audit)

1. **Migrations** — `run_migrations(get_engine())` printed `migrations_ok`. Log lines show `migrations_start` → `migrations_tables_created` → … → `migrations_complete`. (`db_engine_created` may appear twice if the engine is initialized more than once in the same process; harmless.)

2. **Column inspection** (`sqlalchemy.inspect` on `dbo.*`) — output:

```
skill_demand_weekly ['id', 'skill_label', 'esco_uri', 'week_start', 'posting_count', 'computed_at', 'employer_count']
tool_demand_weekly ['id', 'tool_label', 'week_start', 'posting_count', 'computed_at']
skill_velocity ['id', 'skill_label', 'esco_uri', 'week', 'demand_count', 'week_over_week_change', 'four_week_trend', 'trend_confidence']
skill_co_occurrence ['id', 'skill_a', 'skill_b', 'co_occurrence_count', 'week_start', 'computed_at']
```

   *Note:* Physical column order in Postgres has `employer_count` after `computed_at` when the column was added via `ALTER`; ORM attribute order in code differs — behavior is unchanged.

3. **Import smoke test** — `from agents.common.data_store.models import SkillDemandWeekly, ToolDemandWeekly, SkillVelocity, SkillCoOccurrence` completed with exit code 0 (no traceback).

4. **Demand refresh tests** — `pytest -c agents/pyproject.toml agents/tests/test_demand_weekly.py -v` (repo root; mocked delete/insert + compile check + optional DB smoke).

5. **Velocity tests** — `pytest -c agents/pyproject.toml agents/tests/test_velocity.py -v` (4-week rolling vs raw spike, classify/sanitize, mocked refresh, optional DB smoke).

6. **Co-occurrence tests** — `pytest -c agents/pyproject.toml agents/tests/test_co_occurrence.py -v` (lexicographic pairs, top-200 cap + deterministic tie-break, mocked refresh, optional DB smoke).

7. **Analytics agent tests** — `pytest -c agents/pyproject.toml agents/tests/test_analytics_agent.py -v` (health states, mocked four `refresh_*`, step 8–9 skip when step 2 fails, target-week helpers). `agents/tests/test_pipeline_runner.py::test_all_pass` may skip when `PYTHON_DATABASE_URL` is set but the server is unreachable.

8. **IMP-021 — step 2 global sum** — [agents/scripts/verify_aggregates.py](../../agents/scripts/verify_aggregates.py): `SUM(posting_count)` on `skill_demand_weekly` vs reconciled sum from `_SKILLS_EXPANDED`. Drift > **0.5%** → exit code 1. **`--list-weeks`** lists Mondays with Step-2-eligible rows. Example: `PYTHONPATH=. python agents/scripts/verify_aggregates.py --week 2026-03-30`.

9. **Issues #176 / #177 — full Pair A cross-check** — [agents/scripts/verify_analytics_aggregates.py](../../agents/scripts/verify_analytics_aggregates.py): steps **2–3** global drift (≤ `--drift-threshold-pct`, default **0.5**) + per-label full-outer-join mismatches; step **8** `demand_count` / `esco_uri` vs `skill_demand_weekly`, orphans; step **9** lex order (`COLLATE "C"`) + top-200 pair count parity vs manual SQL. Examples:

```bash
PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30
PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30 --only skills,tools
PYTHONPATH=. python agents/scripts/verify_analytics_aggregates.py --week 2026-03-30 --only velocity,cooccurrence
```

**Order:** Refresh steps **2 and 3** for `week_start`, then **8 and 9** (velocity reads five weeks of `skill_demand_weekly` ending at that Monday).

## Dependency Notes

Steps **2** (`skill_demand_weekly`) and **3** (`tool_demand_weekly`) are independent of each other.

- **Step 8** reads **`skill_demand_weekly`** (last five `week_start` slices). Run step **2** for the same Monday `week_start` before step 8 or velocity rows will be empty or wrong for `demand_count` / `esco_uri`.
- **Step 9** does **not** query `skill_demand_weekly`; it uses the same **`_SKILLS_EXPANDED`** SQL as step 2 (same postings/skills after spam/dedup filters). Run step **2** before step **9** in the pipeline for **workflow alignment** and dashboard expectations (see `.cursor/rules/skill-tool-demand.mdc`).

**Pair C** (`role_snapshot_weekly`) will consume **`skill_demand_weekly`** — align any future column changes with them before merge.

## Dashboard Design Decisions

Weekly Insights UI still deferred. Aggregate **data** is available for charts: steps 2–3 (`skill_demand_weekly`, `tool_demand_weekly`), step 8 (`skill_velocity`), step 9 (`skill_co_occurrence`). IMP-021 chart mapping is in `.cursor/rules/skill-tool-demand.mdc` (bars / sparkline / heatmap).

## Edge Cases Found

- **`esco_uri`** is nullable so extracted skills without an ESCO link still roll up under `skill_label`.
- **`create_all` does not migrate** existing tables: if an old `skill_demand_weekly` (or similar) existed with different columns, Postgres would not auto-alter; dev fix is manual `ALTER` or drop/recreate in non-prod. Same for **new** unique constraints/indexes on already-created empty tables — `create_all` with `checkfirst=True` may skip altering an existing table; add constraints with raw SQL/Alembic if your DB predates this change.
- **`UniqueConstraint(skill_label, week_start)`** implies at most one aggregate row per skill per week (single `esco_uri` choice in that row if multiple taxonomy links collapse to one label).
- Runbook wording **“enriched_jobs”** maps to enriched rows in **`dbo.job_postings`** in this repo (and related pipeline tables); there is no separate `enriched_jobs` table.
- **Week alignment:** `date_trunc('week', ...)` uses PostgreSQL’s default week boundary (Monday). Refresh must pass that week’s `::date` as `week_start`.
- **Seeded `agent-fixtures`:** Older snapshots may have `extracted_intelligence.skills = []` for all rows — then `--list-weeks` / step 2 are empty until fixtures or live extraction populate skills. **`aggregate_sum_posting_count = 0`** with a large manual sum usually means step 2 refresh was not run for that week after seeding.
- **Co-occurrence vs SQL verifier:** PostgreSQL default collation can disagree with Python `sorted()` for ordering skills and tie-breaking top 200; the verifier uses **`COLLATE "C"`** on skill labels in the manual CTE so results align with the Python aggregator after the deterministic top-200 change in `co_occurrence.py`.
- **`db_check.py query`:** Only **`SELECT`** is allowed; runbook §3 `TRUNCATE` examples via `db_check query` will fail — use `psql`, a one-off admin SQL, or volume reset (see runbook §3) for full resets.

## Cursor Rules Notes

[`.cursor/rules/skill-tool-demand.mdc`](../../.cursor/rules/skill-tool-demand.mdc) is **frozen** with this implementation: section **“Table columns — frozen IMP-021 implementation (Week 7 final)”** matches `models.py` and `aggregators/` (`week_over_week_change`, `demand_count`, `velocity_week` → `week`, `employer_count` = distinct `company_id`, co-occurrence caps and `_SKILLS_EXPANDED` source). When you change schema or refresh behavior, update **this findings doc**, **`skill-tool-demand.mdc`**, and notify Pair C as listed in that rule.

## Data / Evidence

- **Code:** [agents/common/data_store/models.py](../../agents/common/data_store/models.py) (section “Analytics aggregate tables (Week 7 — Pair A)”).
- **Aggregators:** [agents/analytics/aggregators/__init__.py](../../agents/analytics/aggregators/__init__.py), [demand_weekly.py](../../agents/analytics/aggregators/demand_weekly.py), [velocity.py](../../agents/analytics/aggregators/velocity.py), [co_occurrence.py](../../agents/analytics/aggregators/co_occurrence.py); **agent:** [agents/analytics/agent.py](../../agents/analytics/agent.py); tests: [test_demand_weekly.py](../../agents/tests/test_demand_weekly.py), [test_velocity.py](../../agents/tests/test_velocity.py), [test_co_occurrence.py](../../agents/tests/test_co_occurrence.py), [test_analytics_agent.py](../../agents/tests/test_analytics_agent.py).
- **Cursor contract:** [.cursor/rules/skill-tool-demand.mdc](../../.cursor/rules/skill-tool-demand.mdc).
- **Week 7 testing runbook:** [agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md](../../agents/docs/runbooks/WEEK07_TESTING_RUNBOOK.md).
- **Migrations entrypoint:** [agents/common/data_store/migrations.py](../../agents/common/data_store/migrations.py) (`run_migrations` → `Base.metadata.create_all` + `employer_count` alter).
- **Local verification transcript:** see **Verification Results** for captured stdout and commands.

**Manual refresh (example)** — repo root; `load_dotenv(Path('.env'))` so `PYTHON_DATABASE_URL` is set (same pattern as `verify_aggregates.py`):

```bash
PYTHONPATH=. python -c "
from pathlib import Path
from datetime import date
from dotenv import load_dotenv
load_dotenv(Path('.env'))
from agents.common.data_store.database import session_scope
from agents.analytics.aggregators import (
    refresh_skill_co_occurrence,
    refresh_skill_demand_weekly,
    refresh_skill_velocity,
    refresh_tool_demand_weekly,
)
with session_scope() as s:
    ws = date.fromisoformat('2026-03-30')  # Monday week_start
    print('skills', refresh_skill_demand_weekly(s, ws))
    print('tools', refresh_tool_demand_weekly(s, ws))
    print('velocity', refresh_skill_velocity(s, ws))
    print('co_occurrence', refresh_skill_co_occurrence(s, ws))
"
```

**Commands to verify locally** (repo root, venv activated, `PYTHON_DATABASE_URL` in `.env`):

```bash
PYTHONPATH=. python -c "
from dotenv import load_dotenv
load_dotenv()
from agents.common.data_store.database import get_engine
from agents.common.data_store.migrations import run_migrations
run_migrations(get_engine())
print('migrations_ok')
"
```

```bash
PYTHONPATH=. python -c "
from dotenv import load_dotenv
load_dotenv()
from sqlalchemy import inspect
from agents.common.data_store.database import get_engine
insp = inspect(get_engine())
for t in ('skill_demand_weekly','tool_demand_weekly','skill_velocity','skill_co_occurrence'):
    cols = [c['name'] for c in insp.get_columns(t, schema='dbo')]
    print(t, cols)
"
```

Optional psql: `\d dbo.skill_demand_weekly` and `\d dbo.skill_velocity`.

**Import smoke test:**

```bash
PYTHONPATH=. python -c "from agents.common.data_store.models import SkillDemandWeekly, ToolDemandWeekly, SkillVelocity, SkillCoOccurrence"
```
