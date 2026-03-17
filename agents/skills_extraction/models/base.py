from __future__ import annotations

"""
Base schema types for skills extraction (spans and provenance).

SpanRecord links extracted signals back to source text for audit and debugging.
"""

from pydantic import BaseModel


class SpanRecord(BaseModel):
    """
    Source text span for provenance tracking.

    Links an extracted signal (skill, context, etc.) to the exact substring
    it was derived from. field_source indicates which job field the span
    belongs to (title, description, requirements, responsibilities).
    """

    text: str
    field_source: str  # title | description | requirements | responsibilities
    start_char: int
    end_char: int
