# Week 6 — Adapter findings (IMP-020)

## What I tested

- SQLAlchemy `SOCC` model in `agents/common/data_store/models.py` (`dbo.socc`): `session.execute(select(SOCC).limit(5))` returns rows when the database is available and migrated. Pair B can `from agents.common.data_store.models import SOCC` and query with a scoped session.
- Phase 1 mocks: `MockBLSAdapter.get_wage_data(soc, region)`, `MockONETAdapter.get_occupation_details` / `get_soc_crosswalk`, `MockCensusAdapter.get_regional_demographics` — async contracts, Pydantic return types (`WageEstimate`, `OccupationProfile`, `RegionalProfile`, `SOCMatch`).
- `ExternalEnrichmentFacade.fetch_for_posting` merges adapter outputs into enrichment dicts as JSON-serializable `model_dump()` payloads.

## What I found

- **Unknown SOC (BLS):** returns `None` (no wage row). Callers should treat missing wages as “no OEWS mock coverage,” not as hard failure.
- **O\*NET crosswalk:** title-keyword heuristics return ranked `SOCMatch` entries; when SOC is missing on the posting, the facade can resolve occupation via crosswalk + `get_occupation_details`.
- **Census:** empty `region` string returns `None`; non-empty unknown labels fall back to a generic Borderplex aggregate profile.
- **Sync pipeline:** `EnrichmentAgent.process` is synchronous; adapters are async and are invoked via `asyncio.run` in `run_coroutine` when no event loop is running. Nested loop contexts will raise `RuntimeError` (logged, enrichment continues without external payloads).

## Recommendation

- Keep **abstract bases** (`AbstractBLSAdapter`, `AbstractONETAdapter`, `AbstractCensusAdapter`) as the stable contract; Phase 2 adds `Live*` implementations with `httpx` and the same method signatures.
- Preserve **Pydantic models** as the public return shapes so Phase 2 only changes adapter internals.

## Tradeoffs acknowledged

- **Per-record `asyncio.run`:** simple for Phase 1; higher overhead than a shared async batch. Acceptable until the agent moves to async execution.
- **Mock wage table:** only three SOCs — realistic for demos, not exhaustive.
- **`job_record` as dict** on `EnrichedJobProfile`: avoids forcing full `JobRecord` construction from SkillsExtracted rows; aligns with pipeline reality.

## Data / evidence

- El Paso–style OEWS medians (USD, annual) in mocks: 15-1252 → 95,340; 15-1211 → 85,620; 15-1299 → 78,900 (runbook Week 6 table).
- Borderplex Census mocks use plausible population / income / education percentages for `el_paso`, `juarez_proxy`, and aggregate `borderplex`.
