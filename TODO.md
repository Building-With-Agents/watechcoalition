# TODO — Parallelize Skills Extraction LLM Calls (#166)

> **Branch:** `feat/parallel-skills-extraction`
> **Base:** `development`
> **Goal:** Reduce 568-job extraction from 3–6 hours to under 1 hour via intra-job + inter-job concurrency.

---

## Current Architecture (Serial)

```
for each job (sequential, with time.sleep between):
    extract_tools(job)          # Pass 1 — regex, 0 LLM tokens
    extract_context(job)        # Pass 1 — regex, 0 LLM tokens
    extract_tasks(job)          # Pass 2 — LLM ~8-15s
    extract_responsibilities()  # Pass 2 — LLM ~8-15s
    extract_skills_no_taxonomy()# Pass 2 — LLM ~5-10s
    # total per job: ~20-40s sequential

# then batch taxonomy once
resolve_taxonomy_batch(all_labels)

# then batch DB write
store.save(results)
```

**Throttling constants (designed for 3 RPM, now have 190 RPM):**
- `_CHUNK_SIZE = 5` — process 5 jobs then pause
- `_CHUNK_COOLDOWN = 30s` — pause between chunks
- `_INTER_LLM_DELAY = 1s` — pause between every job

**Key files involved:**
- `agents/skills_extraction/agent.py` — main loop (lines 426-448), `_extract_work_item_no_taxonomy` (lines 488-615)
- `agents/common/llm_client.py` — `invoke_structured_extraction_llm()` (sync, uses `chain.invoke()`)
- `agents/skills_extraction/extractors/tasks.py` — `extract_tasks()` (sync)
- `agents/skills_extraction/extractors/responsibilities.py` — `extract_responsibilities()` (sync)
- `agents/skills_extraction/extractors/skills.py` — `extract_skills_no_taxonomy()` (sync, has 429 backoff)
- `agents/common/data_store/database.py` — `session_scope()` (singleton sessionmaker, not thread-safe for concurrent use)

---

## Target Architecture (Parallel)

```
semaphore = asyncio.Semaphore(SKILLS_EXTRACTION_CONCURRENCY)  # default 5

async def extract_one_job(item, semaphore):
    async with semaphore:
        tools = extract_tools(job)        # sync, fast regex — no change needed
        context = extract_context(job)    # sync, fast regex — no change needed
        tasks, resp, skills = await asyncio.gather(
            extract_tasks_async(job, context),
            extract_responsibilities_async(job, context),
            extract_skills_no_taxonomy_async(job, tools),
        )
        return (item, tools, skills, combined_meta)

# All jobs concurrently (bounded by semaphore)
pending = await asyncio.gather(*[extract_one_job(item, sem) for item in work_items])

# Taxonomy + DB write unchanged
resolve_taxonomy_batch(all_labels)
store.save(results)
```

---

## Work Breakdown

### Phase A: Async LLM Infrastructure (no behavior change yet)

#### A1. Add `ainvoke_structured_extraction_llm` to `agents/common/llm_client.py`
- [ ] Create async counterpart of `invoke_structured_extraction_llm` (line 234)
- [ ] Use `AzureChatOpenAI` with `chain.ainvoke(prompt)` instead of `chain.invoke(prompt)`
- [ ] Same audit logging: `log_extraction_event()` call, token counting, cost computation
- [ ] Same error handling shape: return `(parsed | None, metadata_dict)`, never raise
- [ ] Same 429 detection: `is_rate_limit`, `retry_after_seconds` in metadata
- [ ] Reuse `_resolve_azure_deployment()`, `_model_tier_for_skills_extraction()`, `compute_extraction_cost()` — these are pure functions, no async needed
- [ ] Keep sync `invoke_structured_extraction_llm` intact (no regression for callers outside skills extraction)

**Implementation notes:**
- `AzureChatOpenAI` from `langchain_openai` supports `ainvoke()` natively via `httpx.AsyncClient` under the hood
- `with_structured_output()` returns a chain that also supports `ainvoke()`
- The `include_raw=True` kwarg should work identically with `ainvoke`
- Test with a simple mock: patch `AzureChatOpenAI` and verify `ainvoke` is called

