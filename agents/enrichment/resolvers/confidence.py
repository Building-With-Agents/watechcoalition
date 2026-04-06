"""Field-level and overall confidence scoring for enrichment."""

from __future__ import annotations


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_field_confidence(
    company_confidence: float,
    location_confidence: float,
    sector_id: int | None,
    seniority_confidence: float | None,
) -> dict[str, float]:
    """Build per-field confidence map; all values in ``[0.0, 1.0]``."""
    seniority = 0.0 if seniority_confidence is None else _clamp01(seniority_confidence)
    return {
        "company_id": _clamp01(company_confidence),
        "location_id": _clamp01(location_confidence),
        "sector_id": 0.80 if sector_id is not None else 0.0,
        "seniority": seniority,
    }


def compute_overall_confidence(
    field_confidence: dict,
    extraction_confidence: float | None,
    quality_score: float | None,
    taxonomy_coverage: float | None,
) -> float:
    """
    Weighted blend for overall record confidence; result in ``[0.0, 1.0]``, 4 decimal places.
    """
    ext = 0.0 if extraction_confidence is None else extraction_confidence
    qual = 0.0 if quality_score is None else quality_score
    tax = 0.0 if taxonomy_coverage is None else taxonomy_coverage

    values = list(field_confidence.values())
    field_avg = sum(values) / len(values) if values else 0.0

    total = ext * 0.40 + qual * 0.30 + field_avg * 0.20 + tax * 0.10
    total = _clamp01(total)
    return round(total, 4)
