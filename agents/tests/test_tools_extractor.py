"""Tests for deterministic Pass 1 tool extraction."""

from __future__ import annotations

from agents.common.types import JobRecord
from agents.skills_extraction.extractors.tools import extract_tools


def _job_record(**overrides: object) -> JobRecord:
    """Build a minimal normalized job record for extractor tests."""
    payload = {
        "source": "test-source",
        "external_id": "job-123",
        "title": "Senior Platform Engineer",
        "company": "Acme",
        "description": None,
        "requirements": None,
        "responsibilities": None,
    }
    payload.update(overrides)
    return JobRecord(**payload)


def test_extract_tools_finds_canonical_and_alias_matches() -> None:
    """Canonical names and aliases should normalize to one ToolRecord per tool."""
    job_record = _job_record(
        title="Senior Python Engineer",
        requirements="Build APIs with FastAPI and deploy them to Docker.",
        responsibilities="Own infrastructure in Terraform and GitHub Actions.",
        description=(
            "Experience with Amazon Web Services (AWS), PostgreSQL, and LangChain "
            "for internal AI workflows."
        ),
    )

    records = extract_tools(job_record)

    assert [record.tool_name for record in records] == [
        "Python",
        "FastAPI",
        "Docker",
        "Terraform",
        "GitHub Actions",
        "AWS",
        "PostgreSQL",
        "LangChain",
    ]
    assert next(record for record in records if record.tool_name == "AWS").source_span.text == (
        "Amazon Web Services"
    )
    assert next(record for record in records if record.tool_name == "LangChain").is_genai_tool is True
    assert next(record for record in records if record.tool_name == "Python").tool_id == "tool-python"


def test_extract_tools_skips_ambiguous_terms_without_context() -> None:
    """Precision-first matching should avoid verb and common-word false positives."""
    job_record = _job_record(
        description=(
            "You should excel at communication, go above and beyond for clients, "
            "and move fast in ambiguous environments."
        ),
    )

    assert extract_tools(job_record) == []


def test_extract_tools_keeps_go_when_technical_context_is_present() -> None:
    """The Go language should survive ambiguity filtering with clear stack context."""
    job_record = _job_record(
        description="Build backend services in Go, Python, and Kubernetes.",
    )

    records = extract_tools(job_record)
    tools_by_name = {record.tool_name: record for record in records}

    assert {"Go", "Python", "Kubernetes"} <= set(tools_by_name)
    assert tools_by_name["Go"].source_span.text == "Go"
    assert tools_by_name["Go"].confidence < tools_by_name["Python"].confidence


def test_extract_tools_avoids_nested_overlap_but_keeps_explicit_sql() -> None:
    """PostgreSQL should not imply SQL unless SQL appears as its own token."""
    job_record = _job_record(
        description="Use PostgreSQL for persistence and SQL for analytics.",
    )

    records = extract_tools(job_record)

    assert [record.tool_name for record in records] == ["PostgreSQL", "SQL"]
    assert [record.source_span.text for record in records] == ["PostgreSQL", "SQL"]


def test_extract_tools_dedupes_repeated_aliases_to_one_canonical_record() -> None:
    """Repeated aliases across fields should collapse to a single canonical tool."""
    job_record = _job_record(
        title="Postgres Platform Engineer",
        description="Deep PostgreSQL expertise and Postgres tuning experience.",
    )

    records = extract_tools(job_record)

    assert [record.tool_name for record in records] == ["PostgreSQL"]
    assert records[0].source_span.field_source == "description"
    assert records[0].source_span.text == "PostgreSQL"


def test_extract_tools_prefers_react_js_span_over_react_prefix() -> None:
    """React.js in text should emit React.js (eval GT label), not shorter React."""
    job_record = _job_record(
        description="Front-end experience with React.js and REST APIs.",
    )
    records = extract_tools(job_record)
    assert [record.tool_name for record in records] == ["React.js"]


def test_extract_tools_supports_explicit_excel_but_not_excel_as_a_verb() -> None:
    """Excel should only be returned when the local context is tool-specific."""
    positive_job = _job_record(
        requirements="Advanced Microsoft Excel and dashboard reporting experience required.",
    )
    negative_job = _job_record(
        responsibilities="Excel at stakeholder management and cross-functional delivery.",
    )

    positive_records = extract_tools(positive_job)

    assert [record.tool_name for record in positive_records] == ["Microsoft Excel"]
    assert positive_records[0].category == "other"
    assert extract_tools(negative_job) == []
