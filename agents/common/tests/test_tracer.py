"""
test_tracer.py — EXP-006 observability test suite.

Run with:
    cd agents
    pytest common/tests/test_tracer.py -v
"""

from __future__ import annotations

import time
import uuid

import pytest

from agents.common.event_envelope import EventEnvelope
from agents.common.observability.langfuse_tracer import LangfuseTracer
from agents.common.observability.langsmith_tracer import LangSmithTracer
from agents.common.observability.otel_tracer import OTelTracer
from agents.common.observability.structlog_tracer import StructlogTracer
from agents.common.tracer_base import TracerBase
from agents.ingestion.agent_instrumented import InstrumentedIngestionAgent

TRACER_KINDS = ["structlog", "langsmith", "langfuse", "otel"]


def _make_tracer(kind: str) -> TracerBase:
    tracers = {
        "structlog": StructlogTracer(agent_id="ingestion-agent"),
        "langsmith": LangSmithTracer(agent_id="ingestion-agent"),
        "langfuse": LangfuseTracer(agent_id="ingestion-agent"),
        "otel": OTelTracer(agent_id="ingestion-agent"),
    }
    return tracers[kind]


def _make_event(*, simulate_error: str | None = None, dedup_count: int = 0) -> EventEnvelope:
    return EventEnvelope(
        correlation_id=str(uuid.uuid4()),
        agent_id="test-runner",
        payload={
            "posting_id": str(uuid.uuid4()),
            "source": "jsearch",
            "title": "Software Engineer",
            "company": "Acme Corp",
            "location": "Seattle, WA",
            "dedup_count": dedup_count,
            **({"simulate_error": simulate_error} if simulate_error else {}),
        },
    )


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_tracer_is_instance_of_base(kind: str) -> None:
    assert isinstance(_make_tracer(kind), TracerBase)


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_span_opens_and_closes(kind: str) -> None:
    tracer = _make_tracer(kind)
    cid = str(uuid.uuid4())
    with tracer.start_span("test_span", correlation_id=cid):
        pass
    if kind == "langsmith":
        assert tracer.get_runs()[-1]["status"] == "success"
    if kind == "langfuse":
        assert tracer.get_traces()[-1]["status"] == "success"
    if kind == "otel":
        assert tracer.get_spans()[-1]["status"] == "success"


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_correlation_id_propagated(kind: str) -> None:
    tracer = _make_tracer(kind)
    cid = str(uuid.uuid4())
    with tracer.start_span("correlation_test", correlation_id=cid):
        tracer.log_event("test_event", {"foo": "bar"})
    if kind == "langsmith":
        assert tracer.get_runs()[0]["correlation_id"] == cid
    if kind == "langfuse":
        assert tracer.get_traces()[0]["correlation_id"] == cid
    if kind == "otel":
        assert tracer.get_spans()[0]["correlation_id"] == cid


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_error_surfaced_and_reraised(kind: str) -> None:
    tracer = _make_tracer(kind)
    start = time.perf_counter()
    with pytest.raises(ValueError), tracer.start_span("error_span", correlation_id=str(uuid.uuid4())):
        raise ValueError("bad api key")
    assert time.perf_counter() - start < 30


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_latency_and_counter(kind: str) -> None:
    tracer = _make_tracer(kind)
    with tracer.start_span("metrics_test", correlation_id=str(uuid.uuid4())):
        tracer.record_latency("source_fetch", seconds=0.123)
        tracer.record_latency("dedup_check", seconds=0.005)
        tracer.increment_counter("dedup_count", value=3)
    if kind == "langsmith":
        ops = [e.get("operation") for e in tracer.get_runs()[-1]["events"]]
        assert "source_fetch" in ops
    if kind == "langfuse":
        ops = [e.get("operation") for e in tracer.get_traces()[-1]["events"]]
        assert "source_fetch" in ops
    if kind == "otel":
        ops = [e.get("operation") for e in tracer.get_spans()[-1]["events"]]
        assert "source_fetch" in ops


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_instrumented_agent_produces_ingest_batch_event(kind: str) -> None:
    agent = InstrumentedIngestionAgent(tracer=_make_tracer(kind))
    result = agent.process(_make_event())
    assert result.payload["event_type"] == "IngestBatch"


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_instrumented_agent_surfaces_error(kind: str) -> None:
    agent = InstrumentedIngestionAgent(tracer=_make_tracer(kind))
    start = time.perf_counter()
    with pytest.raises(ValueError, match="SourceFailure"):
        agent.process(_make_event(simulate_error="invalid api key"))
    assert time.perf_counter() - start < 30


@pytest.mark.parametrize("kind", TRACER_KINDS)
def test_100_job_batch(kind: str) -> None:
    agent = InstrumentedIngestionAgent(tracer=_make_tracer(kind))
    success_count = 0
    for i in range(100):
        result = agent.process(_make_event(dedup_count=i % 5))
        assert result.payload["event_type"] == "IngestBatch"
        success_count += 1
    assert success_count == 100


def test_structlog_tracer_has_no_framework_dependency() -> None:
    import sys
    hidden = {}
    for mod in list(sys.modules.keys()):
        if "langchain" in mod or "langgraph" in mod:
            hidden[mod] = sys.modules.pop(mod)
    try:
        tracer = StructlogTracer(agent_id="test")
        with tracer.start_span("independence_test", correlation_id="test-cid"):
            tracer.log_event("ok", {"framework": "none"})
    finally:
        sys.modules.update(hidden)
