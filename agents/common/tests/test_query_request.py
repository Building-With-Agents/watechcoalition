"""Tests for forward-compatible query API types (Week 6)."""

from __future__ import annotations

from agents.common.types.query_request import QueryPersona, QueryRequest


def test_query_request_defaults() -> None:
    q = QueryRequest(query="What are top skills in El Paso?")
    assert q.persona is None
    assert q.intent_hint is None
    assert q.max_results == 10


def test_query_request_with_persona() -> None:
    q = QueryRequest(
        query="Gap analysis for cohort A",
        persona=QueryPersona.CFA_INTERNAL,
        intent_hint="gap_analysis",
        max_results=25,
    )
    assert q.persona == QueryPersona.CFA_INTERNAL
    assert q.max_results == 25
