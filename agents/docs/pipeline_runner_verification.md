# Pipeline runner verification (Task 2.3)

Use this to verify and answer the exercise questions after building the runner.

---

## Exercise 2.3 — Design review (reply in thread)

Review `agents/pipeline_runner.py` and answer the design questions **before** running. Below are the five answers.

### 1) Where does correlation_id originate?

**In the pipeline runner only**, inside `run_pipeline()`, once per record:

```python
for record_index, raw_record in enumerate(raw_postings):
    correlation_id = str(uuid.uuid4())
    event = EventEnvelope(correlation_id=correlation_id, agent_id="runner", payload={"records": [raw_record]})
```

The runner never receives `correlation_id` from outside; it creates it with `uuid.uuid4()` so every record gets a unique id. Agents never create or change it: they get it on the inbound `EventEnvelope` and must pass it through via `create_outbound_event()`. The runner enforces that with a check after each agent: `if out.correlation_id != correlation_id` it raises `ValueError`. So the chain is: **runner creates → each agent propagates → runner verifies**.

### 2) What happens when health_check() fails?

**The pipeline aborts immediately** with a clear message; no records are processed.

`_health_check_gate()` runs `health_check()` on every agent in `PIPELINE_AGENTS`. Any agent whose status is **not** `"ok"` or `"degraded"` is treated as unhealthy. If there is at least one unhealthy agent, the runner builds a message like `"Pipeline aborted: unhealthy agent(s): ingestion=down"`, logs it with `log.error("health_check_failed", ...)`, and raises `SystemExit(msg)`. So it does **not** silently skip the agent; it exits so the operator can fix the failing agent before re-running.

### 3) Which log fields are essential per event?

**Four fields** are required per emitted event for tracing and diagnosis:

- **agent_id** — which agent produced the event  
- **event_id** — unique id for this event (UUID)  
- **correlation_id** — ties this event to one record’s journey through the pipeline  
- **timestamp** — when the event was produced (ISO UTC in the run log)

They come from `_event_to_log_dict(ev)` and are passed to structlog as `log.info("event_emitted", **_event_to_log_dict(out))`. The same four appear in each serialized event in `pipeline_run.json`. Without them you cannot trace a single record across agents or order events in time.

### 4) Why is a simple ordered sequence the right choice for this sprint?

For the **walking skeleton** (this sprint), a fixed ordered list is the right choice because:

- **Single responsibility:** The runner’s job is to chain agents and enforce the event contract. No branching, retries, or fan-out is required yet; the spec is “pass each record through all eight agents in sequence.”
- **Predictability:** One list, one loop. Easy to reason about, easy to debug (e.g. “record broke at agent 3”).
- **Extensibility without rework:** Adding a ninth agent is appending one entry to `PIPELINE_AGENTS`; no change to control flow. Selectivity (e.g. first N agents) is a slice on that same list (`--agents 0:3`).
- **Alignment with Phase 1:** Orchestration (LangGraph, APScheduler, retries, failure handling) is later. This sprint only needs “run health checks, then run the chain”; a simple sequence implements that and leaves room to replace it with a graph or scheduler when the curriculum reaches orchestration.

So the simple ordered sequence is the right choice for this sprint; we are not over-engineering.

### 5) How would you run only part of the pipeline for debugging?

Use the **`--agents`** argument with a slice in the form `start:stop` (or a single index):

```bash
python -m agents.pipeline_runner --agents 0:3
```

That runs only the first three agents (ingestion, normalization, skills_extraction). The runner slices `PIPELINE_AGENTS` with `agent_slice` (e.g. `slice(0, 3)`), so the inner loop iterates over that subset. You get fewer `event_emitted` lines and a shorter `pipeline_run.json` (e.g. 3 events per record instead of 7). Useful to isolate failures (e.g. “does it break in normalization or only after skills extraction?”) or to iterate quickly on the first few agents without running the rest.

---

## Where does correlation_id originate?

**In the runner**, once per record, in `run_pipeline()`:

```python
for record_index, raw_record in enumerate(raw_postings):
    correlation_id = str(uuid.uuid4())
    event = EventEnvelope(correlation_id=correlation_id, agent_id="runner", payload={"records": [raw_record]})
```

It is then **propagated unchanged** because every agent uses `create_outbound_event(inbound_event, payload)`, which copies `inbound_event.correlation_id` into the outbound envelope. The runner also checks `out.correlation_id == correlation_id` and raises if it changes.

## What happens if health_check() fails?

**The pipeline aborts** with a clear message. `_health_check_gate()` runs all agents’ `health_check()`, collects any with status not in `("ok", "degraded")`, and raises `SystemExit(msg)` where `msg` is e.g. `"Pipeline aborted: unhealthy agent(s): ingestion=down"`. No records are processed.

## What does the structlog output look like per event?

Each emitted event is logged with **all four required fields**:

```python
log.info("event_emitted", **_event_to_log_dict(out))
# -> agent_id, event_id, correlation_id, timestamp (ISO)
```

So you see one line per event with those four keys (plus level, timestamp from the processor, and event name). Example: `event_emitted agent_id=ingestion_agent event_id=... correlation_id=... timestamp=...`

## How does the runner iterate? Could you add a ninth agent?

The runner iterates over **`PIPELINE_AGENTS`**, a list of `(name, agent_instance)` tuples. To add a ninth agent: append one more tuple to `PIPELINE_AGENTS`. No other restructuring needed (extensibility).

## How do you run just the first three agents (selectivity)?

Use the **`--agents`** slice:

```bash
python -m agents.pipeline_runner --agents 0:3
```

That runs ingestion → normalization → skills_extraction only. Useful for debugging.

## Where does the run log get written? What format?

**Path:** `agents/data/output/pipeline_run.json` (from `agents.common.paths.PIPELINE_RUN_JSON`).

**Format:** JSON object (all timestamps via `agents.common.datetime_utils`, uniform ISO UTC with Z suffix):

- `run_id`, `started_at`, `finished_at`, `input_record_count`
- `events`: array of serialized `EventEnvelope` objects (each has `event_id`, `correlation_id`, `agent_id`, `timestamp`, `payload`)
- **Overwrite:** Each run overwrites `pipeline_run.json` (no append). To keep history, copy or rename the file before the next run.

`OUTPUT_DIR` is created if it doesn’t exist.
