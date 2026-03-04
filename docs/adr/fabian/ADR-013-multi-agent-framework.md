# ADR-013: Multi-Agent Framework

**Status:** Proposed  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #13, ADR-016 (orchestration)

---

## Context and problem statement

The pipeline has eight agents that communicate only via typed, versioned events. We need a framework that models a sequential pipeline with conditional routing (e.g. only Orchestration consumes `*Failed` / `*Alert`), is Python-native, and integrates with LLM tracing. The framework should handle as much of the agent contract (events, health checks, error routing) as possible without forcing agents to call each other directly. The curriculum reference is LangGraph StateGraph.

## Considered options

* **LangGraph StateGraph** — Graph of nodes (agents/steps) and edges; conditional edges for routing. Python-native; integrates with LangSmith. Reference implementation.
* **CrewAI** — Task-based multi-agent framework with roles and collaboration. Python-native; different abstraction (tasks/agents vs graph nodes).
* **AutoGen** — Conversational multi-agent. Strong for dialogue flows; less natural for a batch pipeline with a strict event contract.
* **Semantic Kernel** — Microsoft stack; more .NET-oriented; less alignment with Python-only agents repo.
* **Custom** — In-process runner that invokes agents in sequence and routes by event type. Full control but no built-in tracing or standard patterns.

## Decision outcome

**Chosen option:** LangGraph StateGraph (reference implementation).

**Rationale:** The execution model maps directly to the spec: nodes are agents (or pipeline steps), edges are “next agent” or “to Orchestrator on failure.” Conditional routing (e.g. on event type or payload) is a first-class feature. The pipeline is batch-first (IC #3) and event-only; LangGraph does not require real-time streaming. LangSmith integration supports the tracing requirement (ADR-017). Using the same framework for orchestration (ADR-016) means one tool to learn and one execution model. CrewAI and AutoGen optimize for different patterns (task delegation, conversation); a custom runner would duplicate routing and tracing that LangGraph provides.

## Consequences

* **Positive:** Single framework for pipeline and orchestration; clear graph model; native tracing path; curriculum and exercises align.
* **Negative:** Dependency on LangChain/LangGraph ecosystem; team must learn StateGraph API.
* **Neutral:** If the team later needs durable execution or human-in-the-loop, LangGraph has extensions but may require additional plumbing.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #13 evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — event-only communication, Orchestration sole consumer of failures
* https://docs.langchain.com/oss/python/langgraph/overview — LangGraph overview
