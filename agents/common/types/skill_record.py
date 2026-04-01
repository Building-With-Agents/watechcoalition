"""SkillRecord and ToolRecord — typed extraction output schemas.

Produced by the Skills Extraction Agent after LLM-based extraction.
Validated by validate_extraction_result() before writing to extracted_intelligence.
"""

from __future__ import annotations

from pydantic import BaseModel


class SkillRecord(BaseModel):
    """A single extracted skill from a job posting."""

    name: str
    skill_type: str = "raw"  # "raw" | "linked" | "genai_extension"
    confidence: float = 0.0
    source_span: str | None = None
    esco_uri: str | None = None
    is_genai_extension: bool = False


class ToolRecord(BaseModel):
    """A single extracted tool or technology from a job posting."""

    name: str
    confidence: float = 0.0
    source_span: str | None = None
