"""Tests for the active versioned skills extraction prompt."""

from __future__ import annotations

from agents.skills_extraction.prompts import SKILLS_PROMPT_VERSION, build_skills_prompt


def test_active_skills_prompt_version_is_v3() -> None:
    assert SKILLS_PROMPT_VERSION == "v3"


def test_skills_prompt_contains_soft_skill_suppression_guidance() -> None:
    prompt = build_skills_prompt(
        title="Product Manager",
        description="Excellent communication skills required.",
        requirements="Stakeholder communication for cross-functional alignment.",
        responsibilities="Lead sprint planning, retrospectives, and daily standups. Build REST APIs with Java and Spring Boot.",
        already_extracted_tool_names=["SQL"],
    )

    assert "Excellent communication skills" in prompt
    assert 'SKIP generic "Communication"' in prompt
    assert "Stakeholder communication for cross-functional alignment" in prompt
    assert 'do NOT invent "Scrum Facilitation"' in prompt
    assert 'do NOT suppress these because they are hard skills' in prompt
    assert "top 5 to 15 most important skills" in prompt
    assert "Do NOT extract standard job duties" in prompt
