from __future__ import annotations

"""
ContextSignal schema for Pass 1 context extraction (Week 4 stub, Week 5 implementation).
Context signals capture structured context from job text (e.g. remote policy,
team size, reporting structure) without consuming LLM tokens. Schema and
signal types defined in ARCHITECTURE_DEEP.md § Work Intelligence Extraction Schemas.
"""
from pydantic import BaseModel

from agents.skills_extraction.models.base import SpanRecord


class ContextSignal(BaseModel):
    """
    A single context signal extracted from job text (dimension 5 of 6).
    Used by extract_context() to return pattern-matched or LLM-derived context.
    Pass 1 (Week 5) uses pattern matching only; no LLM, no tokens consumed.

    Attributes
    ----------
    signal_type : str
        One of: remote_policy, team_size, reporting_structure, growth_stage, ai_usage.
    value : str
        The extracted value (e.g. "hybrid", "5-10", "direct").
    confidence : float
        Confidence in [0, 1] that this signal is correct.
    source_span : SpanRecord | None
        Links back to the source text when available (Pass 1 pattern match).
    """
    signal_type: str
    value: str
    confidence: float
    source_span: SpanRecord | None = None
