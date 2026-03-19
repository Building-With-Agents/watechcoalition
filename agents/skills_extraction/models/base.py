from __future__ import annotations

"""
Base schema types for skills extraction (spans and provenance).

SpanRecord links extracted signals back to source text for audit and debugging.
Defined per ARCHITECTURE_DEEP.md § Work Intelligence Extraction Schemas.
"""

from pydantic import BaseModel


class SpanRecord(BaseModel):
    """
    Source text span for provenance tracking.

    Links an extracted signal (skill, context, etc.) to the exact substring
    it was derived from. Used by ContextSignal and other extraction records
    to reference the source job field and character range.

    Attributes
    ----------
    text : str
        The substring of source text this span refers to.
    field_source : str
        Which job field the span comes from: one of title, description,
        requirements, responsibilities.
    start_char : int
        Start character offset (0-based) in the field text.
    end_char : int
        End character offset (exclusive) in the field text.
    """

    text: str
    field_source: str  # title | description | requirements | responsibilities
    start_char: int
    end_char: int
