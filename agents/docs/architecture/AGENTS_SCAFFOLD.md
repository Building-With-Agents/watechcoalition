# Agents Directory Scaffold

This document describes the initial scaffold of the `agents/` directory for the Job Intelligence Engine. The structure conforms to the canonical layout in [CLAUDE.md](../../../CLAUDE.md) and [docs/planning/ARCHITECTURE_DEEP.md](../../../docs/planning/ARCHITECTURE_DEEP.md).

---

## Source of truth

- **Canonical structure:** [CLAUDE.md](../../../CLAUDE.md) (Repository Structure section)
- **Implementation spec:** [docs/planning/ARCHITECTURE_DEEP.md](../../../docs/planning/ARCHITECTURE_DEEP.md)

---

## What was created

### 1. Directory tree

All directories from the canonical scaffold were created:

| Path | Purpose |
|------|--------|
| `ingestion/`, `ingestion/sources/`, `ingestion/tests/` | Ingestion agent |
| `normalization/`, `normalization/schema/`, `normalization/field_mappers/`, `normalization/tests/` | Normalization agent |
| `skills_extraction/`, `skills_extraction/models/`, `skills_extraction/taxonomy/`, `skills_extraction/tests/` | Skills extraction agent |
| `enrichment/`, `enrichment/classifiers/`, `enrichment/resolvers/`, `enrichment/tests/` | Enrichment (resolvers = Phase 2) |
| `analytics/`, `analytics/aggregators/`, `analytics/query_engine/`, `analytics/tests/` | Analytics agent |
| `visualization/`, `visualization/renderers/`, `visualization/exporters/`, `visualization/tests/` | Visualization agent |
| `orchestration/`, `orchestration/scheduler/`, `orchestration/circuit_breaker/`, `orchestration/saga/`, `orchestration/admin_api/`, `orchestration/tests/` | Orchestration (last three = Phase 2) |
| `demand_analysis/`, `demand_analysis/time_series/`, `demand_analysis/forecasting/`, `demand_analysis/tests/` | Phase 2 scaffold only |
| `common/`, `common/events/`, `common/message_bus/`, `common/data_store/`, `common/config/`, `common/observability/`, `common/errors/` | Shared code |
| `dashboard/` | Streamlit app |
| `platform/`, `platform/infrastructure/`, `platform/ci_cd/`, `platform/monitoring/`, `platform/runbooks/` | Phase 2 scaffold |
| `data/`, `data/staging/`, `data/normalized/`, `data/enriched/`, `data/analytics/`, `data/demand_signals/`, `data/rendered/`, `data/dead_letter/` | Data directories (no Python packages) |
| `eval/` | Eval dataset (30–50 hand-labeled records) |
| `docs/`, `docs/architecture/`, `docs/api/`, `docs/adr/` | Documentation |
| `tests/` | Root integration tests |

### 2. `__init__.py` placement

An empty `__init__.py` was added in every directory that is a Python package so that `agents.ingestion`, `agents.common.events`, and all subpackages are importable.

**No `__init__.py`** was added under:

- `agents/data/` and all `data/*` subdirs (data only)
- `agents/eval/` (data only)
- `agents/docs/` and all `docs/*` subdirs (docs only)

### 3. Named stub modules

Minimal placeholder files were added only where the scaffold names a specific file:

| File | Content |
|------|--------|
| `ingestion/agent.py` | Stub with `health_check()` returning status/agent/last_run/metrics |
| `ingestion/sources/jsearch_adapter.py` | Docstring only |
| `ingestion/sources/scraper_adapter.py` | Docstring only |
| `ingestion/deduplicator.py` | Docstring only |
| `normalization/agent.py` | Stub with `health_check()` |
| `skills_extraction/agent.py` | Stub with `health_check()` |
| `enrichment/agent.py` | Stub with `health_check()` |
| `analytics/agent.py` | Stub with `health_check()` |
| `visualization/agent.py` | Stub with `health_check()` |
| `orchestration/agent.py` | Stub with `health_check()` |
| `demand_analysis/agent.py` | Stub with `health_check()` (Phase 2 scaffold) |
| `common/llm_adapter.py` | `get_adapter(provider)` placeholder returning `None` |
| `dashboard/streamlit_app.py` | Minimal Streamlit app (title + caption) so `streamlit run` works |

Every agent stub exposes a `health_check()`-style contract as required by the architecture.

### 4. Persistence of empty directories

Leaf directories under `data/`, `eval/`, and `docs/` that would otherwise be untracked by git were given a `.gitkeep` file so the structure is committed.

---

## Phase 1 vs Phase 2

- **Phase 1 areas** have the full scaffold: directories, `__init__.py`, and the named stub files above. No implementation logic was added; these are placeholders for the 12-week build.
- **Phase 2 empty scaffolds** contain only `__init__.py` (and, for `demand_analysis/`, the stub `agent.py`). No other implementation files were added in:
  - `orchestration/circuit_breaker/`
  - `orchestration/saga/`
  - `orchestration/admin_api/`
  - `enrichment/resolvers/`
  - `demand_analysis/time_series/`, `demand_analysis/forecasting/`
  - `platform/infrastructure/`, `platform/ci_cd/`, `platform/monitoring/`, `platform/runbooks/`
  - `data/demand_signals/` (data directory; `.gitkeep` only)

---

## Conformance

As of the scaffold implementation, the tree under `agents/` matches the canonical structure in CLAUDE.md and ARCHITECTURE_DEEP.md:

- All listed directories exist.
- All listed named files exist as stubs.
- Phase 2 directories are empty scaffolds only.
- The package is importable from the repo root (e.g. `import agents`, `import agents.ingestion`, `import agents.common.events`).
- Test packages are importable (e.g. `agents.tests`, `agents.ingestion.tests`).

To verify from repo root:

```bash
python -c "import agents; import agents.ingestion; import agents.common.events; print('OK')"
```

To run the minimal dashboard:

```bash
streamlit run agents/dashboard/streamlit_app.py
```

**Python environment:** Use a virtualenv inside `agents/` and activate it from the project root (e.g. `source agents/.venv/bin/activate`). See [agents/README.md](agents/README.md).

**Database connectivity:** Agents use `agents/.env` with `DATABASE_URL` in **`mssql+pyodbc://`** format (not `sqlserver://`). Verify with `python -m agents.connectivity_test` (expect: `job_postings row count: <N>`). Next.js uses the root `.env` and Prisma; both environments coexist in the same repo.
