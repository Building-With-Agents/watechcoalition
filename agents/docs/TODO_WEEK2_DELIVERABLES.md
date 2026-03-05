# Week 2 — TODO: Deliverables & What’s Left

**Source:** [docs/planning/curriculum/week-2-3day-schedule.md](../../docs/planning/curriculum/week-2-3day-schedule.md), [CLAUDE.md](../../CLAUDE.md) (Build Order), [component-diagram-walking-skeleton.html](../../docs/planning/component-diagram-walking-skeleton.html).

**Week 2 deliverable:** LLM adapter + walking skeleton  
**Key outputs:** `llm_adapter.py`, 8 agent stubs, pipeline runner, journey dashboard (Streamlit).  
**Rule:** One real job record travels end-to-end; all agents are stubs (no LLM calls, no DB writes).

---

## Week 2 implementation summary (validated)

All Week 2 **code** deliverables have been implemented and validated:

| Component | Location | Notes |
|-----------|----------|--------|
| LLM adapter | `agents/common/llm_adapter.py` | Provider-agnostic `get_adapter(provider)`, `complete(prompt, schema)` with retry/fallback contract. |
| Demand Analysis stub | `agents/demand_analysis/agent.py` | Explicit stub agent; not in pipeline runner order by design. |
| Orchestration stub | `agents/orchestration/agent.py` | Explicit stub agent for 8-agent completeness. |
| Journey dashboard | `agents/dashboard/streamlit_app.py` | Run controls (incl. skip-health-check), timeline, correlation/event IDs, payload summaries, fixture explorer (Week 2 default + Week 1 staging), load via path or JSON upload. |
| Runner + dashboard wiring | `agents/run_pipeline.py` | `--save-events` option to persist events for dashboard loading. |
| Docs & quick-start | `TODO_WEEK2_DELIVERABLES.md`, `architecture-orientation.md`, repo `README.md` | Week 2 tracking and BaseAgent/AgentEvent pointers. |
| Tests | `agents/tests/test_llm_adapter.py`, `agents/tests/test_week2_stubs.py` | Adapter retries and new stubs (Orchestration, Demand Analysis) covered. |

**Remaining (non-code):** Branch/commit/push workflow and optional Week 2 ADRs if the team selects different technologies.

---

## Post-audit fixes (Week 2)

All 8 audit items have been addressed:

| # | Item | Status | Change |
|---|------|--------|--------|
| 1 | Raw Fixture Explorer vs pipeline input | **Fixed** | Explorer defaults to Week 2 pipeline fixture; can switch to Week 1 staging sample. (`streamlit_app.py`) |
| 2 | Duplicate config (module vs package) | **Fixed** | Removed legacy `agents/common/config.py`; package config is single source. |
| 3 | test_week2_stubs contract alignment | **Fixed** | Stubs now assert BaseAgent, `to_dict()`, and `to_audit_dict()` for both Orchestration and Demand Analysis. (`test_week2_stubs.py`) |
| 4 | llm_audit_log persistence | **Not fixed (intentional)** | Week 2 contract is “no DB writes”; `llm_audit_log` deferred. Explicit scope note added in `llm_adapter.py` docstring. |
| 5 | health_check test dict order | **Fixed** | Assertions use set-based checks instead of dict insertion order. (`test_pipeline_contract.py`) |
| 6 | Dashboard skip-health-check | **Fixed** | Run controls include skip-health-check toggle. (`streamlit_app.py`) |
| 7 | Runner docstring path | **Fixed** | Docstring states “run from repository root” and clarifies `--save-events` path resolution. (`run_pipeline.py`) |
| 8 | Load Saved Journey = fixed path only | **Fixed** | “Load Saved Journey” supports path input and JSON upload, not only the fixed cache path. (`streamlit_app.py`) |

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Done (implemented or completed) |
| ⬜ | Not done — to do |
| 🔄 | Partially done or needs confirmation |

---

## 1. Process & Git (non-code)

| Task | Status | Notes |
|------|--------|--------|
| Create Week 2 branch from `main`, push for backup | ⬜ | `git checkout main && git pull && git checkout -b <name>-week-2-<description>` |
| Follow branch naming: `<your-name>-week-2-<description>` | ⬜ | See [branch-strategy.md](../../docs/branch-strategy.md) |
| Do **not** open a PR to `main`; push branch for backup/review | ⬜ | Leads merge chosen work into `staging` |
| Commit & push at end of Day 1 (llm_adapter + AgentEvent) | ⬜ | — |
| Commit & push at end of Day 2 (8 stubs + pipeline runner) | ⬜ | — |
| Final commit & push at end of Day 3 (journey dashboard + wiring) | ⬜ | — |

---

## 2. Day 1 — LLM adapter & event envelope

| Task | Status | Notes |
|------|--------|--------|
| Implement `agents/common/llm_adapter.py` | ✅ | Added `get_adapter(provider)` with provider-agnostic adapters (`azure_openai`, `openai`, `anthropic`), `complete(prompt, schema)` contract, 2 retries with structured failure logging, graceful `None` fallback. |
| Add or align `AgentEvent` in `common/events/` | ✅ | Present in `agents/common/events/base.py`: `event_id`, `correlation_id`, `agent_id`, `timestamp`, `schema_version`, `payload`; `create_event()`, `to_dict()`. |

