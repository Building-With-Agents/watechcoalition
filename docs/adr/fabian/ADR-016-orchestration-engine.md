# ADR-016: Orchestration Engine

**Status:** Superseded — Decision promoted to Architectural (locked). Retained for history; not ADR-eligible under the new classification.  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #16, ADR-013 (multi-agent framework)

---

## Context and problem statement

The Orchestration Agent is the sole consumer of all `*Failed` and `*Alert` events. It must run the pipeline on a schedule (APScheduler, IC #3), route events between agents, apply retry policies with exponential back-off, and maintain a 100% complete audit log. We need an engine that supports a stateful graph (sequential pipeline with conditional edges), integrates with the chosen multi-agent framework (#13), and does not require a separate workflow server for Phase 1.

## Considered options

* **LangGraph StateGraph** — Same as ADR-013. Orchestration is implemented as a graph that invokes agent nodes and routes on event type. Reference implementation; consistent with #13.
* **Temporal** — Durable workflow engine. Requires a Temporal server; strong for long-running and retries but adds infrastructure.
* **Prefect** — Workflow and scheduling. Python-native; can run in-process; different model (flows/tasks) than event-driven agents.
* **Airflow** — DAG-based scheduling. Oriented toward batch DAGs and operators; less natural fit for an event envelope contract and single-consumer failure handling.
* **Custom** — Python loop: poll schedule, build event, call agents in sequence, handle returns and failures. Full control; no shared framework with agent graph.

## Decision outcome

**Chosen option:** LangGraph StateGraph (reference implementation), consistent with ADR-013.

**Rationale:** Using the same framework for the pipeline and for orchestration means one execution model, one tracing story (LangSmith), and one codebase to learn. The Orchestration Agent can be implemented as a LangGraph that has nodes for “run ingestion,” “run normalization,” etc., and conditional edges that route `*Failed` / `*Alert` to a dedicated handling node while success events flow to the next agent. APScheduler triggers the graph run; retry and back-off can be implemented inside the graph or in the runner. Temporal and Airflow are powerful but introduce a separate server and a different paradigm; for Phase 1 the spec’s “LangGraph StateGraph + APScheduler” keeps complexity minimal and aligns with the curriculum. If the team had chosen a different multi-agent framework in ADR-013, orchestration would need to align with that choice instead.

## Consequences

* **Positive:** One framework for pipeline and orchestration; unified tracing; no extra orchestration server; curriculum alignment.
* **Negative:** Tighter coupling to LangGraph; advanced durability (e.g. Temporal-style) would require a later migration.
* **Neutral:** Retry and audit-log logic remain our responsibility; LangGraph provides structure, not policy.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #16 options and evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — Orchestration Agent, retry policies, audit log, sole consumer of failures
* ADR-013 — Multi-Agent Framework (consistency with #13)

**Implementation note (2026-03):** Classification update: this decision is now Architectural; the ADR is no longer used for team deliberation.
