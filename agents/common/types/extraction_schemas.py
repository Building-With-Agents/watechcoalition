"""Week 5 extraction schemas for Tasks, Responsibilities, and Context (Pair B).

Canonical Pydantic models for the three remaining Work Intelligence dimensions.
SpanRecord is shared with skills/tools and imported from extraction_types.

Source: ARCHITECTURE_DEEP.md, curriculum Week 5 Pair B spec.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from agents.common.types.extraction_types import SpanRecord

TaskCategory = Literal["core", "supporting", "management", "technical"]
SenioritySignal = Literal["entry", "mid", "senior", "lead", "any"]
ResponsibilityScope = Literal["individual", "team", "department", "organization"]
ContextSignalType = Literal[
    "remote_policy",
    "team_size",
    "reporting_structure",
    "work_methodology",
    "ai_adoption_signal",
]


class TaskRecord(BaseModel):
    """One discrete task or duty extracted from job text (Pass 2, Haiku-class LLM)."""

    task_description: str = Field(
        ...,
        description="Short, actionable task phrase from the posting.",
    )
    task_category: TaskCategory = Field(
        ...,
        description="Whether the task is core, supporting, management, or technical.",
    )
    seniority_signal: SenioritySignal = Field(
        ...,
        description="Implied seniority level for performing this task.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_span: SpanRecord = Field(
        ...,
        description="Evidence span in title, description, requirements, or responsibilities.",
    )


class ResponsibilityRecord(BaseModel):
    """One area of ownership extracted from job text (Pass 2, Sonnet-class LLM)."""

    responsibility_description: str = Field(
        ...,
        description="High-level responsibility statement.",
    )
    scope: ResponsibilityScope = Field(
        ...,
        description="individual | team | department | organization.",
    )
    requires_ai_competency: bool = Field(
        ...,
        description="True when the responsibility clearly involves AI/ML work.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_span: SpanRecord = Field(
        ...,
        description="Evidence span in the job text.",
    )


class ContextSignal(BaseModel):
    """Structured context from Pass 1 pattern matching only (zero LLM tokens)."""

    signal_type: ContextSignalType
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source_span: SpanRecord
