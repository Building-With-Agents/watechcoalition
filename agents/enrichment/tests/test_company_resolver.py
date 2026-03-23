"""Tests for company name normalization."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.enrichment.resolvers.company_resolver import (
    create_placeholder_company,
    find_best_fuzzy_match,
    lookup_company_exact,
    normalize_company_name,
    resolve_company,
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


@patch("agents.enrichment.resolvers.company_resolver.find_best_fuzzy_match")
@patch("agents.enrichment.resolvers.company_resolver.lookup_company_exact")
def test_resolve_company_exact_match_returns_high_confidence(
    mock_lookup: MagicMock, mock_fuzzy: MagicMock
) -> None:
    mock_lookup.return_value = 77
    session = MagicMock()

    cid, conf = resolve_company("Contoso Corporation", session)

    assert (cid, conf) == (77, 0.95)
    mock_lookup.assert_called_once_with("contoso", session)
    mock_fuzzy.assert_not_called()


@patch("agents.enrichment.resolvers.company_resolver.create_placeholder_company")
@patch("agents.enrichment.resolvers.company_resolver.find_best_fuzzy_match")
@patch("agents.enrichment.resolvers.company_resolver.lookup_company_exact")
def test_resolve_company_fuzzy_match_returns_score_over_100(
    mock_lookup: MagicMock,
    mock_fuzzy: MagicMock,
    mock_placeholder: MagicMock,
) -> None:
    mock_lookup.return_value = None
    mock_fuzzy.return_value = (3, 88.0)
    session = MagicMock()

    cid, conf = resolve_company("Microsft Corp", session)

    assert cid == 3
    assert conf == 0.88
    assert conf >= 0.85
    mock_placeholder.assert_not_called()


@patch("agents.enrichment.resolvers.company_resolver.create_placeholder_company")
@patch("agents.enrichment.resolvers.company_resolver.find_best_fuzzy_match")
@patch("agents.enrichment.resolvers.company_resolver.lookup_company_exact")
def test_resolve_company_unknown_creates_placeholder(
    mock_lookup: MagicMock,
    mock_fuzzy: MagicMock,
    mock_placeholder: MagicMock,
) -> None:
    mock_lookup.return_value = None
    mock_fuzzy.return_value = (None, 40.0)
    mock_placeholder.return_value = 999
    session = MagicMock()

    cid, conf = resolve_company("Totally New Startup LLC", session)

    assert (cid, conf) == (999, 0.40)
    mock_placeholder.assert_called_once_with(
        "Totally New Startup LLC", "totally new startup", session
    )


@patch("agents.enrichment.resolvers.company_resolver.create_placeholder_company")
@patch("agents.enrichment.resolvers.company_resolver.find_best_fuzzy_match")
@patch("agents.enrichment.resolvers.company_resolver.lookup_company_exact")
def test_resolve_company_twice_unknown_placeholder_once_then_exact(
    mock_lookup: MagicMock,
    mock_fuzzy: MagicMock,
    mock_placeholder: MagicMock,
) -> None:
    """Second call hits exact match against the first placeholder's normalized name."""
    mock_lookup.side_effect = [None, 500]
    mock_fuzzy.return_value = (None, 0.0)
    mock_placeholder.return_value = 500
    session = MagicMock()

    r1 = resolve_company("Zeta Unknown LLC", session)
    r2 = resolve_company("Zeta Unknown LLC", session)

    assert r1 == (500, 0.40)
    assert r2 == (500, 0.95)
    mock_placeholder.assert_called_once_with("Zeta Unknown LLC", "zeta unknown", session)
