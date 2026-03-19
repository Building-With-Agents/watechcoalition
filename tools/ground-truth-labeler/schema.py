"""Pydantic models for ground truth labeling.

Mirrors the extraction_types.py from week-04/skills-tools-extraction branch
(PR #64 schema — required source_span, start_char/end_char, validators).

These models are used by the labeling app to validate records before export.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# --- Literal types (match extraction_types.py) ---

FieldSource = Literal["title", "description", "requirements", "responsibilities"]
SkillType = Literal["Technical", "Domain", "Soft", "Certification", "Tool"]
ToolCategory = Literal[
    "language", "framework", "platform", "database", "devops", "ai_tool", "other"
]

# --- 10 GenAI Extension Skills (for labeler reference) ---

GENAI_SKILLS = [
    "Prompt Engineering",
    "RAG (Retrieval-Augmented Generation)",
    "Fine-Tuning",
    "AI Governance",
    "LLM Evaluation",
    "Agentic Workflows",
    "Vector Database Management",
    "AI Safety & Alignment",
    "Multimodal AI",
    "AI-Assisted Code Generation",
]


class SpanRecord(BaseModel):
    """Source evidence span linking an extraction back to the original text."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    field_source: FieldSource
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_offsets(self) -> SpanRecord:
        if self.end_char < self.start_char:
            raise ValueError("end_char must be >= start_char")
        if (self.end_char - self.start_char) != len(self.text):
            raise ValueError("span offsets must match the captured text length")
        return self


class SkillRecord(BaseModel):
    """A single extracted skill with taxonomy linking metadata."""

    skill_id: str | None = None
    skill_name: str
    type: SkillType
    confidence: float = Field(ge=0.0, le=1.0)
    required_flag: bool | None = None
    esco_uri: str | None = None
    is_genai_extension: bool = False
    source_span: SpanRecord
    span_auto_corrected: bool = False
    original_end_char: int | None = None


class ToolRecord(BaseModel):
    """A single extracted tool."""

    model_config = ConfigDict(populate_by_name=True)

    tool_id: str | None = None
    tool_name: str
    category: ToolCategory
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord
    is_genai_tool: bool = False


class GroundTruthRecord(BaseModel):
    """A fully labeled ground truth record for one job posting."""

    ground_truth_id: str
    external_id: str = ""
    source: str = "JSearch"
    title: str
    company: str
    city: str | None = None
    state: str | None = None
    description: str = ""
    requirements: str = ""
    responsibilities: str = ""
    skills: list[SkillRecord] = Field(default_factory=list)
    tools: list[ToolRecord] = Field(default_factory=list)
    labeler_notes: dict[str, str] = Field(default_factory=dict)
