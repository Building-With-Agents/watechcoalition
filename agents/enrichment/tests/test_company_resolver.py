"""Tests for company name normalization."""

from __future__ import annotations

import pytest

from agents.enrichment.resolvers.company_resolver import normalize_company_name


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
