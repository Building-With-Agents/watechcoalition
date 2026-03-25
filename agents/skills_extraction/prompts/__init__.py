"""Versioned prompts for skills extraction. See SKILLS_PROMPT_VERSION for Exercise 4.5."""

from agents.skills_extraction.prompts.skills_extraction_v3 import (
    SKILLS_PROMPT_VERSION,
    SKILLS_SYSTEM_PROMPT,
    SKILLS_USER_TEMPLATE,
    build_skills_prompt,
)

__all__ = [
    "SKILLS_PROMPT_VERSION",
    "SKILLS_SYSTEM_PROMPT",
    "SKILLS_USER_TEMPLATE",
    "build_skills_prompt",
]
