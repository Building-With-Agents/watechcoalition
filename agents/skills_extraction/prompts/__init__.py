"""Versioned prompts for skills extraction. See SKILLS_PROMPT_VERSION for Exercise 4.5."""

from agents.skills_extraction.prompts.skills_extraction_v1 import (
    SKILLS_PROMPT_VERSION,
    build_skills_prompt,
)

__all__ = ["SKILLS_PROMPT_VERSION", "build_skills_prompt"]