**File:** `agents/common/llm_client.py`
**Tests:** `agents/common/tests/test_llm_client_async.py` (new file)

---

#### A2. Add async extractor wrappers in each extractor module
Three files, same pattern for each:

##### A2a. `agents/skills_extraction/extractors/tasks.py` — add `extract_tasks_async`
- [ ] Create `async def extract_tasks_async(job_record, pass1_context=None) -> tuple[list[TaskRecord], dict]`
- [ ] Same prompt building (`_build_tasks_prompt` is pure, no change needed)
- [ ] Call `ainvoke_structured_extraction_llm` instead of `invoke_structured_extraction_llm`
- [ ] Same error handling: try/except returns `([], metadata)` with `extraction_failed=True`
- [ ] Same metadata shape as sync version
- [ ] Keep sync `extract_tasks` untouched for backward compatibility

**Tests:** `agents/skills_extraction/tests/test_async_extractors.py` (new file)

##### A2b. `agents/skills_extraction/extractors/responsibilities.py` — add `extract_responsibilities_async`
- [ ] Same pattern as A2a, using `_build_responsibilities_prompt` + `ainvoke_structured_extraction_llm`
- [ ] Deployment keys: `_RESP_DEPLOYMENT_KEYS`
- [ ] Model tier: `"sonnet"`

##### A2c. `agents/skills_extraction/extractors/skills.py` — add `extract_skills_no_taxonomy_async`
- [ ] Same prompt building via `build_skills_prompt`
- [ ] **Critical:** Port the 429 backoff loop to async: replace `time.sleep()` with `await asyncio.sleep()`
- [ ] Port the timeout retry loop to async
- [ ] Keep `RATE_LIMIT_BACKOFF_SECS`, `RATE_LIMIT_MAX_CYCLES` constants
- [ ] Keep `_llm_skill_to_record`, `_skill_confidence_threshold` helpers (pure functions)
- [ ] Same confidence threshold filtering
- [ ] No taxonomy resolution (matches existing `extract_skills_no_taxonomy` behavior)

**This is the most complex of the three** because of the retry/backoff logic.

##### A2d. Update `agents/skills_extraction/extractors/__init__.py`
- [ ] Export `extract_tasks_async`, `extract_responsibilities_async`, `extract_skills_no_taxonomy_async`

---

### Phase B: Intra-Job Parallelism (Level 1)

#### B1. Refactor `_extract_work_item_no_taxonomy` to async
- [ ] Rename or create `async def _extract_work_item_no_taxonomy_async(self, item)` in `agent.py`
- [ ] Keep Pass 1 sync (tools + context are regex, instant)
- [ ] Replace sequential LLM calls (lines 541-545) with `asyncio.gather`:
  ```python
  tasks_result, resp_result, skills_result = await asyncio.gather(
      extract_tasks_async(job, pass1_context=context_signals),
      extract_responsibilities_async(job, pass1_context=context_signals),
      extract_skills_no_taxonomy_async(job, pass1_tools=tools),
      return_exceptions=True,  # prevent one failure from cancelling others
  )
  ```
- [ ] Handle `return_exceptions=True`: if any result is an Exception, treat it as failed extraction for that dimension — build appropriate metadata
- [ ] Metadata aggregation unchanged: sum tokens, cost, latency; status = failed/degraded/success based on dimension results
- [ ] `latency_ms` should now reflect wall-clock time (max of three) not sum — update `total_latency` computation to use wall-clock measurement instead
- [ ] Keep sync `_extract_work_item_no_taxonomy` as fallback (controlled by env flag `SKILLS_EXTRACTION_PARALLEL=1|0`)

**File:** `agents/skills_extraction/agent.py`
**Tests:** Update `test_extraction_integration.py` with async-aware mocks

---

### Phase C: Inter-Job Parallelism (Level 2)

