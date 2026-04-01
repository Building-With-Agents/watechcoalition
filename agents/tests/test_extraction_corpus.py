"""Corpus tests (18+ jobs) for Pass 1 ``extract_context`` and Pass 2 ``extract_tasks`` / ``extract_responsibilities``.

- ``extract_context``: real regex path — zero LLM tokens, every signal's span slices the source field.
- ``extract_tasks`` / ``extract_responsibilities``: LLM is mocked — validates prompt wiring, Pass 1 context injection,
  and that returned records have ``source_span`` anchored in the job (same pattern as production schema checks).

Run: ``python -m pytest agents/tests/test_extraction_corpus.py -v`` from repo root.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import TypeAdapter

from agents.common.types import (
    ContextSignal,
    JobRecord,
    ResponsibilityRecord,
    SpanRecord,
    TaskRecord,
)
from agents.skills_extraction.extractors.context import extract_context
from agents.skills_extraction.extractors.responsibilities import (
    _ResponsibilitiesLLMRoot,
    extract_responsibilities,
)
from agents.skills_extraction.extractors.tasks import _TasksLLMRoot, extract_tasks

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_GROUND_TRUTH_PATH = _REPO_ROOT / "tools" / "ground-truth-labeler" / "ground_truth_labeled.json"

# 18 synthetic normalized jobs — mix of regex hits and intentional sparse rows.
_CORPUS_JOBS: list[JobRecord] = [
    JobRecord(
        source="corpus",
        external_id="c01",
        title="Software Engineer",
        company="Acme",
        description="We offer a hybrid schedule with two days onsite per week.",
    ),
    JobRecord(
        source="corpus",
        external_id="c02",
        title="Fully remote Staff Engineer",
        company="RemoteCo",
        description="Build APIs with PostgreSQL.",
    ),
    JobRecord(
        source="corpus",
        external_id="c03",
        title="Analyst",
        company="Corp",
        requirements="Work from home is available for this position.",
    ),
    JobRecord(
        source="corpus",
        external_id="c04",
        title="PM",
        company="BigCo",
        description="You will lead a team of 8 engineers across products.",
    ),
    JobRecord(
        source="corpus",
        external_id="c05",
        title="Director",
        company="Mega",
        responsibilities="This role reports to the VP of Engineering.",
    ),
    JobRecord(
        source="corpus",
        external_id="c06",
        title="Developer",
        company="AgileInc",
        description="We follow Scrum with sprint planning every two weeks.",
    ),
    JobRecord(
        source="corpus",
        external_id="c07",
        title="Researcher",
        company="AILab",
        description="Experience with generative AI and LLMs is a strong plus.",
    ),
    JobRecord(
        source="corpus",
        external_id="c08",
        title="Scientist",
        company="DataCo",
        requirements="Deep learning and machine learning model deployment required.",
    ),
    JobRecord(
        source="corpus",
        external_id="c09",
        title="Engineering Manager",
        company="MixCo",
        description="Hybrid role. Daily stand-up with the team. Matrix reporting applies.",
    ),
    JobRecord(
        source="corpus",
        external_id="c10",
        title="Accountant",
        company="Ledger LLC",
        description="Prepare quarterly filings.",
    ),
    JobRecord(
        source="corpus",
        external_id="c11",
        title="Field Tech",
        company="OnSite Co",
        description="On-site required at client locations five days per week.",
    ),
    JobRecord(
        source="corpus",
        external_id="c12",
        title="Coach",
        company="LeanOrg",
        responsibilities="Facilitate Kanban boards and continuous improvement.",
    ),
    JobRecord(
        source="corpus",
        external_id="c13",
        title="Consultant",
        company="Matrix LLC",
        requirements="Experience with dotted-line reporting in large programs.",
    ),
    JobRecord(
        source="corpus",
        external_id="c14",
        title="MLE",
        company="GenCo",
        description="We are AI-first and ship ML models to production.",
    ),
    JobRecord(
        source="corpus",
        external_id="c15",
        title="Lead",
        company="Startup",
        description="Join our 4-6 person team building the core platform.",
    ),
    JobRecord(
        source="corpus",
        external_id="c16",
        title="PMO",
        company="Enterprise",
        requirements="SAFe program experience preferred.",
    ),
    JobRecord(
        source="corpus",
        external_id="c17",
        title="Dev",
        company="WFH Inc",
        description="100% remote within the United States.",
    ),
    JobRecord(
        source="corpus",
        external_id="c18",
        title="Minimal Title Only",
        company="Co",
    ),
]


def _ground_truth_jobs(limit: int = 20) -> list[JobRecord]:
    if not _GROUND_TRUTH_PATH.is_file():
        return []
    data = json.loads(_GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    out: list[JobRecord] = []
    for row in data[:limit]:
        if not isinstance(row, dict):
            continue
        title = (row.get("title") or "").strip()
        company = (row.get("company") or "Unknown").strip() or "Unknown"
        if not title:
            continue
        out.append(
            JobRecord(
                source=str(row.get("source") or "ground-truth"),
                external_id=str(row.get("external_id") or row.get("ground_truth_id") or "gt"),
                title=title,
                company=company,
                description=row.get("description"),
                requirements=row.get("requirements"),
                responsibilities=row.get("responsibilities"),
            )
        )
    return out


def all_corpus_jobs() -> list[JobRecord]:
    """Synthetic 18 + up to 20 ground-truth rows when the JSON exists (for 10–20+ total)."""
    jobs = list(_CORPUS_JOBS)
    jobs.extend(_ground_truth_jobs(20))
    return jobs


def _field_text(job: JobRecord, field_source: str) -> str:
    raw = getattr(job, field_source, None)
    return raw if isinstance(raw, str) else ""


def _assert_span_anchors(job: JobRecord, span: SpanRecord) -> None:
    text = _field_text(job, span.field_source)
    assert 0 <= span.start_char <= len(text)
    assert 0 <= span.end_char <= len(text)
    assert text[span.start_char : span.end_char] == span.text


def _title_span(job: JobRecord) -> SpanRecord:
    t = (job.title or "").strip()
    assert t, "corpus job must have non-empty title"
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


# --- extract_context ---


def test_extract_context_corpus_tokens_and_spans() -> None:
    adapter = TypeAdapter(list[ContextSignal])
    for job in all_corpus_jobs():
        signals, meta = extract_context(job)
        assert meta.get("tokens_used") == 0
        assert float(meta.get("cost_usd") or 0) == 0.0
        inner = meta.get("extraction_metadata") or {}
        assert inner.get("tokens_used") == 0
        assert inner.get("pass2_llm_calls") == 0
        adapter.validate_python(signals)
        for sig in signals:
            _assert_span_anchors(job, sig.source_span)


def test_extract_context_corpus_synthetic_populated() -> None:
    with_signals = 0
    for job in _CORPUS_JOBS:
        signals, _ = extract_context(job)
        if signals:
            with_signals += 1
    assert with_signals >= 14, f"expected most synthetic jobs to match patterns; got {with_signals}/18"


@pytest.mark.skipif(
    not _GROUND_TRUTH_PATH.is_file(),
    reason=f"Ground truth JSON not found: {_GROUND_TRUTH_PATH}",
)
def test_extract_context_ground_truth_file_has_signals() -> None:
    jobs = _ground_truth_jobs(20)
    assert jobs
    total = 0
    for job in jobs:
        signals, meta = extract_context(job)
        assert meta.get("tokens_used") == 0
        for sig in signals:
            _assert_span_anchors(job, sig.source_span)
        total += len(signals)
    assert total >= 1


# --- extract_tasks (mocked LLM) ---


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
                    task_description="Corpus smoke task",
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


def test_extract_tasks_corpus_mocked_llm_spans() -> None:
    jobs = all_corpus_jobs()
    assert len(jobs) >= 10
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


# --- extract_responsibilities (mocked LLM) ---


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
                    responsibility_description="Corpus smoke responsibility",
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


def test_extract_responsibilities_corpus_mocked_llm_spans() -> None:
    jobs = all_corpus_jobs()
    assert len(jobs) >= 10
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


def test_extraction_corpus_combined_pass1_and_mocked_pass2() -> None:
    """One loop: context (real) + tasks + responsibilities (both mocked) for each job."""
    jobs = _CORPUS_JOBS[:15]
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
