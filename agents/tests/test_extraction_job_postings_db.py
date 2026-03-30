"""Integration tests: sample 15–20 ``job_postings`` rows with no ``extracted_intelligence`` linkage.

Uses :mod:`agents.tests.support.job_posting_extraction_query` (see SQL and linkage rules there).

- ``extract_context``: real Pass 1, zero LLM tokens, ``source_span`` checks.
- ``extract_tasks`` / ``extract_responsibilities``: LLM mocked (CI-safe); validates wiring + spans.

Requires ``PYTHON_DATABASE_URL`` and a seeded ``dbo.job_postings`` / ``dbo.companies`` schema.

Run (repo root)::

    python -m pytest agents/tests/test_extraction_job_postings_db.py -v -m integration

Omit ``-m integration`` to run with the rest of the suite (skips if DB unset).
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import TypeAdapter
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from agents.common.types import ContextSignal, JobRecord, ResponsibilityRecord, SpanRecord, TaskRecord
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import (
    _ResponsibilitiesLLMRoot,
    extract_responsibilities,
)
from agents.skills_extraction.extractors.tasks import _TasksLLMRoot, extract_tasks
from agents.tests.support.job_posting_extraction_query import (
    DEFAULT_MAX_SAMPLE,
    DEFAULT_MIN_SAMPLE,
    fetch_unextracted_job_posting_rows,
    row_to_job_record,
)


def _field_text(job: JobRecord, field_source: str) -> str:
    raw = getattr(job, field_source, None)
    return raw if isinstance(raw, str) else ""


def _assert_span_anchors(job: JobRecord, span: SpanRecord) -> None:
    text = _field_text(job, span.field_source)
    assert 0 <= span.start_char <= len(text)
    assert 0 <= span.end_char <= len(text)
    assert text[span.start_char : span.end_char] == span.text


@pytest.fixture(scope="module")
def integration_engine() -> Engine:
    url = os.getenv("PYTHON_DATABASE_URL")
    if not url:
        pytest.skip("PYTHON_DATABASE_URL not set — integration tests skipped")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database unreachable: {exc}")
    return engine


@pytest.fixture(scope="module")
def unextracted_posting_rows(integration_engine: Engine) -> list[dict]:
    with integration_engine.connect() as conn:
        rows = fetch_unextracted_job_posting_rows(conn, limit=DEFAULT_MAX_SAMPLE)
    if len(rows) < DEFAULT_MIN_SAMPLE:
        pytest.skip(
            f"Need at least {DEFAULT_MIN_SAMPLE} unextracted job_postings; got {len(rows)}. "
            "Seed the database or clear extracted_intelligence/normalized_jobs links for more coverage."
        )
    return rows


@pytest.fixture(scope="module")
def unextracted_job_records(unextracted_posting_rows: list[dict]) -> list[JobRecord]:
    return [row_to_job_record(r) for r in unextracted_posting_rows]


@pytest.mark.integration
def test_unextracted_job_postings_query_size(unextracted_posting_rows: list[dict]) -> None:
    assert DEFAULT_MIN_SAMPLE <= len(unextracted_posting_rows) <= DEFAULT_MAX_SAMPLE


@pytest.mark.integration
def test_extract_context_db_job_postings_tokens_and_spans(unextracted_job_records: list[JobRecord]) -> None:
    adapter = TypeAdapter(list[ContextSignal])
    for job in unextracted_job_records:
        signals, meta = extract_context(job)
        assert meta.get("tokens_used") == 0
        assert float(meta.get("cost_usd") or 0) == 0.0
        inner = meta.get("extraction_metadata") or {}
        assert inner.get("tokens_used") == 0
        assert inner.get("pass2_llm_calls") == 0
        adapter.validate_python(signals)
        for sig in signals:
            _assert_span_anchors(job, sig.source_span)


def _title_span(job: JobRecord) -> SpanRecord:
    t = (job.title or "").strip()
    assert t, "job must have non-empty title"
    end = min(len(t), 24)
    snippet = t[:end]
    return SpanRecord(text=snippet, field_source="title", start_char=0, end_char=len(snippet))


def _description_span(job: JobRecord) -> SpanRecord | None:
    d = (job.description or "").strip()
    if len(d) < 8:
        return None
    end = min(len(d), 40)
    snippet = d[:end]
    return SpanRecord(text=snippet, field_source="description", start_char=0, end_char=len(snippet))


def _make_tasks_side_effect(jobs: list[JobRecord]):
    idx = 0

    def _side_effect(_prompt: str, _schema: type, **_kw: object):
        nonlocal idx
        job = jobs[idx % len(jobs)]
        idx += 1
        span = _title_span(job)
        root = _TasksLLMRoot(
            tasks=[
                TaskRecord(
                    task_description="DB sample task",
                    task_category="core",
                    seniority_signal="any",
                    confidence=0.88,
                    source_span=span,
                )
            ]
        )
        meta = {
            "extraction_failed": False,
            "tokens_used": 12,
            "cost_usd": 0.0,
            "model": "mock-tasks",
            "latency_ms": 1,
        }
        return root, meta

    return _side_effect


def _make_resp_side_effect(jobs: list[JobRecord]):
    idx = 0

    def _side_effect(_prompt: str, _schema: type, **_kw: object):
        nonlocal idx
        job = jobs[idx % len(jobs)]
        idx += 1
        span = _description_span(job) or _title_span(job)
        root = _ResponsibilitiesLLMRoot(
            responsibilities=[
                ResponsibilityRecord(
                    responsibility_description="DB sample responsibility",
                    scope="individual",
                    requires_ai_competency=False,
                    confidence=0.86,
                    source_span=span,
                )
            ]
        )
        meta = {
            "extraction_failed": False,
            "tokens_used": 20,
            "cost_usd": 0.0,
            "model": "mock-resp",
            "latency_ms": 1,
        }
        return root, meta

    return _side_effect


@pytest.mark.integration
def test_extract_tasks_db_job_postings_mocked_llm(unextracted_job_records: list[JobRecord]) -> None:
    jobs = unextracted_job_records
    side_effect = _make_tasks_side_effect(jobs)
    with patch(
        "agents.skills_extraction.extractors.tasks.invoke_structured_extraction_llm",
        side_effect=side_effect,
    ):
        for job in jobs:
            ctx, _ = extract_context(job)
            tasks, meta = extract_tasks(job, pass1_context=ctx)
            assert meta.get("extraction_failed") is False
            assert meta.get("tokens_used", 0) > 0
            assert len(tasks) == 1
            _assert_span_anchors(job, tasks[0].source_span)


@pytest.mark.integration
def test_extract_responsibilities_db_job_postings_mocked_llm(unextracted_job_records: list[JobRecord]) -> None:
    jobs = unextracted_job_records
    side_effect = _make_resp_side_effect(jobs)
    with patch(
        "agents.skills_extraction.extractors.responsibilities.invoke_structured_extraction_llm",
        side_effect=side_effect,
    ):
        for job in jobs:
            ctx, _ = extract_context(job)
            rows, meta = extract_responsibilities(job, pass1_context=ctx)
            assert meta.get("extraction_failed") is False
            assert meta.get("tokens_used", 0) > 0
            assert len(rows) == 1
            _assert_span_anchors(job, rows[0].source_span)


@pytest.mark.integration
def test_extraction_db_job_postings_combined_pass1_and_mocked_pass2(unextracted_job_records: list[JobRecord]) -> None:
    jobs = unextracted_job_records[: min(18, len(unextracted_job_records))]
    task_se = _make_tasks_side_effect(jobs)
    resp_se = _make_resp_side_effect(jobs)
    with (
        patch(
            "agents.skills_extraction.extractors.tasks.invoke_structured_extraction_llm",
            side_effect=task_se,
        ),
        patch(
            "agents.skills_extraction.extractors.responsibilities.invoke_structured_extraction_llm",
            side_effect=resp_se,
        ),
    ):
        for job in jobs:
            ctx, cmeta = extract_context(job)
            assert cmeta.get("tokens_used") == 0
            tasks, tmeta = extract_tasks(job, pass1_context=ctx)
            assert tmeta.get("extraction_failed") is False
            for t in tasks:
                _assert_span_anchors(job, t.source_span)
            resp, rmeta = extract_responsibilities(job, pass1_context=ctx)
            assert rmeta.get("extraction_failed") is False
            for r in resp:
                _assert_span_anchors(job, r.source_span)
