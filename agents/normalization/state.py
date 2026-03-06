"""LangGraph state definition for the Normalization Agent."""

from __future__ import annotations

from typing import TypedDict


class NormalizationState(TypedDict, total=False):
    """Typed state dict for the Normalization Agent LangGraph graph."""

    ingestion_run_id: str
    correlation_id: str
    batch_id: str
    region_id: str
    run_id: str
    normalised_count: int
    quarantined_count: int
    error_count: int
    status: str
    errors: list[str]
    normalization_complete_event: dict
