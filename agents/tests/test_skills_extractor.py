"""Tests for Pass 2 skills extraction (extract_skills) — structured output."""

from __future__ import annotations

from unittest.mock import patch

from agents.common.llm_client import _extract_retry_after
from agents.common.types import JobRecord, SpanRecord, ToolRecord
from agents.skills_extraction.extractors.skills import (
    _LLMSkill,
    _SkillsLLMRoot,
    extract_skills,
)


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


def _make_skills_root(*skills_data: dict) -> _SkillsLLMRoot:
    """Build a _SkillsLLMRoot from dicts for test mocking."""
    return _SkillsLLMRoot(skills=[_LLMSkill(**s) for s in skills_data])


@patch("agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm")
def test_extract_skills_returns_skill_records_and_metadata_when_llm_succeeds(
    mock_invoke,
) -> None:
    root = _make_skills_root(
        {
            "skill_name": "Python",
            "type": "Technical",
            "confidence": 0.92,
            "required_flag": True,
            "source_span": {"text": "Python", "field_source": "requirements", "start_char": 0, "end_char": 6},
        },
        {
            "skill_name": "SQL",
            "type": "Technical",
            "confidence": 0.85,
            "required_flag": None,
            "source_span": {"text": "SQL", "field_source": "requirements", "start_char": 8, "end_char": 11},
        },
    )
    mock_invoke.return_value = (
        root,
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


@patch("agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm")
def test_extract_skills_calls_taxonomy_and_sets_esco_uri(
    mock_invoke,
) -> None:
    root = _make_skills_root(
        {
            "skill_name": "Python",
            "type": "Technical",
            "confidence": 0.9,
            "required_flag": True,
            "source_span": {"text": "Python", "field_source": "requirements", "start_char": 0, "end_char": 6},
        },
    )
    mock_invoke.return_value = (root, {"success": True, "extraction_failed": False})
    job = _job_record()
    skills, _ = extract_skills(job, pass1_tools=[])
    assert len(skills) == 1
    assert skills[0].skill_name == "Python"
    assert hasattr(skills[0], "esco_uri")
    assert hasattr(skills[0], "is_genai_extension")


@patch("agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm")
def test_extract_skills_empty_response_returns_failed(
    mock_invoke,
) -> None:
    mock_invoke.return_value = (
        None,
        {"success": False, "extraction_failed": True, "error_reason": "structured_output_empty"},
    )
    job = _job_record()
    skills, meta = extract_skills(job, pass1_tools=[])
    assert skills == []
    assert meta["extraction_failed"] is True


@patch("agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm")
def test_extract_skills_includes_pass1_tools_in_prompt_context(
    mock_invoke,
) -> None:
    root = _make_skills_root(
        {
            "skill_name": "Leadership",
            "type": "Soft",
            "confidence": 0.8,
            "required_flag": None,
            "source_span": {"text": "Lead", "field_source": "description", "start_char": 0, "end_char": 4},
        },
    )
    mock_invoke.return_value = (root, {"success": True, "extraction_failed": False})
    job = _job_record(description="Lead teams. Python experience.")
    tools = [_tool_record("Python")]
    skills, _ = extract_skills(job, pass1_tools=tools)
    assert len(skills) == 1
    assert skills[0].skill_name == "Leadership"
    # Verify prompt includes tools and prompt v4 guardrails
    call_args = mock_invoke.call_args
    prompt = call_args[0][0]
    assert "Python" in prompt
    assert "Already extracted tools" in prompt or "already extracted" in prompt.lower()


# ---------------------------------------------------------------------------
# 429 rate limit handling
# ---------------------------------------------------------------------------


def test_extract_retry_after_parses_azure_message() -> None:
    """_extract_retry_after extracts seconds from Azure 429 error messages."""
    assert _extract_retry_after("Rate limit reached. Retry after 30 seconds.") == 30
    assert _extract_retry_after("Please retry after 5 seconds") == 5
    assert _extract_retry_after("retry after 120 second") == 120
    assert _extract_retry_after("some other error") is None
    assert _extract_retry_after("") is None


@patch("agents.skills_extraction.extractors.skills.time")
@patch("agents.skills_extraction.extractors.skills.invoke_structured_extraction_llm")
def test_extract_skills_retries_on_429_with_backoff(
    mock_invoke,
    mock_time,
) -> None:
    """When LLM returns 429, extract_skills retries with exponential backoff."""
    rate_limit_meta = {
        "success": False,
        "extraction_failed": True,
        "is_rate_limit": True,
        "retry_after_seconds": 10,
        "error_reason": "429: Rate limit reached",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "latency_ms": 50,
        "provider": "azure-openai",
        "model": "test",
    }
    success_root = _make_skills_root(
        {
            "skill_name": "Python",
            "type": "Technical",
            "confidence": 0.9,
            "source_span": {"text": "Python", "field_source": "description", "start_char": 0, "end_char": 6},
        },
    )
    success_meta = {
        "success": True,
        "extraction_failed": False,
        "tokens_used": 100,
        "cost_usd": 0.01,
        "latency_ms": 500,
        "provider": "azure-openai",
        "model": "test",
    }
    mock_invoke.side_effect = [
        (None, rate_limit_meta),
        (success_root, success_meta),
    ]
    job = _job_record()
    skills, meta = extract_skills(job, pass1_tools=[])
    assert len(skills) == 1
    assert skills[0].skill_name == "Python"
    assert mock_time.sleep.called
    assert meta["tokens_used"] == 100
    assert meta["cost_usd"] == 0.01
    assert meta["latency_ms"] == 550
