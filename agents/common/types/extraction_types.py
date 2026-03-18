"""Pydantic schemas for the Work Intelligence Agent extraction pipeline.

These types define the structured output of the 6-dimension extraction model:
Skills, Tools, Tasks, Responsibilities, Context — plus shared SpanRecord
and ExtractionMetadata.

Source of truth: ARCHITECTURE_DEEP.md § Work Intelligence Agent.

Week 2: schemas defined, used by fixture data.
Week 4: used by real extraction stubs (skills, tools, taxonomy).
Week 5: used by remaining extractors (tasks, responsibilities, context).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpanRecord(BaseModel):
    """Source evidence span linking an extraction back to the original text."""

    text: str
    field_source: str  # title | description | requirements | responsibilities
    char_start: int
    char_end: int


class SkillRecord(BaseModel):
    """A single extracted skill with taxonomy linking metadata."""

    skill_id: str | None = None
    label: str
    type: str  # Technical | Domain | Soft | Certification | Tool
    confidence: float = Field(ge=0.0, le=1.0)
    field_source: str  # title | description | requirements | responsibilities
    required_flag: bool | None = None
    esco_uri: str | None = None  # ESCO digital skills cluster URI
    is_genai_extension: bool = False  # True if from GenAI Extension Layer
    source_span: SpanRecord | None = None


class ToolRecord(BaseModel):
    """A single extracted tool (programming language, framework, platform, etc.)."""

    tool_id: str | None = None
    tool_name: str
    category: str  # language | framework | platform | database | devops | ai_tool | other
    confidence: float = Field(ge=0.0, le=1.0)
    field_source: str
    source_span: SpanRecord | None = None


class TaskRecord(BaseModel):
    """A single extracted job task or duty."""

    task_id: str | None = None
    description: str
    complexity: str | None = None  # routine | analytical | creative | strategic
    confidence: float = Field(ge=0.0, le=1.0)
    field_source: str
    source_span: SpanRecord | None = None


class ResponsibilityRecord(BaseModel):
    """A single extracted responsibility with scope classification."""

    responsibility_id: str | None = None
    description: str
    scope: str | None = None  # individual | team | department | organization
    confidence: float = Field(ge=0.0, le=1.0)
    field_source: str
    source_span: SpanRecord | None = None


class ContextSignal(BaseModel):
    """A contextual signal extracted from the job posting."""

    signal_type: str  # remote_policy | team_size | reporting_structure | growth_stage | ai_usage
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord  # required — links extraction back to source text


class TaxonomyResult(BaseModel):
    """Result of resolving a skill label against the taxonomy store."""

    original_label: str
    esco_uri: str | None = None
    esco_label: str | None = None
    is_genai_extension: bool = False
    resolution_step: int = 6  # 1-6, which step resolved this skill
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ExtractionMetadata(BaseModel):
    """Metadata for a single extraction run over one job record."""

    extraction_version: str = "0.1.0"
    extraction_model: str = ""  # e.g. "claude-sonnet-4-5", "claude-haiku-4-5"
    extraction_tokens_used: int = 0
    extraction_cost_usd: float = 0.0
    pass1_pattern_matches: int = 0  # Hybrid Pass 1: pattern matching hits
    pass2_llm_calls: int = 0  # Hybrid Pass 2: LLM inference calls
    extraction_warnings: list[str] = Field(default_factory=list)
