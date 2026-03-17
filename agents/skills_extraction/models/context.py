from __future__ import annotations

"""
ContextSignal schema for Pass 1 context extraction (Week 4 stub, Week 5 implementation).

Context signals capture structured context from job text (e.g. remote policy,
team size, reporting structure) without consuming LLM tokens.
"""

from typing import Optional

from pydantic import BaseModel

from agents.skills_extraction.models.base import SpanRecord


class ContextSignal(BaseModel):
    """
    A single context signal extracted from job text.

    signal_type is one of: remote_policy | team_size | reporting_structure |
    growth_stage | ai_usage. value is the extracted string; confidence in [0, 1].
    source_span links back to the source text when available (Pass 1 pattern match).
    """

    signal_type: str  # remote_policy | team_size | reporting_structure | growth_stage | ai_usage
    value: str
    confidence: float
    source_span: Optional[SpanRecord] = None
