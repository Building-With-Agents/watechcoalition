"""ExtractionMetadata — per-record cost and provenance tracking.

Attached to every extracted_intelligence row to capture model, tier,
token counts, cost, and which extraction pass produced which dimensions.

Schema mirrors ARCHITECTURE_DEEP.md ExtractionMetadata definition.
"""

from __future__ import annotations

from pydantic import BaseModel


class ExtractionMetadata(BaseModel):
    """Metadata for a single LLM extraction run over one job posting."""

    extraction_version: str
    model_used: str                    # e.g. "claude-sonnet-4-5"
    model_tier: str                    # "sonnet" | "haiku"
    tokens_used: int
    cost_usd: float
    extraction_duration_ms: int
    pass1_tool_count: int              # pattern-matching hits (free, no LLM)
    pass2_llm_dimensions: list[str]    # dimensions processed by LLM
    extraction_warnings: list[str] = []
