# Week 7 — Skill & tool demand (Pair A) — findings

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

## Verification Results

**Local run (2026-04-04)** — repo root, venv `.venv`, `PYTHONPATH=.`, `PYTHON_DATABASE_URL` → `localhost:5432/talent_finder`.

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

## Dependency Notes

Steps **2** (`skill_demand_weekly`) and **3** (`tool_demand_weekly`) are independent of each other. Steps **8** (`skill_velocity`) and **9** (`skill_co_occurrence`) depend on step **2** completing for the same refresh window so velocity and co-occurrence are not computed against empty or stale demand snapshots. **Pair C** (`role_snapshot_weekly`) will consume **`skill_demand_weekly`** — align any future column changes with them before merge.

## Dashboard Design Decisions

Deferred to the Weekly Insights Streamlit task; this exercise is schema-only (no dashboard changes).

## Edge Cases Found

- **`esco_uri`** is nullable so extracted skills without an ESCO link still roll up under `skill_label`.
- **`create_all` does not migrate** existing tables: if an old `skill_demand_weekly` (or similar) existed with different columns, Postgres would not auto-alter; dev fix is manual `ALTER` or drop/recreate in non-prod. Same for **new** unique constraints/indexes on already-created empty tables — `create_all` with `checkfirst=True` may skip altering an existing table; add constraints with raw SQL/Alembic if your DB predates this change.
- **`UniqueConstraint(skill_label, week_start)`** implies at most one aggregate row per skill per week (single `esco_uri` choice in that row if multiple taxonomy links collapse to one label).
- Runbook wording **“enriched_jobs”** maps to enriched rows in **`dbo.job_postings`** in this repo (and related pipeline tables); there is no separate `enriched_jobs` table.

## Cursor Rules Notes

[`.cursor/rules/skill-tool-demand.mdc`](../../.cursor/rules/skill-tool-demand.mdc) still reflects earlier IMP-021 / ARCHITECTURE_DEEP shapes (e.g. `growth_rate`, `trend` enum). This runbook slice uses **`esco_uri`**, **`four_week_trend`**, **`co_occurrence_count`**, and DB column **`week`** on `skill_velocity`. Update that rule in a later task once the aggregate schema is frozen across pairs.

## Data / Evidence

- **Code:** [agents/common/data_store/models.py](../../agents/common/data_store/models.py) (section “Analytics aggregate tables (Week 7 — Pair A)”).
- **Migrations entrypoint:** [agents/common/data_store/migrations.py](../../agents/common/data_store/migrations.py) (`run_migrations` → `Base.metadata.create_all` + `employer_count` alter).
- **Local verification transcript:** same machine as above; see **Verification Results** for captured stdout.

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
