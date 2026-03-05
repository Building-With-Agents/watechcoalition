# ADR-018: Analytics Query Interface

**Status:** Proposed  
**Decision makers:** Engineering  
**Related:** ARCHITECTURAL_DECISIONS.md #18

---

## Context and problem statement

The Analytics Agent exposes a query interface for “Ask the Data” (natural language → SQL with guardrails). Consumers are the Streamlit dashboard and, in principle, the Orchestration Agent or other internal callers. The interface must support passing a query (e.g. text or structured request), returning results, and enforcing SQL guardrails (SELECT only, allowlist tables, row limit, timeout). We need a protocol that is simple to implement, test, and secure within the Phase 1 scope.

## Considered options

* **REST — POST /analytics/query** — Single endpoint; request body carries query text or params; response is JSON (result set or error). Reference implementation.
* **GraphQL** — Flexible query language; clients request exact fields. Requires schema definition and resolver layer; more setup for a single “run query” use case.
* **SQL-over-wire (e.g. Trino)** — Expose a SQL endpoint directly. Powerful for power users but conflicts with the spec’s requirement for guardrails (SELECT only, allowlist, 100-row limit, 30s timeout); raw SQL wire would bypass application-level enforcement.

## Decision outcome

**Chosen option:** REST — `POST /analytics/query` (reference implementation).

**Rationale:** The evaluation criteria emphasize a small number of consumers (Streamlit + Orchestration), query complexity that fits “one question → one response,” and the need to enforce guardrails in application code. A REST endpoint receives the query in the body, runs it through the Analytics Agent’s text-to-SQL and guardrail layer, and returns a JSON result or an error. Guardrails (allowed tables, SELECT only, 100-row limit, 30s timeout) are enforced in the agent before any SQL is executed. GraphQL would add schema and resolver complexity without a clear benefit for this single query pattern. SQL-over-wire would require reimplementing guardrails at the wire layer or would expose raw SQL and violate the spec. REST is easy to test (httpx or requests), document (OpenAPI), and secure (single endpoint, no query string injection).

## Consequences

* **Positive:** Simple contract; guardrails live in one place; easy to test and document; fits Streamlit and internal callers.
* **Negative:** No standardized query language like GraphQL; ad-hoc request/response shape must be documented.
* **Neutral:** If the team later needs a more expressive interface, a second endpoint or versioned API can be added without replacing the first.

## Review summary (thread reply)

* **Which Tool decision you reviewed:** #18 — Analytics query interface (Analytics Agent).
* **One viable alternative:** GraphQL. Flexible query language; requires schema and resolvers; more setup for a single "run query" use case.
* **Which tradeoff matters most:** Simple contract + guardrails in one place vs. no standardized query language (ad-hoc request/response shape).
* **What would make the reference implementation the wrong choice:** Multiple consumers needing different field sets; need for a standardized query language; guardrails enforced at a different layer (e.g. SQL proxy).
* **What evidence belongs in the ADR:** ARCHITECTURE_DEEP (POST /analytics/query, SQL guardrails); small consumer set (Streamlit + Orchestration); SELECT-only, allowlist, 100-row limit, 30s timeout.

## References

* docs/planning/ARCHITECTURAL_DECISIONS.md — #18 options and evaluation criteria
* docs/planning/ARCHITECTURE_DEEP.md — Analytics Agent, POST /analytics/query, SQL guardrails
