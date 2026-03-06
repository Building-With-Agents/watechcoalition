"""Event payload builders for the Normalization Agent."""

from __future__ import annotations


def normalization_complete_payload(
    *,
    batch_id: str,
    region_id: str,
    normalized_count: int,
    quarantined_count: int,
    normalization_status: str,
) -> dict:
    """Build a ``NormalizationComplete`` event payload."""
    return {
        "event_type": "NormalizationComplete",
        "batch_id": batch_id,
        "region_id": region_id,
        "normalized_count": normalized_count,
        "quarantined_count": quarantined_count,
        "normalization_status": normalization_status,
    }


def normalization_failed_payload(
    *,
    batch_id: str,
    error: str,
) -> dict:
    """Build a ``NormalizationFailed`` event payload."""
    return {
        "event_type": "NormalizationFailed",
        "batch_id": batch_id,
        "error": error,
    }
