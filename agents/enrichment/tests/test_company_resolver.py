"""Tests for company name normalization."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.enrichment.resolvers.company_resolver import (
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
