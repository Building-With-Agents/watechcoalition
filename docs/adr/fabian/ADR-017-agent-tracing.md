# ADR-017: Agent Tracing

**Status:** Proposed  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #17, ADR-013 (multi-agent framework)

---

## Context and problem statement

The pipeline uses LLMs in multiple agents and must support debugging (which agent failed, what prompt was sent, latency, token usage) and audit (LLM calls logged to `llm_audit_log`). We need a tracing solution that captures LLM-specific data (prompts, responses, token counts, latency), integrates with the chosen multi-agent framework (#13), and is usable in the 12-week environment without excessive cost or setup.

## Considered options

* **LangSmith** — LangChain’s observability platform. Native integration with LangGraph; captures prompts, token usage, latency, and traces. SaaS; requires API key. Reference implementation.
* **OpenTelemetry + custom spans** — Vendor-neutral; export to Jaeger, Zipkin, or other backends. LLM-specific attributes (prompts, tokens) require custom instrumentation; no built-in LLM UI.
* **Arize Phoenix** — Open-source LLM observability. Can be self-hosted; good for LLM evals and debugging. Different integration path than LangChain stack.

## Decision outcome

**Chosen option:** LangSmith (reference implementation).

**Rationale:** LangGraph and LangChain have first-class LangSmith integration: traces appear with minimal configuration once `LANGSMITH_API_KEY` and `LANGCHAIN_TRACING_V2=true` are set. The spec requires logging every LLM call to `llm_audit_log`; we still implement that for audit compliance, while LangSmith provides a rich UI for debugging and evaluation. OpenTelemetry is valuable for vendor neutrality and self-hosted setups but would require custom spans and possibly a separate store for prompt/response content; that overhead is hard to justify in Phase 1 when the pipeline already assumes LangGraph. Arize Phoenix is a strong alternative for teams that want open-source and self-hosted; the tradeoff is integration effort with the LangGraph-based reference. Cost and data residency can be revisited if the team has strict constraints.

## Consequences

* **Positive:** Minimal setup; good UX for debugging agent and LLM behavior; aligns with LangGraph/LangChain stack.
* **Negative:** SaaS dependency and potential cost; data leaves the environment unless self-hosted options are used.
* **Neutral:** `llm_audit_log` in the database remains the canonical audit record; LangSmith is for development and operations visibility.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #17 options and evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — llm_audit_log, logging of LLM calls
* ADR-013 — Multi-Agent Framework (LangGraph integration)
