"""Tests for company name normalization."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from agents.enrichment.resolvers.company_resolver import (
    create_placeholder_company,
    find_best_fuzzy_match,
    lookup_company_exact,
    normalize_company_name,
    resolve_company,
)

# Stable UUID strings for mocked resolver returns (TEXT company_id / company_id PK).
_UUID_EXACT = "11111111-1111-1111-1111-111111111177"
_UUID_FUZZY = "33333333-3333-3333-3333-333333333333"
_UUID_PLACEHOLDER = "99999999-9999-9999-9999-999999999999"
_UUID_ZETA = "55555555-5555-5555-5555-555555555500"
_UUID_LOOKUP = "00000000-0000-0000-0000-000000000042"
_UUID_ROW = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeee0001"


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
    exec_result.all.return_value = [(_UUID_LOOKUP, "Microsoft Corporation")]
    session.execute.return_value = exec_result

    assert lookup_company_exact("microsoft", session) == _UUID_LOOKUP
    session.execute.assert_called_once()


def test_lookup_company_exact_returns_none_when_not_found() -> None:
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = [(_UUID_ROW, "Totally Different LLC")]
    session.execute.return_value = exec_result

    assert lookup_company_exact("unknown-corp", session) is None
    session.execute.assert_called_once()


@patch("agents.enrichment.resolvers.company_resolver.fuzz")
def test_find_best_fuzzy_match_returns_id_when_above_threshold(mock_fuzz: MagicMock) -> None:
    mock_fuzz.token_sort_ratio.return_value = 90
    mock_fuzz.partial_ratio.return_value = 90
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = [(_UUID_ROW, "microsoft corporation")]
    session.execute.return_value = exec_result

    company_id, score = find_best_fuzzy_match("microsoft", session)
    assert company_id == _UUID_ROW
    assert score >= 85


@patch("agents.enrichment.resolvers.company_resolver.fuzz")
def test_find_best_fuzzy_match_returns_none_when_below_threshold(mock_fuzz: MagicMock) -> None:
    mock_fuzz.token_sort_ratio.return_value = 50
    mock_fuzz.partial_ratio.return_value = 50
    session = MagicMock()
    exec_result = MagicMock()
    exec_result.all.return_value = [(_UUID_ROW, "totally different llc")]
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

    session.add.side_effect = add_side_effect

    cid = create_placeholder_company("Acme Corp.", "acme", session)
    uuid.UUID(cid)
    assert cid == added[0].company_id
    assert isinstance(cid, str)
    session.add.assert_called_once()
    session.flush.assert_called_once()
    assert added[0].company_name == "Acme Corp."


@patch("agents.enrichment.resolvers.company_resolver.find_best_fuzzy_match")
@patch("agents.enrichment.resolvers.company_resolver.lookup_company_exact")
def test_resolve_company_exact_match_returns_high_confidence(
    mock_lookup: MagicMock, mock_fuzzy: MagicMock
) -> None:
    mock_lookup.return_value = _UUID_EXACT
    session = MagicMock()

    cid, conf = resolve_company("Contoso Corporation", session)

    assert (cid, conf) == (_UUID_EXACT, 0.95)
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
    mock_fuzzy.return_value = (_UUID_FUZZY, 88.0)
    session = MagicMock()

    cid, conf = resolve_company("Microsft Corp", session)

    assert cid == _UUID_FUZZY
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
    mock_placeholder.return_value = _UUID_PLACEHOLDER
    session = MagicMock()

    cid, conf = resolve_company("Totally New Startup LLC", session)

    assert (cid, conf) == (_UUID_PLACEHOLDER, 0.40)
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
    mock_lookup.side_effect = [None, _UUID_ZETA]
    mock_fuzzy.return_value = (None, 0.0)
    mock_placeholder.return_value = _UUID_ZETA
    session = MagicMock()

    r1 = resolve_company("Zeta Unknown LLC", session)
    r2 = resolve_company("Zeta Unknown LLC", session)

    assert r1 == (_UUID_ZETA, 0.40)
    assert r2 == (_UUID_ZETA, 0.95)
    mock_placeholder.assert_called_once_with("Zeta Unknown LLC", "zeta unknown", session)
