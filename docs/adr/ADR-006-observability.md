# ADR-006 — Observability & Tracing

| | |
|---|---|
| **Owner** | Enrique |
| **Experiment** | EXP-006 |
| **Status** | Accepted |
| **Date** | Week 3 |

## Decision

Use structlog as the always-on baseline, with Langfuse as the optional trace platform.

## What I Tested

Four candidates via a TracerBase ABC:
- structlog — already installed, zero setup
- LangSmith — LangChain hosted tracing
- Langfuse — hosted or self-hosted, framework-independent
- OpenTelemetry — vendor-neutral distributed tracing

## What I Found

| Candidate     | Full trace UI | Setup time | Framework-independent |
|---------------|---------------|------------|-----------------------|
| structlog     |       No.     |    0 min.  |         Yes.          |
| LangSmith     |       Yes     |   ~10 min. |        Partial.       |
| Langfuse      |       Yes     |   ~15 min  |         Yes           |
| OpenTelemetry | Yes (Jaeger)  |   ~40 min  |         Yes           |

All four surfaced errors in under 1 second (target: 30s).

## Recommendation

structlog (always-on) + Langfuse (when trace UI needed).
TracerBase makes this swappable with zero agent code changes.

## Tradeoffs Acknowledged

- structlog alone has no visual UI — debugging cross-agent failures requires grep on JSON logs.
- Langfuse adds an external dependency. Offline environments should use structlog-only.
- If LangGraph wins EXP-007, LangSmith becomes more attractive — TracerBase makes swapping a one-line change.
- OTelTracer is ready for production when an APM backend is available.

## Data / Evidence

- 100-job batch: 100/100 success across all four tracers
- Error surfacing: < 1s for all four tracers (target < 30s)
- structlog setup: 0 minutes
- Langfuse setup: ~15 minutes (cloud)
- OTel setup: ~40 minutes (Jaeger + collector)
- TracerBase abstraction: zero agent code changes required to swap tracer
