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

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

FieldSource = Literal["title", "description", "requirements", "responsibilities"]
SkillType = Literal["Technical", "Domain", "Soft", "Certification", "Tool"]
ToolCategory = Literal["language", "framework", "platform", "database", "devops", "ai_tool", "other"]


class SpanRecord(BaseModel):
    """Source evidence span linking an extraction back to the original text."""

    model_config = ConfigDict(populate_by_name=True)

    text: str
    field_source: FieldSource
    start_char: int = Field(ge=0, validation_alias=AliasChoices("start_char", "char_start"))
    end_char: int = Field(ge=0, validation_alias=AliasChoices("end_char", "char_end"))

    @model_validator(mode="after")
    def validate_offsets(self) -> SpanRecord:
        """Ensure offsets are ordered and consistent with the captured text."""
        if self.end_char < self.start_char:
            raise ValueError("end_char must be greater than or equal to start_char")

        if (self.end_char - self.start_char) != len(self.text):
            raise ValueError("span offsets must match the captured text length")

        return self


class SkillRecord(BaseModel):
    """A single extracted skill with taxonomy linking metadata."""

    skill_id: str | None = None
    skill_name: str = Field(validation_alias=AliasChoices("skill_name", "label"))
    type: SkillType
    confidence: float = Field(ge=0.0, le=1.0)
    required_flag: bool | None = None
    esco_uri: str | None = None  # ESCO digital skills cluster URI
    is_genai_extension: bool = False  # True if from GenAI Extension Layer
    source_span: SpanRecord
    # Debug: set when source_span end_char was auto-corrected to match len(text)
    span_auto_corrected: bool = False
    original_end_char: int | None = None  # end_char before correction (when span_auto_corrected)


class ToolRecord(BaseModel):
    """A single extracted tool (programming language, framework, platform, etc.)."""

    model_config = ConfigDict(populate_by_name=True)

    tool_id: str | None = None
    tool_name: str = Field(validation_alias=AliasChoices("tool_name", "label"))
    category: ToolCategory
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord
    is_genai_tool: bool = False


class TaskRecord(BaseModel):
    """A single extracted job task or duty."""

    model_config = ConfigDict(populate_by_name=True)

    task_id: str | None = None
    task_description: str = Field(validation_alias=AliasChoices("task_description", "description"))
    category: str
    frequency: str
    complexity: str | None = None  # routine | analytical | creative | strategic
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord | None = None


class ResponsibilityRecord(BaseModel):
    """A single extracted responsibility with scope classification."""

    model_config = ConfigDict(populate_by_name=True)

    responsibility_id: str | None = None
    responsibility_description: str = Field(validation_alias=AliasChoices("responsibility_description", "description"))
    scope: str | None = None  # individual | team | department | organization
    level: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord | None = None


class ContextSignal(BaseModel):
    """A contextual signal extracted from the job posting."""

    signal_type: str  # remote_policy | team_size | reporting_structure | growth_stage | ai_usage
    value: str
    confidence: float = Field(ge=0.0, le=1.0)
    source_span: SpanRecord | None = None  # optional in stubs; required when real extraction populates it


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

    model_config = ConfigDict(populate_by_name=True)

    extraction_version: str = "0.1.0"
    model_used: str = Field(
        default="",
        validation_alias=AliasChoices("model_used", "extraction_model"),
    )
    model_tier: str = ""
    tokens_used: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("tokens_used", "extraction_tokens_used"),
    )
    cost_usd: float = Field(
        default=0.0,
        ge=0.0,
        validation_alias=AliasChoices("cost_usd", "extraction_cost_usd"),
    )
    extraction_duration_ms: int = Field(default=0, ge=0)
    pass1_tool_count: int = Field(
        default=0,
        ge=0,
        validation_alias=AliasChoices("pass1_tool_count", "pass1_pattern_matches"),
    )
    pass2_llm_dimensions: list[str] = Field(default_factory=list)
    pass2_llm_calls: int = Field(default=0, ge=0)
    extraction_warnings: list[str] = Field(default_factory=list)