#### C1. Replace serial loop with semaphore-bounded `asyncio.gather`
- [ ] Add env var `SKILLS_EXTRACTION_CONCURRENCY` (default: `5`)
- [ ] Create `asyncio.Semaphore(concurrency)` at the start of `process()`
- [ ] Replace the `for idx, item in enumerate(work_items)` loop (lines 431-448) with:
  ```python
  semaphore = asyncio.Semaphore(concurrency)

  async def _extract_one(item):
      async with semaphore:
          return (item, *await self._extract_work_item_no_taxonomy_async(item))

  pending = await asyncio.gather(*[_extract_one(item) for item in work_items])
  ```
- [ ] Remove `_INTER_LLM_DELAY` sleep — replaced by semaphore backpressure
- [ ] Remove `_CHUNK_SIZE` / `_CHUNK_COOLDOWN` logic — replaced by semaphore
- [ ] Keep the old constants loadable from env but mark them as **deprecated** in comments (backward compat if someone still sets them and `SKILLS_EXTRACTION_PARALLEL=0`)
- [ ] Items with no normalized text (empty descriptions) should still be handled synchronously inside the async wrapper — they return immediately without LLM calls

**Concurrency math:**
- 190 RPM limit / 3 LLM calls per job = ~63 jobs/min max
- With concurrency=5: 5 jobs × 3 calls = 15 concurrent requests; each job ~10-15s → ~20-30 jobs/min → ~57-90 RPM (safely under 190)
- Make configurable so users can tune: `SKILLS_EXTRACTION_CONCURRENCY=3` for conservative, `=8` for aggressive

**File:** `agents/skills_extraction/agent.py`

---

#### C2. Make `process()` async-aware (sync entrypoint preserved)
- [ ] The public `process(event)` method must remain synchronous (caller contract: `run_processing_loop.py` calls `extract_agent.process(event)` synchronously)
- [ ] Inside `process()`, use `asyncio.run()` (or detect existing loop) to run the async extraction pipeline
- [ ] Pattern:
  ```python
  def process(self, event):
      # ... load work_items, validate ...
      if _parallel_enabled():
          pending = asyncio.run(self._extract_batch_parallel(work_items))
      else:
          pending = self._extract_batch_serial(work_items)  # current code, unchanged
      # ... taxonomy, save, return event ...
  ```
- [ ] Handle edge case: if already inside an event loop (e.g., Jupyter notebook, Streamlit), use `asyncio.get_event_loop().run_until_complete()` or `nest_asyncio`
- [ ] Extract the serial loop into `_extract_batch_serial(work_items) -> list[tuple]` for clean fallback

**File:** `agents/skills_extraction/agent.py`

---

### Phase D: DB Write Safety

#### D1. Verify `session_scope` thread safety for the parallel path
- [ ] Current `session_scope()` in `database.py` uses a singleton `sessionmaker` with `pool_size=5`
- [ ] **DB writes happen AFTER all extraction is complete** (line 478: `self._extraction_store.save(results)`) — so concurrent extraction does NOT touch the DB
- [ ] Confirm: `log_extraction_event()` in `llm_adapter.py` writes to `llm_audit_log` — check if this happens during LLM calls (it does, inside `invoke_structured_extraction_llm`)
- [ ] **Action needed:** `log_extraction_event()` calls `session_scope()` during LLM calls — with concurrent LLM calls, multiple sessions may write to `llm_audit_log` simultaneously
- [ ] Fix: Use `scoped_session` or create per-task sessions for audit logging, OR batch audit logs and write them after extraction, OR use a thread-safe queue for audit writes
- [ ] Recommended approach: **queue audit log entries in-memory during extraction, flush to DB in a single batch after all LLM calls complete** — simplest, no session contention, preserves audit completeness
- [ ] Alternative: `log_extraction_event` already creates its own session per call — verify that SQLAlchemy's connection pool handles concurrent `session_scope()` calls correctly with `pool_size >= SKILLS_EXTRACTION_CONCURRENCY`

**Files:** `agents/common/llm_adapter.py`, `agents/common/data_store/database.py`
**Tests:** Concurrent write test with multiple threads/tasks

---

