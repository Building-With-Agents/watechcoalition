# ADR-007: Multi-Agent Framework for Pipeline Orchestration

**Status:** Adopted  
**Date:** 2026-03-12  
**Deciders:** Fabian (EXP-007 owner)  
**References:** EXP-007 plan and findings (`docs/planning/EXP-007-plan-and-findings-template.md` §10), ARCHITECTURAL_DECISIONS #13, #16, #17

---

## Context

The Job Intelligence Engine is an eight-agent Python pipeline (Ingestion → Normalization → Skills Extraction → Enrichment → Analytics → Visualization → Orchestration; Demand Analysis in Phase 2). The choice of **multi-agent framework** is the highest-leverage architectural decision: it locks event routing, state management, retry/alert behaviour, and observability for all agents. Switching at Week 6 would mean a rewrite; the decision must be informed by evidence and committed before significant implementation.

The architecture spec (ARCHITECTURAL_DECISIONS) had previously resolved #13 (Multi-Agent Framework) and #16 (Orchestration Engine) to **LangGraph StateGraph**, and #17 (Agent Tracing) to **LangSmith**. EXP-007 was run to validate that choice against a **pure Python** state-machine alternative: two runners were implemented (LangGraph and pure Python), compared on topology expressiveness, extensibility, failure handling, latency, and AgentBase compatibility.

---

## Decision

**Adopt LangGraph StateGraph for pipeline and orchestration.**

The pipeline runner and (in Week 6) the Orchestration Agent will use LangGraph’s `StateGraph` with typed state. Agents remain **pure Python** implementations of the existing `AgentBase` ABC; graph nodes call `agent.process(event)`. There is no framework-specific agent base class.

---

## Rationale

1. **Alignment with existing decisions:** ARCHITECTURAL_DECISIONS #13, #16, and #17 already resolve to LangGraph and LangSmith. EXP-007 confirmed that LangGraph works with the current AgentBase contract and that its overhead is acceptable for the target workload.

2. **Phase 2 readiness:** Week 6 requires conditional edges (retry, *Failed/*Alert routing), checkpointing, and clear failure propagation. LangGraph models these natively. A pure Python runner would require building custom retry logic, checkpointing, and a TracerBase to avoid “flying blind.”

3. **Performance:** For 100 stub events, LangGraph added ~95 ms total (~0.9 ms per event); pure Python ~1 ms total. For a daily batch pipeline (e.g. 1,000 jobs &lt; 5 min), this overhead is negligible and does not make the framework a bottleneck.

4. **AgentBase compatibility and resume:** Both candidates honor the AgentBase ABC (no conflicting base class). Both support resume-from-last-step (e.g. after Ingestion) without re-running prior agents. No disqualifying conflict was found.

5. **Declarative topology and tracing:** LangGraph provides an inspectable graph and native LangSmith integration; pure Python would require custom instrumentation and conventions to avoid fragmented retry/state behaviour.

---

## Alternatives Considered

### Pure Python state machine

- **Pros:** No framework dependency; minimal latency (measured ~95× faster for 100 stub events); full control; standard Python debugging.
- **Cons:** No built-in tracing (TracerBase must be built and maintained); no declarative topology; retry, routing, and checkpointing must be implemented and kept consistent across the pipeline. Phase 2 (circuit breakers, saga, compensating flows) would be more work than with LangGraph.

Rejected for this project because Phase 2 and observability are first-class requirements and LangGraph’s overhead is acceptable.

### CrewAI / AutoGen

- **Pros:** Alternative agent frameworks.
- **Cons:** Optimised for conversational/role-based collaboration, not a deterministic ETL-style pipeline. Not evaluated in depth; out of scope for the 2-day timebox.

---

## Consequences

### Positive

- Single framework for pipeline and orchestration; one mental model for the team.
- LangSmith captures node execution, state transitions, and LLM calls without custom spans.
- Conditional edges and checkpointing are available for Week 6 retry and alert routing.
- Agents stay framework-agnostic (AgentBase + EventEnvelope); only the runner is LangGraph-based.

### Negative

- Dependency on LangGraph (and its API/upgrade surface).
- Team must learn StateGraph, state typing, and LangSmith workflow.
- Per-invocation overhead (~0.9 ms in the stub benchmark) is accepted; for real agent work (e.g. LLM calls) it will be negligible relative to I/O.

### Linking to ARCHITECTURAL_DECISIONS

- **#13 (Multi-Agent Framework):** LangGraph StateGraph — validated by EXP-007; findings and this ADR document the evidence.
- **#16 (Orchestration Engine):** LangGraph StateGraph — same rationale; orchestration in Week 6 will use the same framework.
- **#17 (Agent Tracing):** LangSmith — native LangGraph integration; no change.

---

## References

- **EXP-007 plan and findings:** `docs/planning/EXP-007-plan-and-findings-template.md` (especially §10 EXP-007 Findings (Final)).
- **Implementations:** `agents/exp007/langgraph_runner.py`, `agents/exp007/pure_python_runner.py`.
- **Reproducibility:** `python agents/exp007/benchmark_100.py`, `python agents/exp007/crash_test.py`, `pytest agents/tests/test_exp007_crash_resume.py`, `pytest agents/tests/test_pipeline_runner.py -v`.
- **Architecture:** `docs/planning/ARCHITECTURE_DEEP.md`, `docs/planning/ARCHITECTURAL_DECISIONS.md`.
