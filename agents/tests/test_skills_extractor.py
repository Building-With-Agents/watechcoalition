"""Tests for Pass 2 skills extraction (extract_skills)."""

from __future__ import annotations

from unittest.mock import patch

from agents.common.types import JobRecord, SpanRecord, ToolRecord
from agents.skills_extraction.extractors.skills import extract_skills


def _job_record(**overrides: object) -> JobRecord:
    payload = {
        "source": "test",
        "external_id": "job-1",
        "title": "Senior Engineer",
        "company": "Acme",
        "description": "Python and SQL required. Lead cross-functional teams.",
        "requirements": "5+ years Python, REST APIs.",
        "responsibilities": None,
    }
    payload.update(overrides)
    return JobRecord(**payload)


def _tool_record(name: str) -> ToolRecord:
    return ToolRecord(
        tool_name=name,
        category="language",
        confidence=0.95,
        source_span=SpanRecord(text=name, field_source="requirements", start_char=0, end_char=len(name)),
    )


@patch("agents.skills_extraction.extractors.skills._invoke_client")
def test_extract_skills_returns_skill_records_and_metadata_when_llm_succeeds(
    mock_invoke,
) -> None:
    mock_invoke.return_value = (
        '{"skills": ['
        '{"label": "Python", "type": "Technical", "confidence": 0.92, "required_flag": true, '
        '"source_span": {"text": "Python", "field_source": "requirements", "start_char": 0, "end_char": 6}},'
        '{"label": "SQL", "type": "Technical", "confidence": 0.85, "required_flag": null, '
        '"source_span": {"text": "SQL", "field_source": "requirements", "start_char": 8, "end_char": 11}}'
        "]}",
        {"success": True, "tokens_used": 100, "cost_usd": 0.0, "extraction_failed": False},
    )
    job = _job_record()
    skills, meta = extract_skills(job, pass1_tools=[])
    assert len(skills) == 2
    assert skills[0].skill_name == "Python"
    assert skills[0].type == "Technical"
    assert skills[1].skill_name == "SQL"
    assert skills[1].type == "Technical"
    assert meta["success"] is True
    assert meta.get("tokens_used") == 100


@patch("agents.skills_extraction.extractors.skills._invoke_client")
def test_extract_skills_calls_taxonomy_and_sets_esco_uri(
    mock_invoke,
) -> None:
    mock_invoke.return_value = (
        '{"skills": ['
        '{"label": "Python", "type": "Technical", "confidence": 0.9, "required_flag": true, '
        '"source_span": {"text": "Python", "field_source": "requirements", "start_char": 0, "end_char": 6}}'
        "]}",
        {"success": True, "extraction_failed": False},
    )
    job = _job_record()
    skills, _ = extract_skills(job, pass1_tools=[])
    assert len(skills) == 1
    assert skills[0].skill_name == "Python"
    assert hasattr(skills[0], "esco_uri")
    assert hasattr(skills[0], "is_genai_extension")


@patch("agents.skills_extraction.extractors.skills._invoke_client")
def test_extract_skills_invalid_json_returns_empty_and_failed(
    mock_invoke,
) -> None:
    mock_invoke.return_value = ("not valid json {", {"success": True, "extraction_failed": False})
    job = _job_record()
    skills, meta = extract_skills(job, pass1_tools=[])
    assert skills == []
    assert meta["extraction_failed"] is True


@patch("agents.skills_extraction.extractors.skills._invoke_client")
def test_extract_skills_includes_pass1_tools_in_prompt_context(
    mock_invoke,
) -> None:
    mock_invoke.return_value = (
        '{"skills": [{"label": "Leadership", "type": "Soft", "confidence": 0.8, "required_flag": null, '
        '"source_span": {"text": "Lead", "field_source": "description", "start_char": 0, "end_char": 4}}]}',
        {"success": True, "extraction_failed": False},
    )
    job = _job_record(description="Lead teams. Python experience.")
    tools = [_tool_record("Python")]
    skills, _ = extract_skills(job, pass1_tools=tools)
    assert len(skills) == 1
    assert skills[0].skill_name == "Leadership"
    call_args = mock_invoke.call_args[0][0]
    assert "Python" in call_args
    assert "Already extracted tools" in call_args or "already extracted" in call_args.lower()
    assert "Excellent communication skills" in call_args
    assert 'SKIP generic "Communication"' in call_args
    assert 'do NOT invent "Scrum Facilitation"' in call_args
    assert 'do NOT suppress these because they are hard skills' in call_args