#### D2. Ensure `SQLAlchemyExtractionStore.save()` remains single-threaded
- [ ] Verify `save()` is only called once, after all `pending` results are collected (line 478)
- [ ] No change needed if extraction results are collected into a list first, then saved
- [ ] Add an assertion or guard: if `save()` is accidentally called concurrently, log an error

**File:** `agents/skills_extraction/agent.py` (lines 287-355)

---

### Phase E: Configuration & Observability

#### E1. New environment variables
- [ ] `SKILLS_EXTRACTION_CONCURRENCY` — int, default `5`. Max concurrent jobs in flight.
- [ ] `SKILLS_EXTRACTION_PARALLEL` — bool, default `1`. Set to `0` to fall back to serial mode.
- [ ] Document in `.env.example` and `CLAUDE.md`

#### E2. Structured logging for parallel execution
- [ ] Log at batch start: `skills_extraction_parallel_start`, concurrency level, total jobs, parallel enabled/disabled
- [ ] Log per-job completion: `skills_extraction_job_complete`, job_id, wall_clock_ms, dimensions_succeeded
- [ ] Log batch summary: `skills_extraction_batch_complete`, total_wall_clock_ms, total_llm_calls, avg_per_job_ms, concurrency_utilization (jobs_completed / time / concurrency)
- [ ] Log when semaphore is saturated (all slots occupied) — optional, for tuning
- [ ] Deprecation warnings if `_CHUNK_SIZE`, `_CHUNK_COOLDOWN`, or `_INTER_LLM_DELAY` env vars are set while parallel mode is active

#### E3. Metrics for processing loop
- [ ] `run_processing_loop.py` already logs `iteration_complete` — ensure extraction time is captured
- [ ] Add wall-clock timing around `extract_agent.process(extract_event)` call
- [ ] Compare serial vs parallel in logs for validation

---

### Phase F: Testing

#### F1. Unit tests for async LLM client
- [ ] Test `ainvoke_structured_extraction_llm` with mocked `AzureChatOpenAI.ainvoke`
- [ ] Test error paths: timeout, 429 rate limit, empty response, import error
- [ ] Test token counting and cost computation match sync version
- [ ] Test metadata shape matches sync version exactly

**File:** `agents/common/tests/test_llm_client_async.py`

#### F2. Unit tests for async extractors
- [ ] Test `extract_tasks_async` returns same shape as `extract_tasks` with mocked LLM
- [ ] Test `extract_responsibilities_async` returns same shape as `extract_responsibilities`
- [ ] Test `extract_skills_no_taxonomy_async` returns same shape, including 429 backoff behavior
- [ ] Test that a failed dimension returns `([], metadata)` without raising

**File:** `agents/skills_extraction/tests/test_async_extractors.py`

#### F3. Unit tests for parallel batch extraction
- [ ] Test `_extract_batch_parallel` with 3-5 mocked jobs — verify all run concurrently
- [ ] Test semaphore limits: set concurrency=2, submit 5 jobs, verify max 2 in flight at once
- [ ] Test that one job's LLM failure doesn't block or corrupt other jobs' results
- [ ] Test that one dimension's failure (e.g., tasks 429) doesn't block other dimensions for the same job
- [ ] Test empty-description jobs are handled correctly in parallel batch (no LLM calls, immediate return)
- [ ] Test that results list matches serial output for same input (ordering may differ — sort by job_id for comparison)

**File:** `agents/skills_extraction/tests/test_parallel_extraction.py`

#### F4. Integration test — parallel vs serial equivalence
- [ ] Run same batch of 5-10 mock jobs through both serial and parallel paths
- [ ] Compare: same number of results, same extraction statuses, same skills per job
- [ ] Verify event payload shape is identical (`SkillsExtracted` event)
- [ ] Verify `_build_payload` and `_build_extraction_result` work correctly with parallel-gathered results

**File:** `agents/skills_extraction/tests/test_extraction_integration.py` (extend existing)

#### F5. Test fallback to serial mode
- [ ] Set `SKILLS_EXTRACTION_PARALLEL=0`, verify serial path runs
- [ ] Verify `_CHUNK_SIZE`, `_CHUNK_COOLDOWN`, `_INTER_LLM_DELAY` are respected in serial mode
- [ ] Verify parallel env vars (`SKILLS_EXTRACTION_CONCURRENCY`) are ignored in serial mode

