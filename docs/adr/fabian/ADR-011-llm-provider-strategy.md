# ADR-011: LLM Provider Strategy

**Status:** Proposed  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #11

---

## Context and problem statement

The pipeline uses LLMs in Skills Extraction (required), Enrichment (optional), Analytics (optional), and Visualization (optional). We need a policy for which LLM provider(s) to use and how agents invoke them. The curriculum assumes Azure OpenAI as the default, but teams may want to switch providers for cost, compliance, or testing. Direct calls to a single provider create vendor lock-in and make it hard to run tests without a live API key or to compare costs across providers.

## Considered options

* **Provider-agnostic adapter** — Single abstraction (`agents/common/llm_adapter.py`) with `get_adapter(provider=os.getenv("LLM_PROVIDER", "azure_openai"))` and a `complete(prompt, schema)` interface. Azure OpenAI default; switchable via env.
* **Fixed provider** — All agents call Azure OpenAI (or another provider) directly. No abstraction layer.

## Decision outcome

**Chosen option:** Provider-agnostic adapter with Azure OpenAI as default, switchable via `LLM_PROVIDER` env var. This is the default implementation behind the `LLMAdapter` ABC (Decision #26); it can be swapped without changing agent code.

**Rationale:** The spec requires fallback behavior (2 retries → log to `llm_audit_log` → set `extraction_status = "failed"` → continue batch). An adapter centralizes that behavior and keeps agents from duplicating retry and logging logic. Tests can use a mock or a local provider without a live Azure key. Cost and compliance can be addressed later by adding another provider implementation behind the same interface. The abstraction overhead is one small module; the benefit for testing and future flexibility justifies it.

## Consequences

* **Positive:** Tests can run without Azure credentials; fallback and audit logging live in one place; switching providers does not require editing agent code.
* **Negative:** One extra layer to maintain; new providers require implementing the adapter interface.
* **Neutral:** Default remains Azure OpenAI; teams that never switch still depend on the adapter.

## Review summary (thread reply)

* **Which Tool decision you reviewed:** #11 — LLM provider strategy.
* **One viable alternative:** Fixed provider (e.g. Azure OpenAI only, no adapter). Simpler, but no testing without live key and no cost/compliance swap.
* **Which tradeoff matters most:** Testability and future swap cost vs. one extra abstraction to maintain.
* **What would make the reference implementation the wrong choice:** If the program never needed to test without Azure, never switched providers, and the adapter added measurable latency or bugs; or if a single fixed provider were a hard compliance requirement.
* **What evidence belongs in the ADR:** Week 2 scaffold of `llm_adapter.py`; fallback rule (2 retries → `llm_audit_log`); env var `LLM_PROVIDER`; test runs with mock adapter.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #11 evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — Common Patterns (LLM adapter), fallback behavior
