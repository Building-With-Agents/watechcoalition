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

**Chosen option:** Provider-agnostic adapter with Azure OpenAI as default, switchable via `LLM_PROVIDER` env var.

**Rationale:** The spec requires fallback behavior (2 retries → log to `llm_audit_log` → set `extraction_status = "failed"` → continue batch). An adapter centralizes that behavior and keeps agents from duplicating retry and logging logic. Tests can use a mock or a local provider without a live Azure key. Cost and compliance can be addressed later by adding another provider implementation behind the same interface. The abstraction overhead is one small module; the benefit for testing and future flexibility justifies it.

## Consequences

* **Positive:** Tests can run without Azure credentials; fallback and audit logging live in one place; switching providers does not require editing agent code.
* **Negative:** One extra layer to maintain; new providers require implementing the adapter interface.
* **Neutral:** Default remains Azure OpenAI; teams that never switch still depend on the adapter.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #11 evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — Common Patterns (LLM adapter), fallback behavior