---

### Phase G: Documentation & Cleanup

#### G1. Update `CLAUDE.md`
- [ ] Add `SKILLS_EXTRACTION_CONCURRENCY` and `SKILLS_EXTRACTION_PARALLEL` to env vars section
- [ ] Update Skills Extraction Agent description to mention parallel extraction
- [ ] Note deprecation of `_CHUNK_SIZE`, `_CHUNK_COOLDOWN`, `_INTER_LLM_DELAY` in parallel mode

#### G2. Update `agents/skills_extraction/agent.py` module docstring
- [ ] Describe parallel execution model
- [ ] Document concurrency limits and how to tune

#### G3. Mark deprecated constants
- [ ] `_CHUNK_SIZE`, `_CHUNK_COOLDOWN`, `_INTER_LLM_DELAY` — add deprecation comment, note they only apply in serial fallback mode

#### G4. Close issue #166
- [ ] Verify all acceptance criteria met (checklist below)
- [ ] PR description with benchmark results

---

## Acceptance Criteria Checklist

- [ ] Tasks, responsibilities, and skills extraction run concurrently for each job (intra-job parallelism) — **Phase B**
- [ ] Multiple jobs processed concurrently with configurable concurrency limit (inter-job parallelism) — **Phase C**
- [ ] `_CHUNK_SIZE` / `_CHUNK_COOLDOWN` / `_INTER_LLM_DELAY` replaced by semaphore-based concurrency control — **Phase C1**
- [ ] Concurrency limit configurable via env var (`SKILLS_EXTRACTION_CONCURRENCY=5`) — **Phase E1**
- [ ] Failed LLM call for one dimension does not block other dimensions — **Phase B1** (`return_exceptions=True`)
- [ ] DB writes remain safe (no session conflicts) — **Phase D**
- [ ] No regression on extraction quality (same results, just faster) — **Phase F4**
- [ ] 568-job batch completes in under 1 hour — **Phase C** (expected: 20-40 min)

---

## Execution Order

```
A1 → A2a → A2b → A2c → A2d    (async infrastructure — can be one PR)
    ↓
B1 → F2                        (intra-job parallelism + tests)
    ↓
C1 → C2 → D1 → D2              (inter-job parallelism + DB safety)
    ↓
E1 → E2 → E3                   (config + observability)
    ↓
F1 → F3 → F4 → F5              (remaining tests)
    ↓
G1 → G2 → G3 → G4              (docs + cleanup + close)
```

**Recommended PR strategy:**
1. **PR 1:** Phase A (async LLM infra) + Phase F1 — low risk, no behavior change
2. **PR 2:** Phase B (intra-job) + Phase F2 — 2x speedup, still serial across jobs
3. **PR 3:** Phase C + D + E + F3-F5 + G — full parallelism, 6-10x speedup

Or ship as a single PR if the branch is reviewed as a whole.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| `asyncio.run()` conflicts with existing event loop (Streamlit, Jupyter) | Detect loop with `asyncio.get_running_loop()`; use `nest_asyncio` or `loop.run_until_complete()` as fallback |
| 429 thundering herd with concurrent requests | Semaphore caps total concurrent jobs; 429 backoff in each extractor uses `asyncio.sleep` with jitter; server `Retry-After` header respected |
| DB session contention in `log_extraction_event` | Option A: increase pool_size to match concurrency. Option B: batch audit writes. Option C: per-coroutine session. Recommend Option A for simplicity. |
| Ordering changes break downstream consumers | `pending` list may be reordered — verify `_build_payload` doesn't depend on order. `results` list used by `save()` can be any order. |
| LangChain `ainvoke` behavior differs from `invoke` | Test with mocks first; then validate with real Azure endpoint on a small batch before running 568 jobs |
| `with_structured_output` + `ainvoke` compatibility | LangChain 0.2+ supports this; verify installed version. `include_raw=True` tested in A1. |
