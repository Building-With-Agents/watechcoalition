"""Tests for enrichment confidence helpers."""

from __future__ import annotations

from agents.enrichment.resolvers.confidence import (
    compute_field_confidence,
    compute_overall_confidence,
)


def test_compute_field_confidence_clamps_and_all_keys_present() -> None:
    out = compute_field_confidence(
        company_confidence=-0.5,
        location_confidence=1.5,
        sector_id=42,
        seniority_confidence=0.75,
    )
    assert set(out.keys()) == {"company_id", "location_id", "sector_id", "seniority"}
    assert out["company_id"] == 0.0
    assert out["location_id"] == 1.0
    assert out["sector_id"] == 0.80
    assert out["seniority"] == 0.75


def test_compute_field_confidence_sector_none() -> None:
    out = compute_field_confidence(0.5, 0.5, None, 0.5)
    assert out["sector_id"] == 0.0


def test_compute_field_confidence_seniority_none() -> None:
    out = compute_field_confidence(0.5, 0.5, 1, None)
    assert out["seniority"] == 0.0


def test_compute_overall_confidence_weighted_average() -> None:
    field = {
        "company_id": 0.25,
        "location_id": 0.25,
        "sector_id": 0.25,
        "seniority": 0.25,
    }
    # mean field = 0.25
    # 0.25*0.4 + 0.25*0.3 + 0.25*0.2 + 0.25*0.1 = 0.25
    assert compute_overall_confidence(field, 0.25, 0.25, 0.25) == 0.2500


def test_compute_overall_confidence_all_none() -> None:
    field = {"company_id": 0.0, "location_id": 0.0, "sector_id": 0.0, "seniority": 0.0}
    assert compute_overall_confidence(field, None, None, None) == 0.0


def test_compute_overall_confidence_clamped_to_one() -> None:
    field = {"a": 10.0, "b": 10.0}
    # mean = 10; contribution 2.0 from field term alone
    assert compute_overall_confidence(field, 1.0, 1.0, 1.0) == 1.0