---

## 3. Day 2 — Eight agent stubs + pipeline runner

| Task | Status | Notes |
|------|--------|--------|
| Ingestion Agent stub | ✅ | Reads fixture, wraps one record in event. |
| Normalization Agent stub | ✅ | Pass-through / stub payload. |
| Skills Extraction Agent stub | ✅ | Returns fixture payload (e.g. `fixture_skills_extracted.json`), no LLM. |
| Enrichment Agent stub | ✅ | Returns fixture payload (e.g. `fixture_enriched.json`), no LLM. |
| Analytics Agent stub | ✅ | Returns fixture payload (e.g. `fixture_analytics_refreshed.json`), no LLM. |
| Visualization Agent stub | ✅ | Emits final event (e.g. `status: "complete"`). |
| Orchestration Agent stub | ✅ | Added `agents/orchestration/agent.py` stub. Runner remains the Week 2 sequential execution path; orchestration module now exists explicitly for 8-agent completeness. |
| Demand Analysis Agent stub | ✅ | Added `agents/demand_analysis/agent.py` stub (consume event → emit stub `AgentEvent` payload). Not added to Week 2 runner order by design. |
| Use fixture data for one job end-to-end | ✅ | `fallback_scrape_sample.json` → stubs; `fixture_skills_extracted.json`, `fixture_enriched.json`, `fixture_analytics_refreshed.json` where stubs stand in for LLM. |
| Pipeline runner: run stub chain (Ingestion → … → Visualization), one `correlation_id` | ✅ | `agents/common/pipeline/runner.py` + `agents/run_pipeline.py`. |
| Runner in-process, no DB | ✅ | Events only. |

---

## 4. Day 3 — Journey dashboard + wiring

| Task | Status | Notes |
|------|--------|--------|
| **Journey dashboard** in Streamlit | ✅ | Replaced dashboard with Journey view: run controls, event timeline, event IDs, `correlation_id`, payload summaries, and saved-event loading. No DB required. |
| Wire pipeline runner as launchable entrypoint | ✅ | `python -m agents.run_pipeline` (and `--health`, `--save-events` for dashboard). |
| One real record runs end-to-end and is visible somewhere | ✅ | End-to-end run emits events and Journey dashboard renders the run timeline and payloads. |
| Self-check: `llm_adapter.py` present and callable | ✅ | `agents/common/llm_adapter.py` added; adapter selection and `complete(...)` callable contract implemented. |
| Self-check: 8 stubs; one run end-to-end; dashboard shows the journey | ✅ | Ingestion/Normalization/Skills/Enrichment/Analytics/Visualization + Orchestration + Demand Analysis stubs present; runner and Journey dashboard wired. |

---

## 5. Documentation & decisions (non-code or light code)

| Task | Status | Notes |
|------|--------|--------|
| Week 2 ADRs (if team chooses different tech) | ⬜ | **Docs/decisions** — CLAUDE: “If your team’s Week 2 ADRs select different technologies, adapt the implementation.” ARCHITECTURAL_DECISIONS: SA decisions (e.g. #11 LLM provider, #13 framework, #14 message bus) must converge before the agent that depends on them. Document or confirm any Week 2-relevant ADRs. |
| Update or add doc pointers for “which base/event to use” | ✅ | README and orientation docs now point to BaseAgent + AgentEvent contracts and Week 2 journey flow. |
| Ensure `.env` / README mention `LLM_PROVIDER`, Azure OpenAI vars | ✅ | `.env.example` already contains required vars; README now references LLM provider configuration. |

---

## 6. Summary checklist (quick pass)

| Deliverable | Done? |
|-------------|--------|
| `llm_adapter.py` with get_adapter + complete + retries | ✅ |
| AgentEvent (event envelope) | ✅ |
| 6 pipeline agent stubs (Ingestion → Visualization) | ✅ |
| Orchestration stub or runner-as-orchestration clarified | ✅ |
| Demand Analysis stub (stub only) | ✅ |
| Pipeline runner (one correlation_id, in-process) | ✅ |
| Fixtures used for one job end-to-end | ✅ |
| Entrypoint `python -m agents.run_pipeline` | ✅ |
| **Journey dashboard** (one screen, one job, events + correlation_id) | ✅ |
| Branch/commit/push and no-PR-to-main workflow | ⬜ |
| ADR / env docs as needed | ✅ |
| Tests for adapter + Week 2 stubs | ✅ | `test_llm_adapter.py`, `test_week2_stubs.py`. |

---

## References

- **Week 2 schedule:** [docs/planning/curriculum/week-2-3day-schedule.md](../../docs/planning/curriculum/week-2-3day-schedule.md)
- **Build order:** [CLAUDE.md](../../CLAUDE.md) — Week 2 row
- **LLM adapter & event envelope:** [docs/planning/ARCHITECTURE_DEEP.md](../../docs/planning/ARCHITECTURE_DEEP.md)
- **Walking skeleton diagram:** [docs/planning/component-diagram-walking-skeleton.html](../../docs/planning/component-diagram-walking-skeleton.html)
- **Branch/PR rules:** [docs/branch-strategy.md](../../docs/branch-strategy.md)
