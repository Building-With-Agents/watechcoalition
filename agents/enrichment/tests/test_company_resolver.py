"""Tests for company name normalization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.enrichment.resolvers.company_resolver import (
    create_placeholder_company,
    find_best_fuzzy_match,
    lookup_company_exact,
    normalize_company_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Microsoft Corporation", "microsoft"),
        ("Microsoft Corp.", "microsoft"),
        ("Microsoft Corp", "microsoft"),
        ("MSFT", "msft"),
        ("  Apple Inc.  ", "apple"),
        ("spacex", "spacex"),
        ("Ernst & Young LLP", "ernst & young"),
    ],
)
def test_normalize_company_name(raw: str, expected: str) -> None:
    assert normalize_company_name(raw) == expected


def test_lookup_company_exact_returns_id_when_found() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = 42
    session.execute.return_value = exec_result

    assert lookup_company_exact("microsoft", session) == 42
    session.execute.assert_called_once()


def test_lookup_company_exact_returns_none_when_not_found() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.scalar_one_or_none.return_value = None
    session.execute.return_value = exec_result

    assert lookup_company_exact("unknown-corp", session) is None
    session.execute.assert_called_once()


@patch("agents.enrichment.resolvers.company_resolver.fuzz")
def test_find_best_fuzzy_match_returns_id_when_above_threshold(mock_fuzz: MagicMock) -> None:
    mock_fuzz.token_sort_ratio.return_value = 90
    mock_fuzz.partial_ratio.return_value = 90
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = [(1, "microsoft corporation")]
    session.execute.return_value = exec_result

    company_id, score = find_best_fuzzy_match("microsoft", session)
    assert company_id == 1
    assert score >= 85


@patch("agents.enrichment.resolvers.company_resolver.fuzz")
def test_find_best_fuzzy_match_returns_none_when_below_threshold(mock_fuzz: MagicMock) -> None:
    mock_fuzz.token_sort_ratio.return_value = 50
    mock_fuzz.partial_ratio.return_value = 50
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = [(1, "totally different llc")]
    session.execute.return_value = exec_result

    company_id, score = find_best_fuzzy_match("microsoft", session)
    assert company_id is None
    assert score == 50.0


def test_find_best_fuzzy_match_empty_candidates() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = []
    session.execute.return_value = exec_result

    company_id, score = find_best_fuzzy_match("anything", session)
    assert company_id is None
    assert score == 0.0


def test_create_placeholder_company_returns_id_and_adds_flushes() -> None:
    session = MagicMock()
    added: list = []

    def add_side_effect(obj: object) -> None:
        added.append(obj)

    def flush_side_effect() -> None:
        if added:
            added[0].id = 999

    session.add.side_effect = add_side_effect
    session.flush.side_effect = flush_side_effect

    cid = create_placeholder_company("Acme Corp.", "acme", session)
    assert cid == 999
    session.add.assert_called_once()
    session.flush.assert_called_once()
    assert added[0].normalized_name == "acme"
    assert added[0].raw_name == "Acme Corp."
    assert added[0].is_placeholder is True
