"""Shared pipeline state for EXP-007 two-agent (Ingestion → Normalization) runners.

Used by both the LangGraph and pure Python implementations so we can
compare topology expressiveness and behavior on the same state shape.
"""

from __future__ import annotations

from typing import TypedDict


class TwoAgentPipelineState(TypedDict, total=False):
    """State passed through the two-agent pipeline (Ingestion → Normalization).

    current_event: EventEnvelope as dict (for LangGraph serialization and inspection).
    correlation_id: Set at pipeline entry, propagated unchanged.
    status: "ok" | "failed".
    errors: List of error messages if any step failed.
    """

    current_event: dict
    correlation_id: str
    status: str
    errors: list[str]
