"""Unit tests for ingest_description_sample (no API / DB)."""

from __future__ import annotations

from unittest.mock import MagicMock

from agents.scripts.ingest_description_sample import (
    DescriptionCoverage,
    build_region_config,
    query_description_coverage,
)


def test_description_coverage_pct_zero_when_empty() -> None:
    c = DescriptionCoverage(0, 0, 0, 0)
    assert c.pct_with_description == 0.0


def test_description_coverage_pct() -> None:
    c = DescriptionCoverage(10, 4, 3, 7)
    assert c.pct_with_description == 40.0


def test_build_region_config_jsearch() -> None:
    d = build_region_config(
        region_id="r1",
        query_location="TX",
        keywords=["python"],
    )
    assert d["sources"] == ["jsearch"]
    assert d["region_id"] == "r1"
    assert d["keywords"] == ["python"]
    assert d["radius_miles"] == 9999


def test_query_description_coverage() -> None:
    r1 = MagicMock(description="hello", processing_status="pending")
    r2 = MagicMock(description="", processing_status="awaiting_description")
    r3 = MagicMock(description=None, processing_status="awaiting_description")
    r4 = MagicMock(description="  \n\t ", processing_status="awaiting_description")

    session = MagicMock()
    session.query.return_value.filter.return_value.all.return_value = [r1, r2, r3, r4]

    cov = query_description_coverage(session, "batch-uuid")
    assert cov.total_staged == 4
    assert cov.with_non_empty_description == 1
    assert cov.pending == 1
    assert cov.awaiting_description == 3
