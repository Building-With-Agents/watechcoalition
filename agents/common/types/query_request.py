"""Forward-compatible query API types for Phase 2 Query Agent routing.

Phase 1 analytics / Q&A must ignore ``QueryRequest.persona`` if present on requests.
Phase 2 uses ``persona`` to select synthesis templates and access controls.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class QueryPersona(StrEnum):
    """Stakeholder role hint for response routing (Phase 2)."""

    WORKFORCE_BOARD = "workforce_board_director"
    EMPLOYER = "employer_partner"
    CFA_INTERNAL = "cfa_internal"
    STUDENT = "cohort_student"


class QueryRequest(BaseModel):
    """Natural-language workforce intelligence query (Phase 1 / Phase 2 boundary)."""

    query: str = Field(..., min_length=1, description="User question or search text.")
    persona: QueryPersona | None = Field(
        default=None,
        description="Optional; Phase 1 ignores. Phase 2 routes by persona.",
    )
    intent_hint: str | None = Field(
        default=None,
        description="Optional coarse intent label from UI or orchestrator.",
    )
    max_results: int = Field(default=10, ge=1, le=500)
