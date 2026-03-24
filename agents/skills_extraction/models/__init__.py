from __future__ import annotations

"""
Skills extraction Pydantic models (schemas) for skills, context, and spans.

ContextSignal and SpanRecord are used by the context extractor (extract_context);
other models (SkillRecord, ToolRecord, etc.) are used by downstream extractors.
Schema definitions follow ARCHITECTURE_DEEP.md § Work Intelligence Extraction.
"""

from agents.common.types.extraction_types import ContextSignal
from agents.skills_extraction.models.base import SpanRecord

__all__ = ["SpanRecord", "ContextSignal"]
